from repositories.payment_repository import PaymentRepository
from repositories.student_repository import StudentRepository
from config import format_montant, calculate_payment_status
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

class PaymentService:
    """Service pour la gestion des paiements avec validation du solde"""
    
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.student_repo = StudentRepository()
    
    def create_payment(self, student_id: int, montant: float, mode_paiement: str) -> Dict[str, Any]:
        """
        Crée un nouveau paiement avec validation du solde
        
        Args:
            student_id: ID de l'élève
            montant: Montant du paiement
            mode_paiement: Mode de paiement (especes, cheque, virement, mobile_money)
            
        Returns:
            Dictionnaire contenant le paiement créé et le nouveau solde
            
        Raises:
            ValueError: Si le montant est invalide ou dépasse le solde restant
        """
        # Conversion en entier (FCFA n'a pas de sous-unité)
        montant = int(round(montant))
        
        # Validation du montant
        if montant <= 0:
            raise ValueError("Le montant doit être positif")
        
        # Validation du mode de paiement
        modes_valides = ['especes', 'cheque', 'virement', 'mobile_money']
        if mode_paiement not in modes_valides:
            raise ValueError(f"Mode de paiement invalide. Modes valides: {', '.join(modes_valides)}")
        
        # Récupérer l'élève
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Élève introuvable")
        
        # Calculer le solde actuel
        total_paye = self.payment_repo.get_total_by_student(student_id)
        solde_restant = student['montant_total'] - total_paye
        
        # Validation : le paiement ne doit pas faire passer le solde en dessous de 0
        if montant > solde_restant:
            raise ValueError(
                f"Le montant ({format_montant(montant)}) dépasse le solde restant ({format_montant(solde_restant)}). "
                f"Solde après paiement: {format_montant(solde_restant - montant)}"
            )
        
        # Générer un numéro de reçu unique
        numero_recu = self._generate_receipt_number()
        
        # Créer le paiement
        payment_id = self.payment_repo.create(student_id, montant, mode_paiement, numero_recu)
        
        # Récupérer le paiement créé
        payment = self.payment_repo.get_by_id(payment_id)
        
        # Calculer le nouveau solde
        nouveau_solde = solde_restant - montant
        
        return {
            'payment': payment,
            'solde_restant': nouveau_solde,
            'solde_precedent': solde_restant,
            'statut': calculate_payment_status(nouveau_solde, student['montant_total'])
        }
    
    def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un paiement par son ID"""
        return self.payment_repo.get_by_id(payment_id)
    
    def get_student_payments(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Récupère tous les paiements d'un élève avec détails complets
        
        Args:
            student_id: ID de l'élève
            
        Returns:
            Liste des paiements avec informations de l'élève et solde (plus récent en premier)
        """
        from database.database import get_connection
        
        # Récupérer les paiements dans l'ordre chronologique (du plus ancien au plus récent)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE student_id = ? ORDER BY date ASC, id ASC",
                (student_id,)
            )
            payments_chronological = [dict(row) for row in cursor.fetchall()]
        
        student = self.student_repo.get_by_id(student_id)
        
        if not student:
            return payments_chronological
        
        # Enrichir chaque paiement avec le solde après ce paiement
        enriched_payments = []
        cumul_paye = 0
        
        for payment in payments_chronological:
            cumul_paye += payment['montant']
            solde_apres = student['montant_total'] - cumul_paye
            
            enriched_payment = {
                **payment,
                'eleve_nom': student['nom'],
                'eleve_prenom': student['prenom'],
                'eleve_classe': student['classe'],
                'solde_apres_paiement': solde_apres,
                'statut': calculate_payment_status(solde_apres, student['montant_total'])
            }
            enriched_payments.append(enriched_payment)
        
        # Retourner en ordre inverse (plus récent en premier)
        return list(reversed(enriched_payments))
    
    def get_all_payments(self) -> List[Dict[str, Any]]:
        """Récupère tous les paiements"""
        return self.payment_repo.get_all()
    
    def delete_payment(self, payment_id: int) -> bool:
        """Supprime un paiement"""
        return self.payment_repo.delete(payment_id)
    
    def get_student_balance(self, student_id: int) -> Dict[str, Any]:
        """
        Calcule le solde actuel d'un élève
        
        Returns:
            Dictionnaire avec total_du, total_paye, solde_restant, statut
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Élève introuvable")
        
        total_paye = self.payment_repo.get_total_by_student(student_id)
        solde_restant = student['montant_total'] - total_paye
        
        return {
            'student_id': student_id,
            'total_du': student['montant_total'],
            'total_paye': total_paye,
            'solde_restant': solde_restant,
            'statut': calculate_payment_status(solde_restant, student['montant_total'])
        }
    
    def _generate_receipt_number(self) -> str:
        """Génère un numéro de reçu unique"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"REC-{timestamp}-{unique_id}"
