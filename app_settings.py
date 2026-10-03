"""Module de configuration centralisée pour l'application EduPaie.

Ce module lit le fichier app_config.ini et fournit un accès uniforme
à toutes les configurations de l'application.
"""

import os
import configparser
from pathlib import Path
from typing import List

# Chemin du fichier de configuration
CONFIG_FILE = Path(__file__).parent / "app_config.ini"

# Charger la configuration
config = configparser.ConfigParser()
if CONFIG_FILE.exists():
    config.read(CONFIG_FILE, encoding='utf-8')
else:
    # Configuration par défaut si le fichier n'existe pas
    config['APP'] = {
        'name': 'EduPaie',
        'version': '1.0.0',
        'display_name': 'EduPaie - Gestion des frais de scolarité'
    }
    config['CURRENCY'] = {
        'code': 'FCFA',
        'max_amount': '1000000',
        'suffix': ' FCFA'
    }
    config['PAYMENT_MODES'] = {
        'modes': 'especes,cheque,virement,mobile_money'
    }
    config['SECURITY'] = {
        'auth_enabled': 'true',
        'password_iterations': '200000'
    }
    config['LOGGING'] = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }


def get_app_name() -> str:
    """Retourne le nom de l'application."""
    return config.get('APP', 'name', fallback='EduPaie')


def get_app_version() -> str:
    """Retourne la version de l'application."""
    return config.get('APP', 'version', fallback='1.0.0')


def get_app_display_name() -> str:
    """Retourne le nom d'affichage de l'application."""
    return config.get('APP', 'display_name', fallback='EduPaie')


def get_currency_code() -> str:
    """Retourne le code de la devise."""
    return config.get('CURRENCY', 'code', fallback='FCFA')


def get_max_amount() -> int:
    """Retourne le plafond maximum pour les montants."""
    return int(config.get('CURRENCY', 'max_amount', fallback='1000000'))


def get_currency_suffix() -> str:
    """Retourne le suffixe pour l'affichage des montants."""
    return config.get('CURRENCY', 'suffix', fallback=' FCFA')


def get_payment_modes() -> List[str]:
    """Retourne la liste des modes de paiement acceptés."""
    modes_str = config.get('PAYMENT_MODES', 'modes', fallback='especes,cheque,virement,mobile_money')
    return [mode.strip() for mode in modes_str.split(',')]


def get_college_classes() -> List[str]:
    """Retourne la liste des classes de collège."""
    classes_str = config.get('CLASSES', 'college', fallback='6ème A,6ème B,6ème C,5ème A,5ème B,5ème C,4ème A,4ème B,4ème C,3ème A,3ème B,3ème C')
    return [classe.strip() for classe in classes_str.split(',')]


def get_lycee_classes() -> List[str]:
    """Retourne la liste des classes de lycée."""
    classes_str = config.get('CLASSES', 'lycee', fallback='2nde A,2nde B,2nde C,1ère A,1ère B,1ère C,Terminale A,Terminale B,Terminale C')
    return [classe.strip() for classe in classes_str.split(',')]


def get_all_classes() -> List[str]:
    """Retourne toutes les classes (collège + lycée)."""
    return get_college_classes() + get_lycee_classes()


def is_auth_enabled() -> bool:
    """Retourne True si l'authentification est activée."""
    return config.getboolean('SECURITY', 'auth_enabled', fallback=True)


def get_password_iterations() -> int:
    """Retourne le nombre d'itérations pour le hachage du mot de passe."""
    return config.getint('SECURITY', 'password_iterations', fallback=200000)


def get_log_level() -> str:
    """Retourne le niveau de logging."""
    return config.get('LOGGING', 'level', fallback='INFO')


def get_log_format() -> str:
    """Retourne le format des logs."""
    return config.get('LOGGING', 'format', fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_database_path() -> Path:
    """Retourne le chemin de la base de données."""
    from database.database import DB_PATH
    return DB_PATH


def get_receipts_path() -> Path:
    """Retourne le chemin du dossier des reçus."""
    from database.database import USER_DATA_DIR
    return USER_DATA_DIR / "receipts"
