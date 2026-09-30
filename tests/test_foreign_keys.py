# -*- coding: utf-8 -*-
"""Tests de non-régression pour la correction CRIT-01 de l'audit.

Vérifie que les clés étrangères SQLite sont appliquées (ON DELETE CASCADE)
et que la purge des paiements orphelins fonctionne.

Exécution : python -m unittest tests.test_foreign_keys -v
"""

import gc
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Import depuis la racine du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from repositories.payment_repository import PaymentRepository
from repositories.student_repository import StudentRepository
from services.payment_service import PaymentService
from services.student_service import StudentService


class ForeignKeyTestCase(unittest.TestCase):
    """Base de données temporaire recréée pour chaque test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_test_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_database()

        self.student_repo = StudentRepository()
        self.payment_repo = PaymentRepository()
        self.student_service = StudentService()
        self.payment_service = PaymentService()

    def tearDown(self):
        # Les connexions sqlite3 non fermées forment un cycle de références
        # (bug IMP-05 de l'audit : connexions jamais fermées). Sous Windows,
        # le fichier .db reste verrouillé tant que le GC n'a pas collecté
        # ces cycles ; un collect() explicite simule la fermeture propre.
        gc.collect()
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    def _create_student_with_payment(self, montant_paye=50_000.0):
        """Crée un élève et un paiement, retourne (student_id, payment_id)."""
        student_id = self.student_service.create_student(
            "DIOP", "Awa", "6ème A", "2025-2026", 500_000
        )
        result = self.payment_service.create_payment(
            student_id, montant_paye, "especes"
        )
        return student_id, result["payment"]["id"]

    # ------------------------------------------------------------------
    # CRIT-01 : le pragma est actif
    # ------------------------------------------------------------------

    def test_pragma_foreign_keys_active(self):
        """get_connection() doit activer PRAGMA foreign_keys pour chaque connexion."""
        with db.get_connection() as conn:
            value = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(value, 1)

    # ------------------------------------------------------------------
    # CRIT-01 : le CASCADE fonctionne
    # ------------------------------------------------------------------

    def test_delete_student_cascades_payments(self):
        """Supprimer un élève doit supprimer ses paiements (ON DELETE CASCADE)."""
        student_id, _ = self._create_student_with_payment()

        deleted = self.student_repo.delete(student_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.student_repo.get_by_id(student_id))

        remaining = self.payment_repo.get_by_student(student_id)
        self.assertEqual(remaining, [])

    # ------------------------------------------------------------------
    # CRIT-01 : une insertion orpheline est refusée
    # ------------------------------------------------------------------

    def test_insert_orphan_payment_rejected(self):
        """Insérer un paiement pour un élève inexistant doit échouer."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.payment_repo.create(
                999_999, 100.0, "especes", "REC-ORPHELIN-TEST"
            )

    # ------------------------------------------------------------------
    # CRIT-01 : purge des orphelins hérités
    # ------------------------------------------------------------------

    def test_cleanup_orphan_payments_deletes_orphans(self):
        """cleanup_orphan_payments() supprime les paiements sans élève."""
        # Simuler un orphelin hérité d'avant la correction (bypass de la FK)
        conn = sqlite3.connect(db.DB_PATH)
        try:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute(
                """
                INSERT INTO payments (student_id, montant, mode_paiement, numero_recu)
                VALUES (?, ?, ?, ?)
                """,
                (999_999, 200_000.0, "especes", "REC-ORPHAN-LEGACY"),
            )
            conn.commit()
        finally:
            conn.close()

        with db.get_connection() as conn:
            before = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
            self.assertEqual(before, 1)

        deleted = db.cleanup_orphan_payments()
        self.assertEqual(deleted, 1)

        with db.get_connection() as conn:
            after = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        self.assertEqual(after, 0)

    def test_cleanup_orphan_payments_keeps_valid_payments(self):
        """cleanup_orphan_payments() ne touche pas aux paiements valides."""
        student_id, _ = self._create_student_with_payment()

        deleted = db.cleanup_orphan_payments()
        self.assertEqual(deleted, 0)

        payments = self.payment_repo.get_by_student(student_id)
        self.assertEqual(len(payments), 1)

    def test_cleanup_orphan_payments_empty_db(self):
        """cleanup_orphan_payments() retourne 0 sur une base vide."""
        self.assertEqual(db.cleanup_orphan_payments(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
