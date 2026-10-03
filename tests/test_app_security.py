import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from security import ensure_master_password_file, hash_password, verify_password


class AppSecurityTestCase(unittest.TestCase):
    def test_hash_password_verifies_correct_value(self):
        password_hash = hash_password("MonMotDePasse123!")

        self.assertTrue(verify_password("MonMotDePasse123!", password_hash))
        self.assertFalse(verify_password("mauvais-mot-de-passe", password_hash))

    def test_password_file_is_created_with_hash(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            password_file = Path(tmp_dir) / ".edupaie_auth"

            ensure_master_password_file(password_file, "Secret123!")

            self.assertTrue(password_file.exists())
            self.assertTrue(password_file.read_text(encoding="utf-8").startswith("pbkdf2_sha256$"))
            self.assertTrue(verify_password("Secret123!", password_file.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
