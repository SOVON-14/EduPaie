import sys
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from data.seed import seed
from services.student_service import StudentService


class SeedDataTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="edupaie_seed_")
        self.previous_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "test.db"

    def tearDown(self):
        db.DB_PATH = self.previous_db_path
        self.temp_dir.cleanup()

    def test_seed_creates_varied_dataset(self):
        seed()

        with db.get_connection() as conn:
            student_count = conn.execute(
                "SELECT COUNT(*) FROM students"
            ).fetchone()[0]
            payment_count = conn.execute(
                "SELECT COUNT(*) FROM payments"
            ).fetchone()[0]
            payment_modes = conn.execute(
                "SELECT COUNT(DISTINCT mode_paiement) FROM payments"
            ).fetchone()[0]
            max_payments_per_student = conn.execute(
                """
                SELECT MAX(payment_count)
                FROM (
                    SELECT COUNT(*) AS payment_count
                    FROM payments
                    GROUP BY student_id
                )
                """
            ).fetchone()[0]

        statuses = {
            student["statut"]
            for student in StudentService().get_all_students()
        }

        self.assertGreaterEqual(student_count, 15)
        self.assertGreaterEqual(payment_count, 15)
        self.assertEqual(payment_modes, 4)
        self.assertGreaterEqual(max_payments_per_student, 3)
        self.assertEqual(
            statuses,
            {"Soldé", "Partiellement payé", "Non payé"},
        )

    def test_seed_can_write_to_a_separate_database(self):
        active_db_path = db.DB_PATH
        sample_db_path = Path(self.temp_dir.name) / "sample.db"

        seed(sample_db_path)

        self.assertEqual(db.DB_PATH, active_db_path)
        with closing(sqlite3.connect(sample_db_path)) as conn:
            student_count = conn.execute(
                "SELECT COUNT(*) FROM students"
            ).fetchone()[0]
        self.assertGreaterEqual(student_count, 15)


if __name__ == "__main__":
    unittest.main(verbosity=2)