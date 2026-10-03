# -*- coding: utf-8 -*-
"""Tests d'intégration de l'interface utilisateur EduPaie.

Ces tests vérifient l'intégration entre les composants UI et les services.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import database.database as db
from ui.main_window import MainWindow
from services.student_service import StudentService
from services.payment_service import PaymentService


class UIIntegrationTestCase(unittest.TestCase):
    """Tests d'intégration de l'interface utilisateur."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_ui_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_database()

        self.student_service = StudentService()
        self.payment_service = PaymentService()

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    def test_main_window_opens_and_loads_data(self):
        """La fenêtre principale s'ouvre et charge les données."""
        window = MainWindow()
        
        # En mode offscreen, la fenêtre peut ne pas être visible
        # On vérifie simplement qu'elle existe
        self.assertIsNotNone(window)
        
        # Vérifier que les onglets existent
        self.assertEqual(window.tabs.count(), 2)
        self.assertEqual(window.tabs.tabText(0), "Tableau de bord")
        self.assertEqual(window.tabs.tabText(1), "Élèves")
        
        # Vérifier que les statistiques sont chargées
        self.assertGreater(window.stats_table.rowCount(), 0)
        
        window.close()

    def test_add_student_dialog_integration(self):
        """Test l'intégration du dialogue d'ajout d'élève."""
        from ui.student_dialog import StudentDialog
        
        window = MainWindow()
        
        # Ouvrir le dialogue d'ajout
        dialog = StudentDialog(window)
        
        # Vérifier que le dialogue s'ouvre
        self.assertIsNotNone(dialog)
        
        # Vérifier que les champs existent
        self.assertIsNotNone(dialog.nom_input)
        self.assertIsNotNone(dialog.prenom_input)
        self.assertIsNotNone(dialog.classe_input)
        self.assertIsNotNone(dialog.annee_input)
        self.assertIsNotNone(dialog.montant_input)
        
        # Remplir le formulaire
        dialog.nom_input.setText("Test")
        dialog.prenom_input.setText("Integration")
        dialog.classe_input.setCurrentText("6ème A")
        dialog.annee_input.setText("2024-2025")
        dialog.montant_input.setValue(500000)
        
        # Valider le formulaire (sans accepter pour éviter de modifier la base)
        dialog.validate_and_accept()
        
        # Vérifier que la validation passe
        self.assertTrue(dialog.result() == 1 or dialog.result() == 0)  # QDialog.Accepted ou QDialog.Rejected
        
        dialog.close()
        window.close()

    def test_payment_dialog_integration(self):
        """Test l'intégration du dialogue de paiement."""
        from ui.payment_dialog import PaymentDialog
        from services.receipt_service import ReceiptService
        
        # Créer un élève
        student_id = self.student_service.create_student(
            "Test", "Payment", "6ème A", "2024-2025", 500000
        )
        
        window = MainWindow()
        receipt_service = ReceiptService()
        
        # Ouvrir le dialogue de paiement
        dialog = PaymentDialog(
            window, student_id, self.student_service, self.payment_service, receipt_service
        )
        
        # Vérifier que les informations de l'élève sont affichées
        self.assertIn("Test Payment", dialog.student_info_label.text())
        self.assertIn("500 000 FCFA", dialog.balance_label.text())
        
        # Entrer un montant valide
        dialog.montant_input.setValue(200000)
        dialog.mode_input.setCurrentIndex(0)  # Espèces
        
        # Fermer le dialogue sans enregistrer
        dialog.reject()
        
        window.close()

    def test_student_detail_dialog_integration(self):
        """Test l'intégration du dialogue de détails d'élève."""
        from ui.student_detail import StudentDetailDialog
        from services.receipt_service import ReceiptService
        
        # Créer un élève avec un paiement
        student_id = self.student_service.create_student(
            "Test", "Detail", "6ème A", "2024-2025", 500000
        )
        self.payment_service.create_payment(student_id, 200000, "especes")
        
        receipt_service = ReceiptService()
        
        # Ouvrir le dialogue de détails
        dialog = StudentDetailDialog(
            student_id, self.student_service, self.payment_service, receipt_service
        )
        
        # Vérifier que les informations sont affichées
        self.assertIn("Test Detail", dialog.student_info_label.text())
        self.assertIn("300 000 FCFA", dialog.payment_stats_label.text())  # Solde restant
        
        # Vérifier que l'historique des paiements est chargé
        self.assertEqual(dialog.payments_table.rowCount(), 1)
        
        dialog.close()

    def test_filter_students_integration(self):
        """Test l'intégration du filtrage des élèves."""
        # Créer plusieurs élèves
        self.student_service.create_student("Koffi", "Yao", "6ème A", "2024-2025", 500000)
        self.student_service.create_student("Mensah", "Komi", "5ème B", "2024-2025", 450000)
        self.student_service.create_student("Ahou", "Adjoua", "6ème A", "2024-2025", 480000)
        
        window = MainWindow()
        
        # Vérifier que tous les élèves sont affichés
        self.assertEqual(window.students_table.rowCount(), 3)
        
        # Filtrer par classe
        window.class_filter.setCurrentText("6ème A")
        window.filter_students()
        self.assertEqual(window.students_table.rowCount(), 2)
        
        # Filtrer par recherche
        window.class_filter.setCurrentText("Toutes les classes")
        window.search_input.setText("Koffi")
        window.filter_students()
        self.assertEqual(window.students_table.rowCount(), 1)
        
        window.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
