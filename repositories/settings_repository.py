from database.database import get_connection
from typing import Optional, Dict, Any

class SettingsRepository:
    """Repository pour la gestion des paramètres de l'application"""
    
    def get(self, key: str) -> Optional[str]:
        """Récupère une valeur de paramètre par sa clé"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def set(self, key: str, value: str) -> bool:
        """Définit ou met à jour une valeur de paramètre"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, date_modification = CURRENT_TIMESTAMP
            """, (key, value, value))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all(self) -> Dict[str, str]:
        """Récupère tous les paramètres"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def delete(self, key: str) -> bool:
        """Supprime un paramètre"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
