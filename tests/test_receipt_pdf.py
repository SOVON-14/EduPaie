import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database.database as db
from services.payment_service import PaymentService
from services.receipt_service import ReceiptService
from services.student_service import StudentService


class ReceiptPdfTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="edupaie_receipt_")
        self.previous_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "test.db"
        db.init_database()

        self.student_service = StudentService()
        self.payment_service = PaymentService()
        self.receipt_service = ReceiptService()

    def tearDown(self):
        db.DB_PATH = self.previous_db_path
        self.temp_dir.cleanup()

    def test_generates_a_valid_pdf_receipt(self):
        student_id = self.student_service.create_student(
            "DIALLO", "Aminata", "6ème A", "2025-2026", 250_000
        )
        payment = self.payment_service.create_payment(
            student_id, 100_000, "mobile_money"
        )["payment"]
        output_path = Path(self.temp_dir.name) / "receipt.pdf"

        result_path = self.receipt_service.generate_pdf_receipt(
            payment["numero_recu"], str(output_path)
        )

        pdf_bytes = Path(result_path).read_bytes()
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertTrue(pdf_bytes.rstrip().endswith(b"%%EOF"))
        self.assertGreater(len(pdf_bytes), 1_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)