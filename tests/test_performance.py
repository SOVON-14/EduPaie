# -*- coding: utf-8 -*-
"""Tests de performance pour EduPaie.

Ces tests vérifient que l'application reste performante avec beaucoup de données.
"""

import os
import sys
import tempfile
import unittest
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from services.student_service import StudentService
from services.payment_service import PaymentService
from services.dashboard_service import DashboardService


class PerformanceTestCase(unittest.TestCase):
    """Tests de performance avec beaucoup de données."""

    @classmethod
    def setUpClass(cls):
        cls.app = None  # Pas besoin de QApplication pour les tests de performance

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="edupaie_perf_")
        self._old_db_path = db.DB_PATH
        db.DB_PATH = Path(self._tmp.name) / "test.db"
        db.init_database()

        self.student_service = StudentService()
        self.payment_service = PaymentService()
        self.dashboard_service = DashboardService()

    def tearDown(self):
        db.DB_PATH = self._old_db_path
        self._tmp.cleanup()

    def test_load_100_students_performance(self):
        """Test le chargement de 100 élèves."""
        # Créer 100 élèves
        start_time = time.time()
        for i in range(100):
            self.student_service.create_student(
                f"Nom{i}", f"Prenom{i}", "6ème A", "2024-2025", 500000
            )
        creation_time = time.time() - start_time
        
        print(f"\nCréation de 100 élèves: {creation_time:.2f}s")
        self.assertLess(creation_time, 5.0, "La création de 100 élèves devrait prendre moins de 5 secondes")
        
        # Charger tous les élèves
        start_time = time.time()
        students = self.student_service.get_all_students()
        load_time = time.time() - start_time
        
        print(f"Chargement de 100 élèves: {load_time:.2f}s")
        self.assertEqual(len(students), 100)
        self.assertLess(load_time, 1.0, "Le chargement de 100 élèves devrait prendre moins de 1 seconde")

    def test_load_100_students_with_payments_performance(self):
        """Test le chargement de 100 élèves avec des paiements."""
        # Créer 100 élèves avec des paiements
        for i in range(100):
            student_id = self.student_service.create_student(
                f"Nom{i}", f"Prenom{i}", "6ème A", "2024-2025", 500000
            )
            # Ajouter 1 à 3 paiements par élève
            num_payments = (i % 3) + 1
            for j in range(num_payments):
                self.payment_service.create_payment(
                    student_id, 100000, "especes"
                )
        
        # Charger tous les élèves (avec jointure optimisée)
        start_time = time.time()
        students = self.student_service.get_all_students()
        load_time = time.time() - start_time
        
        print(f"\nChargement de 100 élèves avec paiements: {load_time:.2f}s")
        self.assertEqual(len(students), 100)
        self.assertLess(load_time, 2.0, "Le chargement de 100 élèves avec paiements devrait prendre moins de 2 secondes")

    def test_dashboard_stats_performance(self):
        """Test le calcul des statistiques du tableau de bord."""
        # Créer 100 élèves avec des paiements variés
        for i in range(100):
            student_id = self.student_service.create_student(
                f"Nom{i}", f"Prenom{i}", "6ème A", "2024-2025", 500000
            )
            # Ajouter des paiements variés
            if i % 3 == 0:
                # Élève soldé
                self.payment_service.create_payment(student_id, 500000, "especes")
            elif i % 3 == 1:
                # Élève partiellement payé
                self.payment_service.create_payment(student_id, 250000, "especes")
            # Sinon: élève non payé
        
        # Calculer les statistiques
        start_time = time.time()
        stats = self.dashboard_service.get_overview_stats()
        stats_time = time.time() - start_time
        
        print(f"\nCalcul des statistiques tableau de bord: {stats_time:.2f}s")
        self.assertEqual(stats['nombre_total_eleves'], 100)
        self.assertLess(stats_time, 1.0, "Le calcul des statistiques devrait prendre moins de 1 seconde")

    def test_search_performance(self):
        """Test la performance de la recherche."""
        # Créer 100 élèves
        for i in range(100):
            self.student_service.create_student(
                f"Nom{i}", f"Prenom{i}", "6ème A", "2024-2025", 500000
            )
        
        # Rechercher un élève
        start_time = time.time()
        results = self.student_service.search_students("Nom50")
        search_time = time.time() - start_time
        
        print(f"\nRecherche d'élève: {search_time:.2f}s")
        self.assertEqual(len(results), 1)
        self.assertLess(search_time, 0.5, "La recherche devrait prendre moins de 0.5 seconde")

    def test_class_filter_performance(self):
        """Test la performance du filtrage par classe."""
        # Créer des élèves dans différentes classes
        classes = ["6ème A", "6ème B", "5ème A", "5ème B"]
        for i, classe in enumerate(classes):
            for j in range(25):
                self.student_service.create_student(
                    f"Nom{i}{j}", f"Prenom{i}{j}", classe, "2024-2025", 500000
                )
        
        # Filtrer par classe
        start_time = time.time()
        students = self.student_service.get_students_by_class("6ème A")
        filter_time = time.time() - start_time
        
        print(f"\nFiltrage par classe: {filter_time:.2f}s")
        self.assertEqual(len(students), 25)
        self.assertLess(filter_time, 0.5, "Le filtrage par classe devrait prendre moins de 0.5 seconde")


if __name__ == "__main__":
    unittest.main(verbosity=2)
