from repositories.student_repository import StudentRepository
from repositories.payment_repository import PaymentRepository
from config import format_montant, calculate_payment_status
from typing import List, Optional, Dict, Any
import re
import sqlite3
import logging

logger = logging.getLogger(__name__)

class StudentService:
    """Service pour la gestion des élèves avec logique métier.
    
    Ce service effectue la validation des données, calcule les soldes
    et les statuts de paiement, et gère les interactions avec le repository.
    """
    
    def __init__(self):
        self.student_repo = StudentRepository()
        self.payment_repo = PaymentRepository()
    
    def create_student(self, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> int:
        """Crée un nouvel élève avec validation.
        
        Args:
            nom: Nom de l'élève
            prenom: Prénom de l'élève
            classe: Classe de l'élève
            annee_scolaire: Année scolaire (format YYYY-YYYY)
            montant_total: Montant total des frais de scolarité
            
        Returns:
            ID de l'élève créé
            
        Raises:
            ValueError: Si les données sont invalides ou si l'élève existe déjà
        """
        montant_total = int(round(montant_total))
        if montant_total <= 0:
            raise ValueError("Le montant total doit être positif")
        
        # Validation du format de l'année scolaire
        if not re.match(r'^\d{4}-\d{4}$', annee_scolaire):
            raise ValueError("L'année scolaire doit être au format YYYY-YYYY (ex: 2024-2025)")
        
        try:
            student_id = self.student_repo.create(nom, prenom, classe, annee_scolaire, montant_total)
            logger.info(f"Élève créé avec succès: ID {student_id}, {nom} {prenom}, {classe}")
            return student_id
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"Tentative de création d'élève en double: {nom} {prenom}, {classe}, {annee_scolaire}")
                raise ValueError(
                    "Un élève avec ces informations existe déjà "
                    f"(nom: {nom}, prénom: {prenom}, classe: {classe}, année: {annee_scolaire})"
                )
            logger.error(f"Erreur lors de la création de l'élève: {e}")
            raise
    
    def get_student(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un élève avec ses informations de paiement"""
        student = self.student_repo.get_by_id(student_id)
        if student:
            payments = self.payment_repo.get_by_student(student_id)
            total_paid = sum(p['montant'] for p in payments)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = calculate_payment_status(balance, student['montant_total'])
            student['paiements'] = payments
        
        return student
    
    def get_all_students(self) -> List[Dict[str, Any]]:
        """Récupère tous les élèves avec leur statut de paiement (optimisé avec jointure)"""
        students = self.student_repo.get_all_with_payments()
        for student in students:
            total_paid = student.get('total_paye', 0)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = calculate_payment_status(balance, student['montant_total'])
        
        return students
    
    def get_students_by_class(self, classe: str) -> List[Dict[str, Any]]:
        """Récupère tous les élèves d'une classe avec leur statut de paiement (optimisé avec jointure)"""
        students = self.student_repo.get_by_class_with_payments(classe)
        for student in students:
            total_paid = student.get('total_paye', 0)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = calculate_payment_status(balance, student['montant_total'])
        
        return students
    
    def update_student(self, student_id: int, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> bool:
        """Met à jour un élève"""
        montant_total = int(round(montant_total))
        if montant_total <= 0:
            raise ValueError("Le montant total doit être positif")
        
        # Validation du format de l'année scolaire
        if not re.match(r'^\d{4}-\d{4}$', annee_scolaire):
            raise ValueError("L'année scolaire doit être au format YYYY-YYYY (ex: 2024-2025)")
        
        # Vérifier que le nouveau montant total n'est pas inférieur aux paiements déjà effectués
        total_paye = self.payment_repo.get_total_by_student(student_id)
        if montant_total < total_paye:
            raise ValueError(
                f"Le montant total ({format_montant(montant_total)}) ne peut pas être inférieur "
                f"au montant déjà payé ({format_montant(total_paye)})"
            )
        
        try:
            return self.student_repo.update(student_id, nom, prenom, classe, annee_scolaire, montant_total)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    "Un élève avec ces informations existe déjà "
                    f"(nom: {nom}, prénom: {prenom}, classe: {classe}, année: {annee_scolaire})"
                )
            raise
    
    def delete_student(self, student_id: int) -> bool:
        """Supprime un élève"""
        return self.student_repo.delete(student_id)
    
    def search_students(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des élèves par nom ou prénom avec leur statut de paiement (optimisé avec jointure)"""
        students = self.student_repo.search_with_payments(query)
        for student in students:
            total_paid = student.get('total_paye', 0)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = calculate_payment_status(balance, student['montant_total'])
        
        return students
    
    def get_classes(self) -> List[str]:
        """Récupère la liste de toutes les classes"""
        return self.student_repo.get_classes()
