import sys
from PySide6.QtWidgets import QApplication
from database.database import ensure_database_exists
from ui.main_window import MainWindow

def main():
    """Point d'entrée de l'application"""
    # S'assurer que la base de données existe
    ensure_database_exists()
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style moderne
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Exécuter l'application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
