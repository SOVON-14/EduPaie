# -*- coding: utf-8 -*-
"""Tests de non-régression pour la correction CRIT-02 (devise FCFA centralisée).

Vérifie que :
- format_montant() produit le format FCFA attendu (sans décimales) ;
- plus aucune occurrence "EUR" ne subsiste dans l'UI ni les services ;
- le plafond de paiement est aligné sur le solde de l'élève (IMP-03).

Exécution : python -m unittest tests.test_config_devise -v
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from config import DEVISE, DECIMALES, MONTANT_MAX, format_montant


class FormatMontantTestCase(unittest.TestCase):
    """format_montant() et centralisation de la devise (CRIT-02)."""

    def test_format_fcfa_sans_decimales(self):
        self.assertEqual(format_montant(150000), "150 000 FCFA")

    def test_format_grand_montant(self):
        self.assertEqual(format_montant(1250000), "1 250 000 FCFA")

    def test_format_montant_negatif(self):
        self.assertEqual(format_montant(-100000), "-100 000 FCFA")

    def test_aucune_devise_en_dur_dans_le_code(self):
        """Aucun fichier UI/service ne doit coder la devise en dur."""
        fichiers = [
            "ui/main_window.py",
            "ui/student_dialog.py",
            "ui/payment_dialog.py",
            "ui/student_detail.py",
            "services/receipt_service.py",
        ]
        racine = Path(__file__).parent.parent
        for relatif in fichiers:
            contenu = (racine / relatif).read_text(encoding="utf-8")
            self.assertNotIn(
                "EUR", contenu, f"{relatif} contient encore une devise en dur"
            )

    def test_devise_unique_definie_dans_config(self):
        self.assertEqual(DEVISE, "FCFA")
        self.assertEqual(DECIMALES, 0)


class PaymentDialogPlafondTestCase(unittest.TestCase):
    """IMP-03 : le plafond de paiement suit le solde de l'élève."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_devise_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_database()

        from services.payment_service import PaymentService
        from services.student_service import StudentService
        from services.receipt_service import ReceiptService
        from ui.payment_dialog import PaymentDialog

        self.student_service = StudentService()
        self.payment_service = PaymentService()
        self.receipt_service = ReceiptService()

        # Élève dont le total dû dépasse l'ancien plafond de 100 000
        self.student_id = self.student_service.create_student(
            "PLAFOND", "Test", "6ème A", "2025-2026", 2_000_000
        )
        self.dialog = PaymentDialog(
            None,
            self.student_id,
            self.student_service,
            self.payment_service,
            self.receipt_service,
        )

    def tearDown(self):
        self.dialog.close()
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    def test_plafond_paiement_aligne_sur_montant_max(self):
        self.assertEqual(self.dialog.montant_input.maximum(), float(MONTANT_MAX))

    def test_paiement_superieur_ancien_plafond_accepte(self):
        """Un paiement de 150 000 (au-dessus de l'ancien max de 100 000) doit être possible."""
        self.dialog.montant_input.setValue(150_000)
        self.dialog.validate_amount()
        self.assertTrue(self.dialog.ok_btn.isEnabled())

    def test_paiement_depassant_le_solde_refuse(self):
        self.dialog.montant_input.setValue(2_000_001)
        self.dialog.validate_amount()
        self.assertFalse(self.dialog.ok_btn.isEnabled())


if __name__ == "__main__":
    unittest.main(verbosity=2)
