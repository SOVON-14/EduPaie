from database.database import get_connection
from typing import List, Optional, Dict, Any

class PaymentRepository:
    """Repository pour la gestion des paiements en base de données"""
    
    def create(self, student_id: int, montant: float, mode_paiement: str, numero_recu: str) -> int:
        """Crée un nouveau paiement et retourne son ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO payments (student_id, montant, mode_paiement, numero_recu)
                VALUES (?, ?, ?, ?)
                """,
                (student_id, montant, mode_paiement, numero_recu)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_by_id(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un paiement par son ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_by_student(self, student_id: int) -> List[Dict[str, Any]]:
        """Récupère tous les paiements d'un élève"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE student_id = ? ORDER BY date DESC",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les paiements"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments ORDER BY date DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def delete(self, payment_id: int) -> bool:
        """Supprime un paiement"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_total_by_student(self, student_id: int) -> float:
        """Calcule le total des paiements pour un élève"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(montant), 0) FROM payments WHERE student_id = ?",
                (student_id,)
            )
            return cursor.fetchone()[0]
    
    def get_total_all(self) -> float:
        """Calcule le total de tous les paiements"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(montant), 0) FROM payments")
            return cursor.fetchone()[0]
