# -*- coding: utf-8 -*-
"""Tests de non-régression pour la correction IMP-05 de l'audit.

Vérifie que get_connection() ferme toujours la connexion SQLite
(succès comme exception), qu'elle commit/rollback correctement,
et qu'aucune ResourceWarning « unclosed database » n'est émise.

Exécution : python -m unittest tests.test_connection_cleanup -v
"""

import os
import sqlite3
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from repositories.student_repository import StudentRepository
from services.payment_service import PaymentService
from services.student_service import StudentService


class ConnectionCleanupTestCase(unittest.TestCase):
    """Fermeture garantie des connexions SQLite (IMP-05)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_conn_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_database()

    def tearDown(self):
        # Pas de gc.collect() volontairement : si une connexion fuit,
        # le fichier .db reste verrouillé sous Windows et cleanup() échoue.
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    # ------------------------------------------------------------------
    # Fermeture de la connexion
    # ------------------------------------------------------------------

    def test_connection_closed_after_success(self):
        """Le fichier .db doit être immédiatement supprimable après le bloc with."""
        with db.get_connection() as conn:
            conn.execute("SELECT 1")
        # Aucun gc.collect() : la fermeture doit être immédiate
        os.remove(db.DB_PATH)  # lève PermissionError si la connexion fuit
        db.init_database()  # recrée pour les tests suivants

    def test_connection_closed_after_exception(self):
        """La connexion doit être fermée même si le bloc lève une exception."""
        with self.assertRaises(RuntimeError):
            with db.get_connection() as conn:
                conn.execute("SELECT 1")
                raise RuntimeError("erreur simulée")
        os.remove(db.DB_PATH)
        db.init_database()

    def test_connection_rolls_back_on_exception(self):
        """Une exception dans le bloc doit annuler les écritures (rollback)."""
        student_id = StudentRepository().create(
            "ROLL", "Back", "6ème A", "2025-2026", 100_000
        )

        def failing_operation():
            with db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO payments (student_id, montant, mode_paiement, numero_recu)
                    VALUES (?, ?, ?, ?)
                    """,
                    (student_id, 50_000.0, "especes", "REC-ROLLBACK-TEST"),
                )
                raise RuntimeError("interruption simulée")

        with self.assertRaises(RuntimeError):
            failing_operation()

        with db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        self.assertEqual(count, 0, "L'insertion aurait dû être annulée")

    def test_connection_commits_on_success(self):
        """Les écritures du bloc doivent être persistées."""
        student_id = StudentRepository().create(
            "COM", "Mit", "6ème A", "2025-2026", 100_000
        )
        with db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO payments (student_id, montant, mode_paiement, numero_recu)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, 30_000.0, "cheque", "REC-COMMIT-TEST"),
            )
        # Nouvelle connexion indépendante : la donnée doit être là
        with db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        self.assertEqual(count, 1)

    # ------------------------------------------------------------------
    # Aucune ResourceWarning (l'ancien symptôme d'IMP-05)
    # ------------------------------------------------------------------

    def test_no_resource_warning_on_typical_usage(self):
        """Un flux métier complet ne doit émettre aucune ResourceWarning."""
        student_service = StudentService()
        payment_service = PaymentService()

        with warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            student_id = student_service.create_student(
                "WARN", "Free", "6ème A", "2025-2026", 500_000
            )
            payment_service.create_payment(student_id, 100_000, "especes")
            student_service.get_all_students()
            student_service.get_student(student_id)
            payment_service.get_student_payments(student_id)
            payment_service.get_student_balance(student_id)

    def test_row_factory_preserved(self):
        """Le comportement sqlite3.Row doit être conservé (accès par nom)."""
        StudentRepository().create("ROW", "Factory", "6ème A", "2025-2026", 100_000)
        with db.get_connection() as conn:
            row = conn.execute("SELECT nom, prenom FROM students").fetchone()
        self.assertIsInstance(row, sqlite3.Row)
        self.assertEqual(row["nom"], "ROW")


if __name__ == "__main__":
    unittest.main(verbosity=2)
