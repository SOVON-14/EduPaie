# -*- coding: utf-8 -*-
"""Tests de non-régression pour les corrections IMP-09 et IMP-10 de l'audit.

IMP-09 : update_student() doit valider les données comme create_student()
         (notamment le format de l'année scolaire).
IMP-10 : update_student() doit refuser un montant_total inférieur au
         montant déjà payé (solde négatif silencieux).

Exécution : python -m unittest tests.test_student_update_validation -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from services.payment_service import PaymentService
from services.student_service import StudentService


class StudentUpdateValidationTestCase(unittest.TestCase):
    """Validation des données à la modification d'un élève."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_upd_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_database()
        self.student_service = StudentService()
        self.payment_service = PaymentService()

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    def _create_student(self, montant_total=500_000.0):
        return self.student_service.create_student(
            "DIOP", "Awa", "6ème A", "2025-2026", montant_total
        )

    # ------------------------------------------------------------------
    # IMP-09 : validation de l'année scolaire à la modification
    # ------------------------------------------------------------------

    def test_update_refuse_annee_invalide(self):
        student_id = self._create_student()
        with self.assertRaises(ValueError) as ctx:
            self.student_service.update_student(
                student_id, "DIOP", "Awa", "6ème A", "2025", 500_000
            )
        self.assertIn("année scolaire", str(ctx.exception).lower())
        # Les données ne doivent pas avoir été modifiées
        student = self.student_service.get_student(student_id)
        self.assertEqual(student["annee_scolaire"], "2025-2026")

    def test_update_refuse_montant_nul_ou_negatif(self):
        student_id = self._create_student()
        with self.assertRaises(ValueError):
            self.student_service.update_student(
                student_id, "DIOP", "Awa", "6ème A", "2025-2026", 0
            )
        with self.assertRaises(ValueError):
            self.student_service.update_student(
                student_id, "DIOP", "Awa", "6ème A", "2025-2026", -100
            )

    def test_update_accepte_annee_valide(self):
        student_id = self._create_student()
        updated = self.student_service.update_student(
            student_id, "DIOP", "Awa", "6ème A", "2026-2027", 500_000
        )
        self.assertTrue(updated)
        self.assertEqual(
            self.student_service.get_student(student_id)["annee_scolaire"],
            "2026-2027",
        )

    def test_create_refuse_toujours_annee_invalide(self):
        """Régression : la validation à la création doit rester en place."""
        with self.assertRaises(ValueError):
            self.student_service.create_student(
                "DIOP", "Awa", "6ème A", "abcd-efgh", 500_000
            )

    # ------------------------------------------------------------------
    # IMP-10 : montant_total < déjà payé refusé
    # ------------------------------------------------------------------

    def test_update_refuse_montant_inferieur_deja_paye(self):
        student_id = self._create_student(500_000)
        self.payment_service.create_payment(student_id, 200_000, "especes")

        with self.assertRaises(ValueError) as ctx:
            self.student_service.update_student(
                student_id, "DIOP", "Awa", "6ème A", "2025-2026", 100_000
            )
        self.assertIn("déjà payé", str(ctx.exception))
        # Le montant total ne doit pas avoir changé
        student = self.student_service.get_student(student_id)
        self.assertEqual(student["montant_total"], 500_000)
        self.assertEqual(student["solde"], 300_000)

    def test_update_accepte_montant_egal_deja_paye(self):
        """Solde = 0 (élève soldé) : modification légitime."""
        student_id = self._create_student(500_000)
        self.payment_service.create_payment(student_id, 500_000, "especes")
        updated = self.student_service.update_student(
            student_id, "DIOP", "Awa", "6ème A", "2025-2026", 500_000
        )
        self.assertTrue(updated)
        self.assertEqual(self.student_service.get_student(student_id)["solde"], 0)

    def test_update_accepte_montant_superieur(self):
        student_id = self._create_student(500_000)
        self.payment_service.create_payment(student_id, 200_000, "especes")
        updated = self.student_service.update_student(
            student_id, "DIOP", "Awa", "6ème A", "2025-2026", 800_000
        )
        self.assertTrue(updated)
        self.assertEqual(
            self.student_service.get_student(student_id)["solde"], 600_000
        )

    def test_update_sans_paiement_montant_libre(self):
        """Sans aucun paiement, toute valeur positive est acceptable."""
        student_id = self._create_student(500_000)
        updated = self.student_service.update_student(
            student_id, "DIOP", "Awa", "6ème A", "2025-2026", 300_000
        )
        self.assertTrue(updated)
        self.assertEqual(
            self.student_service.get_student(student_id)["montant_total"], 300_000
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
