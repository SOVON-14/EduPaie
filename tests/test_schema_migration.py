# -*- coding: utf-8 -*-
"""Tests de non-régression pour la migration de schéma v1 de l'audit.

IMP-04 : montants stockés en entiers (FCFA sans sous-unité).
DB-02  : CHECK(montant > 0) en base, pas seulement dans les services.
DB-03  : UNIQUE(nom, prenom, classe, annee_scolaire) contre les doublons.

Vérifie aussi la migration des bases à l'ancien schéma (v0 : montants REAL)
: conservation des données, arrondi, cascade, AUTOINCREMENT, idempotence.

Exécution : python -m unittest tests.test_schema_migration -v
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from repositories.payment_repository import PaymentRepository
from repositories.student_repository import StudentRepository
from services.payment_service import PaymentService
from services.student_service import StudentService

# Ancien schéma (v0) tel qu'avant les corrections de l'audit
ANCIEN_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    classe TEXT NOT NULL,
    annee_scolaire TEXT NOT NULL,
    montant_total REAL NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    montant REAL NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode_paiement TEXT NOT NULL CHECK(mode_paiement IN ('especes', 'cheque', 'virement', 'mobile_money')),
    numero_recu TEXT NOT NULL UNIQUE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_payments_student_id ON payments(student_id);
CREATE INDEX IF NOT EXISTS idx_students_classe ON students(classe);
"""


class MigrationSchemaTestCase(unittest.TestCase):
    """Migration v0 -> v1 et nouvelles contraintes SQL."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_migr_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    def _creer_base_ancien_schema(self):
        """Reconstruit une base v0 avec des montants flottants."""
        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.executescript(ANCIEN_SCHEMA)
            conn.execute(
                "INSERT INTO students (nom, prenom, classe, annee_scolaire, montant_total) "
                "VALUES (?, ?, ?, ?, ?)",
                ("DIOP", "Awa", "6ème A", "2025-2026", 500000.7),
            )
            conn.execute(
                "INSERT INTO payments (student_id, montant, mode_paiement, numero_recu) "
                "VALUES (?, ?, ?, ?)",
                (1, 100000.4, "especes", "REC-MIG-1"),
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # IMP-04 : montants en entiers
    # ------------------------------------------------------------------

    def test_base_neuve_en_version_1(self):
        db.init_database()
        with db.get_connection() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        self.assertEqual(version, 1)

    def test_migration_conserve_et_convertit_les_donnees(self):
        self._creer_base_ancien_schema()
        db.ensure_database_exists()  # déclenche la migration

        with db.get_connection() as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)

            row = conn.execute(
                "SELECT nom, montant_total, typeof(montant_total) FROM students"
            ).fetchone()
            self.assertEqual(row["nom"], "DIOP")
            self.assertEqual(row["montant_total"], 500001)  # arrondi de 500000.7
            self.assertEqual(row[2], "integer")

            pay = conn.execute(
                "SELECT montant, typeof(montant), student_id, numero_recu FROM payments"
            ).fetchone()
            self.assertEqual(pay["montant"], 100000)  # arrondi de 100000.4
            self.assertEqual(pay[1], "integer")
            self.assertEqual(pay["student_id"], 1)
            self.assertEqual(pay["numero_recu"], "REC-MIG-1")

    def test_migration_cascade_encore_active(self):
        self._creer_base_ancien_schema()
        db.ensure_database_exists()
        self.assertTrue(StudentRepository().delete(1))
        with db.get_connection() as conn:
            n = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        self.assertEqual(n, 0)

    def test_migration_autoincrement_continue(self):
        self._creer_base_ancien_schema()
        db.ensure_database_exists()
        sid = StudentRepository().create("NOUVEAU", "Eleve", "5ème A", "2025-2026", 100000)
        self.assertGreater(sid, 1, "AUTOINCREMENT doit continuer après migration")

    def test_migration_deja_en_v1_est_idempotente(self):
        db.init_database()
        StudentRepository().create("A", "B", "6ème A", "2025-2026", 100000)
        db.migrate_schema()  # ne doit rien casser
        students = StudentRepository().get_all()
        self.assertEqual(len(students), 1)
        with db.get_connection() as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_service_convertit_les_montants_en_entiers(self):
        db.init_database()
        ss = StudentService()
        ps = PaymentService()
        sid = ss.create_student("A", "B", "6ème A", "2025-2026", 150000.9)
        student = ss.get_student(sid)
        self.assertIsInstance(student["montant_total"], int)
        self.assertEqual(student["montant_total"], 150001)

        result = ps.create_payment(sid, 50000.9, "especes")
        self.assertIsInstance(result["payment"]["montant"], int)
        self.assertEqual(result["payment"]["montant"], 50001)
        self.assertEqual(result["solde_restant"], 100000)

    # ------------------------------------------------------------------
    # DB-02 : CHECK(montant > 0) en base
    # ------------------------------------------------------------------

    def test_check_montant_etudiant_positif(self):
        db.init_database()
        with self.assertRaises(sqlite3.IntegrityError):
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO students (nom, prenom, classe, annee_scolaire, montant_total) "
                    "VALUES ('X', 'Y', '6ème A', '2025-2026', 0)"
                )

    def test_check_montant_paiement_positif(self):
        db.init_database()
        StudentRepository().create("X", "Y", "6ème A", "2025-2026", 100000)
        with self.assertRaises(sqlite3.IntegrityError):
            with db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO payments (student_id, montant, mode_paiement, numero_recu) "
                    "VALUES (1, -5, 'especes', 'REC-NEGATIF')"
                )

    # ------------------------------------------------------------------
    # DB-03 : UNIQUE anti-doublons élèves
    # ------------------------------------------------------------------

    def test_unique_anti_doublons_eleves_en_base(self):
        db.init_database()
        StudentRepository().create("X", "Y", "6ème A", "2025-2026", 100000)
        with self.assertRaises(sqlite3.IntegrityError):
            StudentRepository().create("X", "Y", "6ème A", "2025-2026", 200000)
        # Même identité mais autre classe : légitime
        sid = StudentRepository().create("X", "Y", "6ème B", "2025-2026", 100000)
        self.assertGreater(sid, 1)

    def test_service_message_clair_sur_doublon(self):
        db.init_database()
        ss = StudentService()
        ss.create_student("A", "B", "6ème A", "2025-2026", 100000)
        with self.assertRaises(ValueError) as ctx:
            ss.create_student("A", "B", "6ème A", "2025-2026", 200000)
        self.assertIn("existe déjà", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
