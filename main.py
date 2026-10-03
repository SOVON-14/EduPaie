import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from database.database import ensure_database_exists
from ui.main_window import MainWindow
from security import prompt_for_app_auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """Point d'entrée de l'application."""
    try:
        # S'assurer que la base de données existe
        ensure_database_exists()

        # Créer l'application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("EduPaie")
        app.setApplicationDisplayName("EduPaie")
        app.setStyle('Fusion')

        # Demander l'authentification
        if not prompt_for_app_auth():
            logger.info("Authentification refusée ou annulée.")
            return 0

        # Créer et afficher la fenêtre principale
        window = MainWindow()
        window.show()

        logger.info("Démarrage de l'application EduPaie réussi.")
        return app.exec()
    except Exception as exc:
        logger.exception("Erreur critique au démarrage de l'application")

        # Feedback convivial pour l'utilisateur final
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "EduPaie - Erreur",
            "Une erreur critique empêche le démarrage de l'application.\n\n"
            f"Détail technique : {exc}",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
