import contextlib
import sqlite3
import os
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "data" / "edupaie.db"

# Version du schéma, suivie via PRAGMA user_version (cf. migrate_schema)
SCHEMA_VERSION = 1

@contextlib.contextmanager
def get_connection():
    """Ouvre une connexion SQLite avec commit/rollback et fermeture garanties.

    Utilisation :
        with get_connection() as conn:
            conn.execute(...)

    La connexion est commitée si le bloc réussit, annulée (rollback) en cas
    d'exception, et TOUJOURS fermée à la sortie.

    Correction IMP-05 de l'audit : l'ancienne version retournait une
    connexion brute jamais fermée ; son cycle de références internes
    (connexion <-> curseurs en cache) n'était rompu que par le garbage
    collector, laissant le fichier .db verrouillé sous Windows et
    produisant des ResourceWarning « unclosed database ».
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        # SQLite n'applique les clés étrangères que si le pragma est activé
        # pour CHAQUE connexion (correction CRIT-01 de l'audit : le ON DELETE
        # CASCADE de la table payments était inopérant sans cela).
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialise la base de données avec le schéma"""
    schema_path = Path(__file__).parent / "schema.sql"
    
    with get_connection() as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

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

def migrate_schema():
    """Applique les migrations de schéma selon PRAGMA user_version.

    Corrige partiellement IMP-06 de l'audit : le schéma n'était créé que
    pour une base inexistante, sans mise à jour des bases anciennes.
    """
    with get_connection() as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version >= SCHEMA_VERSION:
            return
        try:
            if version < 1:
                _migrate_v1(conn)
        except sqlite3.IntegrityError as e:
            raise ValueError(
                "Migration impossible : la base contient des données "
                "incompatibles avec les nouvelles contraintes (doublons "
                "d'élèves ou montants invalides). Corrigez ces données avant "
                f"de relancer l'application. Détail : {e}"
            )

def _migrate_v1(conn):
    """v1 : montants en entiers + CHECK(> 0) + UNIQUE anti-doublons élèves.

    Corrections IMP-04, DB-02 et DB-03 de l'audit. SQLite ne permet pas de
    modifier une colonne existante : les tables sont recréées et les
    données copiées en arrondissant les montants à l'entier le plus proche
    (le FCFA n'a pas de sous-unité). La migration est atomique (BEGIN/COMMIT)
    et les clés étrangères sont désactivées le temps de la recréation
    (sinon le DROP TABLE des élèves supprimerait les paiements en CASCADE).
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript("""
        BEGIN;
        CREATE TABLE students_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            classe TEXT NOT NULL,
            annee_scolaire TEXT NOT NULL,
            montant_total INTEGER NOT NULL CHECK(montant_total > 0),
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(nom, prenom, classe, annee_scolaire)
        );
        INSERT INTO students_v1 (id, nom, prenom, classe, annee_scolaire, montant_total, date_creation)
            SELECT id, nom, prenom, classe, annee_scolaire, CAST(ROUND(montant_total) AS INTEGER), date_creation
            FROM students;
        DROP TABLE students;
        ALTER TABLE students_v1 RENAME TO students;

        CREATE TABLE payments_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            montant INTEGER NOT NULL CHECK(montant > 0),
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mode_paiement TEXT NOT NULL CHECK(mode_paiement IN ('especes', 'cheque', 'virement', 'mobile_money')),
            numero_recu TEXT NOT NULL UNIQUE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );
        INSERT INTO payments_v1 (id, student_id, montant, date, mode_paiement, numero_recu)
            SELECT id, student_id, CAST(ROUND(montant) AS INTEGER), date, mode_paiement, numero_recu
            FROM payments;
        DROP TABLE payments;
        ALTER TABLE payments_v1 RENAME TO payments;

        CREATE INDEX IF NOT EXISTS idx_payments_student_id ON payments(student_id);
        CREATE INDEX IF NOT EXISTS idx_students_classe ON students(classe);
        COMMIT;
    """)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

def ensure_database_exists():
    """Vérifie si la base de données existe, sinon la crée"""
    if not DB_PATH.exists():
        init_database()
    # Applique les migrations de schéma (montants entiers, contraintes SQL)
    migrate_schema()
    # Purge des orphelins hérités d'avant l'activation des clés étrangères
    cleanup_orphan_payments()
