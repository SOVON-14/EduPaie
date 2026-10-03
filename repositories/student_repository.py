from database.database import get_connection
from typing import List, Optional, Dict, Any

class StudentRepository:
    """Repository pour la gestion des élèves en base de données.
    
    Ce repository fournit les opérations CRUD pour les élèves,
    ainsi que des méthodes de recherche et de filtrage.
    """
    
    def create(self, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> int:
        """Crée un nouvel élève et retourne son ID.
        
        Args:
            nom: Nom de l'élève
            prenom: Prénom de l'élève
            classe: Classe de l'élève
            annee_scolaire: Année scolaire (format YYYY-YYYY)
            montant_total: Montant total des frais de scolarité
            
        Returns:
            ID de l'élève créé
            
        Raises:
            sqlite3.IntegrityError: Si un élève avec les mêmes informations existe déjà
        """
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
        """Récupère un élève par son ID.
        
        Args:
            student_id: ID de l'élève
            
        Returns:
            Dictionnaire contenant les informations de l'élève ou None
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Récupère tous les élèves.
        
        Returns:
            Liste de tous les élèves
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students ORDER BY nom, prenom")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_classe(self, classe: str) -> List[Dict[str, Any]]:
        """Récupère tous les élèves d'une classe.
        
        Args:
            classe: Nom de la classe
            
        Returns:
            Liste des élèves de cette classe
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM students WHERE classe = ? ORDER BY nom, prenom",
                (classe,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update(self, student_id: int, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> bool:
        """Met à jour un élève.
        
        Args:
            student_id: ID de l'élève
            nom: Nouveau nom
            prenom: Nouveau prénom
            classe: Nouvelle classe
            annee_scolaire: Nouvelle année scolaire
            montant_total: Nouveau montant total
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
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
        """Supprime un élève (et ses paiements via CASCADE).
        
        Args:
            student_id: ID de l'élève à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des élèves par nom ou prénom.
        
        Args:
            query: Chaîne de recherche (nom ou prénom)
            
        Returns:
            Liste des élèves correspondant à la recherche
        """
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
    
    def get_all_with_payments(self) -> List[Dict[str, Any]]:
        """Récupère tous les élèves avec leurs paiements en une seule requête (optimisation N+1)"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.*,
                    COALESCE(SUM(p.montant), 0) as total_paye
                FROM students s
                LEFT JOIN payments p ON s.id = p.student_id
                GROUP BY s.id
                ORDER BY s.nom, s.prenom
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_class_with_payments(self, classe: str) -> List[Dict[str, Any]]:
        """Récupère tous les élèves d'une classe avec leurs paiements en une seule requête"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.*,
                    COALESCE(SUM(p.montant), 0) as total_paye
                FROM students s
                LEFT JOIN payments p ON s.id = p.student_id
                WHERE s.classe = ?
                GROUP BY s.id
                ORDER BY s.nom, s.prenom
            """, (classe,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_with_payments(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des élèves par nom ou prénom avec leurs paiements en une seule requête"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    s.*,
                    COALESCE(SUM(p.montant), 0) as total_paye
                FROM students s
                LEFT JOIN payments p ON s.id = p.student_id
                WHERE s.nom LIKE ? OR s.prenom LIKE ?
                GROUP BY s.id
                ORDER BY s.nom, s.prenom
            """, (f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()]
