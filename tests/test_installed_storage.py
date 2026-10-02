import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database.database as db


class InstalledStorageTestCase(unittest.TestCase):
    def test_installed_data_directory_uses_local_app_data(self):
        with tempfile.TemporaryDirectory(prefix="edupaie_localappdata_") as temp_dir:
            with patch.dict(os.environ, {"LOCALAPPDATA": temp_dir}), patch.object(
                db.sys, "frozen", True, create=True
            ):
                self.assertEqual(
                    db.get_user_data_dir(), Path(temp_dir) / "EduPaie"
                )

    def test_first_launch_copies_bundled_database_only_once(self):
        with tempfile.TemporaryDirectory(prefix="edupaie_install_") as temp_dir:
            root = Path(temp_dir)
            bundle_root = root / "_internal"
            bundled_db = bundle_root / "data" / "edupaie.db"
            user_data_dir = root / "LocalAppData" / "EduPaie"
            installed_db = user_data_dir / "edupaie.db"
            bundled_db.parent.mkdir(parents=True)

            previous_db_path = db.DB_PATH
            try:
                db.DB_PATH = bundled_db
                db.init_database()
                with db.get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO students
                            (nom, prenom, classe, annee_scolaire, montant_total)
                        VALUES ('DEMO', 'Élève', '6ème A', '2025-2026', 100000)
                        """
                    )

                db.DB_PATH = installed_db
                with patch.object(db.sys, "frozen", True, create=True), patch.object(
                    db.sys, "_MEIPASS", str(bundle_root), create=True
                ), patch.dict(os.environ, {"LOCALAPPDATA": str(user_data_dir.parent)}):
                    db.ensure_database_exists()
                    with db.get_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO students
                                (nom, prenom, classe, annee_scolaire, montant_total)
                            VALUES ('LOCAL', 'Modification', '5ème A', '2025-2026', 100000)
                            """
                        )

                    db.ensure_database_exists()
                    with db.get_connection() as conn:
                        students = conn.execute(
                            "SELECT nom FROM students ORDER BY nom"
                        ).fetchall()

                self.assertEqual([row["nom"] for row in students], ["DEMO", "LOCAL"])
            finally:
                db.DB_PATH = previous_db_path


if __name__ == "__main__":
    unittest.main(verbosity=2)