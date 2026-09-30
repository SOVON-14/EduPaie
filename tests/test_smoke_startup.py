# -*- coding: utf-8 -*-
"""Smoke test : démarre l'application complète hors-écran avec le correctif CRIT-01.

Simule le flux de main.py (ensure_database_exists -> QApplication -> MainWindow)
sans lancer la boucle d'événements. Valide que l'application démarre et que les
données réelles se chargent.

Exécution : python -m unittest tests.test_smoke_startup -v
"""

import os
import sys
import unittest
from pathlib import Path

#Plateforme hors-écran (CI / terminal sans affichage)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication

import database.database as db
from ui.main_window import MainWindow


class SmokeStartupTestCase(unittest.TestCase):
    """Démarrage complet de l'application (hors-écran)."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_app_starts_with_real_database(self):
        """L'application démarre, la DB s'initialise et les stats se chargent."""
        # Flux identique à main.py
        db.ensure_database_exists()

        window = MainWindow()

        # L'élève de la DB réelle apparaît dans les statistiques
        metric = window.stats_table.item(0, 0)
        value = window.stats_table.item(0, 1)
        self.assertIsNotNone(metric)
        self.assertIsNotNone(value)
        self.assertEqual(metric.text(), "Nombre total d'élèves")
        self.assertGreater(int(value.text()), 0)

        # Le correctif CRIT-01 est actif sur les connexions de l'app
        with db.get_connection() as conn:
            fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(fk, 1)

        # La base réelle ne contient aucun paiement orphelin
        orphans = db.cleanup_orphan_payments()
        self.assertEqual(orphans, 0)

        window.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
