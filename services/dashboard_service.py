from repositories.student_repository import StudentRepository
from repositories.payment_repository import PaymentRepository
from typing import Dict, Any, List

class DashboardService:
    """Service pour le tableau de bord avec statistiques et vues d'ensemble"""
    
    def __init__(self):
        self.student_repo = StudentRepository()
        self.payment_repo = PaymentRepository()
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques globales du tableau de bord
        
        Returns:
            Dictionnaire contenant :
            - nombre_total_eleves: Nombre total d'élèves
            - total_encaisse: Montant total encaissé
            - total_restant_du: Montant total restant dû
            - nombre_eleves_non_soldes: Nombre d'élèves non soldés
            - nombre_eleves_soldes: Nombre d'élèves soldés
            - nombre_eleves_partiellement_payes: Nombre d'élèves partiellement payés
        """
        # Récupérer tous les élèves
        students = self.student_repo.get_all()
        nombre_total_eleves = len(students)
        
        # Calculer les totaux
        total_du = sum(student['montant_total'] for student in students)
        total_encaisse = self.payment_repo.get_total_all()
        total_restant_du = total_du - total_encaisse
        
        # Calculer les statuts
        nombre_eleves_soldes = 0
        nombre_eleves_partiellement_payes = 0
        nombre_eleves_non_soldes = 0
        
        for student in students:
            total_paye = self.payment_repo.get_total_by_student(student['id'])
            solde = student['montant_total'] - total_paye
            
            if solde <= 0:
                nombre_eleves_soldes += 1
            elif solde < student['montant_total']:
                nombre_eleves_partiellement_payes += 1
            else:
                nombre_eleves_non_soldes += 1
        
        # nombre_eleves_non_soldes inclut les non payés et partiellement payés
        nombre_eleves_non_soldes = nombre_eleves_partiellement_payes + nombre_eleves_non_soldes
        
        return {
            'nombre_total_eleves': nombre_total_eleves,
            'total_encaisse': total_encaisse,
            'total_restant_du': total_restant_du,
            'total_du': total_du,
            'nombre_eleves_non_soldes': nombre_eleves_non_soldes,
            'nombre_eleves_soldes': nombre_eleves_soldes,
            'nombre_eleves_partiellement_payes': nombre_eleves_partiellement_payes,
            'nombre_eleves_non_payes': nombre_eleves_non_soldes - nombre_eleves_partiellement_payes
        }
    
    def get_students_by_status(self, statut: str) -> List[Dict[str, Any]]:
        """
        Récupère les élèves filtrés par statut de paiement
        
        Args:
            statut: Statut de paiement ('Soldé', 'Partiellement payé', 'Non payé')
            
        Returns:
            Liste des élèves avec le statut demandé
        """
        students = self.student_repo.get_all()
        filtered_students = []
        
        for student in students:
            total_paye = self.payment_repo.get_total_by_student(student['id'])
            solde = student['montant_total'] - total_paye
            
            # Déterminer le statut
            if solde <= 0:
                current_statut = "Soldé"
            elif solde < student['montant_total']:
                current_statut = "Partiellement payé"
            else:
                current_statut = "Non payé"
            
            # Filtrer par statut
            if current_statut == statut:
                student['total_paye'] = total_paye
                student['solde'] = solde
                student['statut'] = current_statut
                filtered_students.append(student)
        
        return filtered_students
    
    def get_class_stats(self) -> List[Dict[str, Any]]:
        """
        Récupère les statistiques par classe
        
        Returns:
            Liste des statistiques par classe
        """
        classes = self.student_repo.get_classes()
        class_stats = []
        
        for classe in classes:
            students = self.student_repo.get_by_classe(classe)
            nombre_eleves = len(students)
            total_du = sum(student['montant_total'] for student in students)
            
            total_encaisse = 0
            nombre_soldes = 0
            nombre_partiellement_payes = 0
            nombre_non_payes = 0
            
            for student in students:
                total_paye = self.payment_repo.get_total_by_student(student['id'])
                total_encaisse += total_paye
                solde = student['montant_total'] - total_paye
                
                if solde <= 0:
                    nombre_soldes += 1
                elif solde < student['montant_total']:
                    nombre_partiellement_payes += 1
                else:
                    nombre_non_payes += 1
            
            class_stats.append({
                'classe': classe,
                'nombre_eleves': nombre_eleves,
                'total_du': total_du,
                'total_encaisse': total_encaisse,
                'total_restant': total_du - total_encaisse,
                'nombre_soldes': nombre_soldes,
                'nombre_partiellement_payes': nombre_partiellement_payes,
                'nombre_non_payes': nombre_non_payes
            })
        
        # Trier par nom de classe
        class_stats.sort(key=lambda x: x['classe'])
        
        return class_stats
    
    def get_recent_payments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les paiements récents
        
        Args:
            limit: Nombre maximum de paiements à retourner
            
        Returns:
            Liste des paiements récents avec informations de l'élève
        """
        payments = self.payment_repo.get_all()[:limit]
        enriched_payments = []
        
        for payment in payments:
            student = self.student_repo.get_by_id(payment['student_id'])
            if student:
                enriched_payment = {
                    **payment,
                    'eleve_nom': student['nom'],
                    'eleve_prenom': student['prenom'],
                    'eleve_classe': student['classe']
                }
                enriched_payments.append(enriched_payment)
        
        return enriched_payments
    
    def get_payment_summary_by_month(self) -> List[Dict[str, Any]]:
        """
        Récupère un résumé des paiements par mois
        
        Returns:
            Liste des résumés mensuels
        """
        from database.database import get_connection
        from datetime import datetime
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    strftime('%Y-%m', date) as mois,
                    COUNT(*) as nombre_paiements,
                    SUM(montant) as total_montant
                FROM payments
                GROUP BY strftime('%Y-%m', date)
                ORDER BY mois DESC
                """
            )
            rows = cursor.fetchall()
        
        summary = []
        for row in rows:
            summary.append({
                'mois': row[0],
                'nombre_paiements': row[1],
                'total_montant': row[2] if row[2] else 0
            })
        
        return summary
