from repositories.payment_repository import PaymentRepository
from repositories.student_repository import StudentRepository
from typing import Optional, Dict, Any
from datetime import datetime

class ReceiptService:
    """Service pour la gestion des reçus de paiement"""
    
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.student_repo = StudentRepository()
    
    def get_receipt_by_number(self, numero_recu: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un reçu par son numéro
        
        Args:
            numero_recu: Numéro unique du reçu
            
        Returns:
            Dictionnaire contenant toutes les informations du reçu ou None
        """
        from database.database import get_connection
        
        # Récupérer le paiement par numéro de reçu
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE numero_recu = ?",
                (numero_recu,)
            )
            payment_row = cursor.fetchone()
            
            if not payment_row:
                return None
            
            payment = dict(payment_row)
        
        # Récupérer les informations de l'élève
        student = self.student_repo.get_by_id(payment['student_id'])
        if not student:
            return None
        
        # Calculer le solde après ce paiement
        total_paye_avant = self._get_total_before_payment(payment['student_id'], payment['id'])
        solde_apres = student['montant_total'] - total_paye_avant - payment['montant']
        
        return {
            'numero_recu': payment['numero_recu'],
            'date_paiement': payment['date'],
            'montant_paye': payment['montant'],
            'mode_paiement': payment['mode_paiement'],
            'eleve': {
                'id': student['id'],
                'nom': student['nom'],
                'prenom': student['prenom'],
                'classe': student['classe'],
                'annee_scolaire': student['annee_scolaire']
            },
            'montant_total': student['montant_total'],
            'solde_apres_paiement': solde_apres,
            'statut': self._get_payment_status(solde_apres, student['montant_total'])
        }
    
    def get_student_receipts(self, student_id: int) -> list[Dict[str, Any]]:
        """
        Récupère tous les reçus d'un élève
        
        Args:
            student_id: ID de l'élève
            
        Returns:
            Liste des reçus chronologiques
        """
        payments = self.payment_repo.get_by_student(student_id)
        receipts = []
        
        for payment in payments:
            receipt = self.get_receipt_by_number(payment['numero_recu'])
            if receipt:
                receipts.append(receipt)
        
        return receipts
    
    def get_payment_receipt(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère le reçu pour un paiement spécifique
        
        Args:
            payment_id: ID du paiement
            
        Returns:
            Dictionnaire contenant les informations du reçu ou None
        """
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            return None
        
        return self.get_receipt_by_number(payment['numero_recu'])
    
    def _get_total_before_payment(self, student_id: int, payment_id: int) -> float:
        """
        Calcule le total des paiements avant un paiement donné
        
        Args:
            student_id: ID de l'élève
            payment_id: ID du paiement
            
        Returns:
            Total des paiements effectués avant ce paiement
        """
        from database.database import get_connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COALESCE(SUM(montant), 0) 
                FROM payments 
                WHERE student_id = ? AND id < ?
                """,
                (student_id, payment_id)
            )
            return cursor.fetchone()[0]
    
    def _get_payment_status(self, balance: float, total: float) -> str:
        """Détermine le statut de paiement"""
        if balance <= 0:
            return "Soldé"
        elif balance < total:
            return "Partiellement payé"
        else:
            return "Non payé"
