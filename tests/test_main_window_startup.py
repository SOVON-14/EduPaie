# -*- coding: utf-8 -*-
"""Tests de non-régression pour la correction IMP-01 de l'audit.

Vérifie que la liste des élèves est chargée au démarrage de la MainWindow
(avant correction, la table restait vide jusqu'au premier clic sur
« Actualiser »).

Exécution : python -m unittest tests.test_main_window_startup -v
"""

import os
import sys
import unittest
from pathlib import Path

# Plateforme hors-écran (CI / terminal sans affichage)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QAbstractItemView

import database.database as db
from ui.main_window import MainWindow
from ui.student_detail import StudentDetailDialog


class MainWindowStartupTestCase(unittest.TestCase):
    """Chargement des données au démarrage de la fenêtre principale."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        # Flux identique à main.py (initialise la DB réelle si besoin)
        db.ensure_database_exists()
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()

    def _row_count(self):
        return self.window.students_table.rowCount()

    # ------------------------------------------------------------------
    # IMP-01 : la table des élèves est remplie au démarrage
    # ------------------------------------------------------------------

    def test_students_table_loaded_at_startup(self):
        """La table des élèves doit être remplie dès la construction."""
        expected = len(self.window.student_service.get_all_students())
        self.assertGreater(expected, 0, "La base réelle doit contenir des élèves")
        self.assertEqual(self._row_count(), expected)

    def test_students_table_rows_match_database(self):
        """Les lignes affichées correspondent aux élèves de la base."""
        students = sorted(
            self.window.student_service.get_all_students(),
            key=lambda s: (s["nom"], s["prenom"]),
        )
        for row, student in enumerate(students):
            self.assertEqual(
                self.window.students_table.item(row, 0).text(),
                str(student["id"]),
            )
            self.assertEqual(
                self.window.students_table.item(row, 1).text(), student["nom"]
            )

    def test_class_filter_populated_at_startup(self):
        """Le filtre de classes doit contenir les classes existantes."""
        classes = self.window.student_service.get_classes()
        # "Toutes les classes" + une entrée par classe
        self.assertEqual(self.window.class_filter.count(), len(classes) + 1)

    def test_refresh_data_keeps_table_consistent(self):
        """Actualiser ne duplique pas les lignes."""
        self.window.refresh_data()
        expected = len(self.window.student_service.get_all_students())
        self.assertEqual(self._row_count(), expected)

    # ------------------------------------------------------------------
    # IMP-02 : les tableaux ne sont pas éditables
    # ------------------------------------------------------------------

    def test_main_window_tables_not_editable(self):
        """IMP-02 : aucune cellule des 3 tableaux principaux n'est éditable."""
        no_edit = QAbstractItemView.NoEditTriggers
        self.assertEqual(self.window.students_table.editTriggers(), no_edit)
        self.assertEqual(self.window.stats_table.editTriggers(), no_edit)
        self.assertEqual(self.window.class_table.editTriggers(), no_edit)

    def test_payments_table_not_editable(self):
        """IMP-02 : la table des paiements du détail élève n'est pas éditable."""
        students = self.window.student_service.get_all_students()
        self.assertTrue(students, "la base doit contenir des élèves")
        dialog = StudentDetailDialog(
            students[0]["id"],
            self.window.student_service,
            self.window.payment_service,
            self.window.receipt_service,
            None,
        )
        try:
            self.assertEqual(
                dialog.payments_table.editTriggers(),
                QAbstractItemView.NoEditTriggers,
            )
        finally:
            dialog.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
