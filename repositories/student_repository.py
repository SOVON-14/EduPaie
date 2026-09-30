from database.database import get_connection
from typing import List, Optional, Dict, Any

class StudentRepository:
    """Repository pour la gestion des élèves en base de données"""
    
    def create(self, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> int:
        """Crée un nouvel élève et retourne son ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO students (nom, prenom, classe, annee_scolaire, montant_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nom, prenom, classe, annee_scolaire, montant_total)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un élève par son ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les élèves"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students ORDER BY nom, prenom")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_classe(self, classe: str) -> List[Dict[str, Any]]:
        """Récupère tous les élèves d'une classe"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE classe = ? ORDER BY nom, prenom",
                (classe,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update(self, student_id: int, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> bool:
        """Met à jour un élève"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE students 
                SET nom = ?, prenom = ?, classe = ?, annee_scolaire = ?, montant_total = ?
                WHERE id = ?
                """,
                (nom, prenom, classe, annee_scolaire, montant_total, student_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete(self, student_id: int) -> bool:
        """Supprime un élève (et ses paiements via CASCADE)"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des élèves par nom ou prénom"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM students 
                WHERE nom LIKE ? OR prenom LIKE ?
                ORDER BY nom, prenom
                """,
                (f"%{query}%", f"%{query}%")
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_classes(self) -> List[str]:
        """Récupère la liste de toutes les classes uniques"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT classe FROM students ORDER BY classe")
            return [row[0] for row in cursor.fetchall()]
