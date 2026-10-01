import PyInstaller.__main__
import sys
import os

def build_exe():
    """Construit l'exécutable Windows avec PyInstaller"""
    
    # Options PyInstaller
    pyinstaller_args = [
        'main.py',                      # Point d'entrée
        '--name=EduPaie',               # Nom de l'exécutable
        '--onefile',                    # Créer un seul fichier .exe
        '--windowed',                   # Application sans console (GUI)
        '--icon=resources/icons/app_icon.ico' if os.path.exists('resources/icons/app_icon.ico') else '',  # Icône si disponible
        '--add-data=database:database',  # Inclure le dossier database
        '--hidden-import=PySide6',      # Inclure PySide6
        '--hidden-import=reportlab',     # Inclure reportlab
        '--clean',                       # Nettoyer les fichiers temporaires
        '--noconfirm',                   # Pas de confirmation
    ]
    
    # Filtrer les arguments vides
    pyinstaller_args = [arg for arg in pyinstaller_args if arg]
    
    print("Construction de l'exécutable EduPaie...")
    print("Options:", ' '.join(pyinstaller_args))
    
    sys.argv = ['pyinstaller'] + pyinstaller_args
    PyInstaller.__main__.run()

if __name__ == '__main__':
    build_exe()
