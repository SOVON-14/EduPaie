import sqlite3
import os
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "data" / "edupaie.db"

def get_connection():
    """Crée et retourne une connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialise la base de données avec le schéma"""
    schema_path = Path(__file__).parent / "schema.sql"
    
    with get_connection() as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()

def ensure_database_exists():
    """Vérifie si la base de données existe, sinon la crée"""
    if not DB_PATH.exists():
        init_database()
