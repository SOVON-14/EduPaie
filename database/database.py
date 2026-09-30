import sqlite3
import os
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "data" / "edupaie.db"

def get_connection():
    """Crée et retourne une connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # SQLite n'applique les clés étrangères que si le pragma est activé
    # pour CHAQUE connexion (correction CRIT-01 de l'audit : le ON DELETE
    # CASCADE de la table payments était inopérant sans cela).
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    """Initialise la base de données avec le schéma"""
    schema_path = Path(__file__).parent / "schema.sql"
    
    with get_connection() as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()

def cleanup_orphan_payments():
    """Supprime les paiements dont l'élève n'existe plus.

    Purge des paiements orphelins créés avant l'activation des clés
    étrangères (audit CRIT-01 : le CASCADE était inopérant, les paiements
    d'un élève supprimé restaient en base).

    Returns:
        Nombre de paiements orphelins supprimés
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM payments
            WHERE NOT EXISTS (
                SELECT 1 FROM students WHERE students.id = payments.student_id
            )
            """
        )
        deleted = cursor.rowcount
        conn.commit()
        return deleted

def ensure_database_exists():
    """Vérifie si la base de données existe, sinon la crée"""
    if not DB_PATH.exists():
        init_database()
    # Purge des orphelins hérités d'avant l'activation des clés étrangères
    cleanup_orphan_payments()
