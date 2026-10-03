import base64
import hashlib
import os
from pathlib import Path


PASSWORD_ITERATIONS = 200_000
PASSWORD_SALT_BYTES = 16
PASSWORD_PREFIX = "pbkdf2_sha256"


def _get_user_data_dir() -> Path:
    from database.database import USER_DATA_DIR

    return USER_DATA_DIR


def get_master_password_file() -> Path:
    user_data_dir = _get_user_data_dir()
    user_data_dir.mkdir(parents=True, exist_ok=True)
    return user_data_dir / ".edupaie_auth"


def hash_password(password: str) -> str:
    """Crée un hachage PBKDF2-SHA256 d'un mot de passe."""
    if not isinstance(password, str) or not password:
        raise ValueError("Le mot de passe ne peut pas être vide.")

    salt = os.urandom(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_digest = base64.b64encode(digest).decode("ascii")
    return f"{PASSWORD_PREFIX}${PASSWORD_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hachage stocké."""
    if not password or not stored_hash:
        return False

    if not stored_hash.startswith(f"{PASSWORD_PREFIX}$"):
        return False

    try:
        _, iterations_str, salt_b64, digest_b64 = stored_hash.split("$", 3)
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64)
        expected_digest = base64.b64decode(digest_b64)
        computed_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac_compare(expected_digest, computed_digest)
    except (TypeError, ValueError):
        return False


def hmac_compare(expected: bytes, actual: bytes) -> bool:
    """Comparaison sécurisée de deux données hachées."""
    if len(expected) != len(actual):
        return False
    result = 0
    for a, b in zip(expected, actual):
        result |= a ^ b
    return result == 0


def ensure_master_password_file(password_file: str | Path, password: str) -> Path:
    """Crée un fichier de mot de passe protégé à partir d'un hash."""
    path = Path(password_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(hash_password(password), encoding="utf-8")
    return path


def is_master_password_configured() -> bool:
    password_file = get_master_password_file()
    return password_file.exists() and password_file.stat().st_size > 0


def prompt_for_app_auth(parent=None) -> bool:
    """Demande un mot de passe au démarrage. Le premier lancement le configure."""
    from PySide6.QtWidgets import QInputDialog, QMessageBox

    password_file = get_master_password_file()

    if not password_file.exists() or password_file.stat().st_size == 0:
        password, ok = QInputDialog.getText(
            parent,
            "Sécurisation EduPaie",
            "Choisissez un mot de passe maître pour protéger les données de l'application.",
            QInputDialog.EchoMode.Password,
        )
        if not ok or not str(password).strip():
            return False

        ensure_master_password_file(password_file, str(password).strip())
        return True

    password, ok = QInputDialog.getText(
        parent,
        "Accès EduPaie",
        "Entrez le mot de passe pour ouvrir l'application.",
        QInputDialog.EchoMode.Password,
    )
    if not ok:
        return False

    stored_hash = password_file.read_text(encoding="utf-8").strip()
    if not verify_password(str(password), stored_hash):
        QMessageBox.critical(
            parent,
            "Accès refusé",
            "Le mot de passe est incorrect.",
        )
        return False

    return True
