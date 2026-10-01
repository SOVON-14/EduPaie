from repositories.student_repository import StudentRepository
from repositories.payment_repository import PaymentRepository
from config import format_montant
from typing import List, Optional, Dict, Any
import re
import sqlite3

class StudentService:
    """Service pour la gestion des élèves avec logique métier"""
    
    def __init__(self):
        self.student_repo = StudentRepository()
        self.payment_repo = PaymentRepository()
    
    def _valider_donnees_eleve(self, annee_scolaire: str, montant_total: float) -> int:
        """Valide les données communes à la création et à la modification.

        Correction IMP-09 de l'audit : la validation (notamment du format de
        l'année scolaire) n'était appliquée qu'à la création, pas à la
        modification.
        Correction IMP-04 de l'audit : les montants sont convertis en entiers
        (le FCFA n'a pas de sous-unité) et stockés comme tels en base.
        """
        montant_total = int(round(montant_total))
        if montant_total <= 0:
            raise ValueError("Le montant total doit être positif")

        # Validation du format de l'année scolaire
        if not re.match(r'^\d{4}-\d{4}$', annee_scolaire):
            raise ValueError("L'année scolaire doit être au format YYYY-YYYY (ex: 2024-2025)")

        return montant_total

    def create_student(self, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> int:
        """Crée un nouvel élève"""
        montant_total = self._valider_donnees_eleve(annee_scolaire, montant_total)

        try:
            return self.student_repo.create(nom, prenom, classe, annee_scolaire, montant_total)
        except sqlite3.IntegrityError:
            # Correction DB-03 de l'audit : doublons d'élèves interdits en base
            raise ValueError(
                "Un élève identique existe déjà (même nom, prénom, classe et année scolaire)."
            )
    
    def get_student(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un élève avec ses informations de paiement"""
        student = self.student_repo.get_by_id(student_id)
        if student:
            payments = self.payment_repo.get_by_student(student_id)
            total_paid = sum(p['montant'] for p in payments)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = self._get_payment_status(balance, student['montant_total'])
            student['paiements'] = payments
        
        return student
    
    def get_all_students(self) -> List[Dict[str, Any]]:
        """Récupère tous les élèves avec leur statut de paiement"""
        students = self.student_repo.get_all()
        for student in students:
            payments = self.payment_repo.get_by_student(student['id'])
            total_paid = sum(p['montant'] for p in payments)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = self._get_payment_status(balance, student['montant_total'])
        
        return students
    
    def get_students_by_class(self, classe: str) -> List[Dict[str, Any]]:
        """Récupère tous les élèves d'une classe avec leur statut de paiement"""
        students = self.student_repo.get_by_classe(classe)
        for student in students:
            payments = self.payment_repo.get_by_student(student['id'])
            total_paid = sum(p['montant'] for p in payments)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = self._get_payment_status(balance, student['montant_total'])
        
        return students
    
    def update_student(self, student_id: int, nom: str, prenom: str, classe: str, annee_scolaire: str, montant_total: float) -> bool:
        """Met à jour un élève"""
        montant_total = self._valider_donnees_eleve(annee_scolaire, montant_total)

        # Correction IMP-10 de l'audit : refuser un nouveau montant total
        # inférieur au montant déjà payé (le solde deviendrait négatif).
        total_paye = self.payment_repo.get_total_by_student(student_id)
        if montant_total < total_paye:
            raise ValueError(
                f"Le montant total ({format_montant(montant_total)}) est inférieur "
                f"au montant déjà payé ({format_montant(total_paye)}) : "
                "le solde deviendrait négatif."
            )

        try:
            return self.student_repo.update(student_id, nom, prenom, classe, annee_scolaire, montant_total)
        except sqlite3.IntegrityError:
            # Correction DB-03 de l'audit : doublons d'élèves interdits en base
            raise ValueError(
                "Impossible de modifier : un autre élève avec le même nom, "
                "prénom, classe et année scolaire existe déjà."
            )
    
    def delete_student(self, student_id: int) -> bool:
        """Supprime un élève"""
        return self.student_repo.delete(student_id)
    
    def search_students(self, query: str) -> List[Dict[str, Any]]:
        """Recherche des élèves par nom ou prénom avec leur statut de paiement"""
        students = self.student_repo.search(query)
        for student in students:
            payments = self.payment_repo.get_by_student(student['id'])
            total_paid = sum(p['montant'] for p in payments)
            balance = student['montant_total'] - total_paid
            
            student['total_paye'] = total_paid
            student['solde'] = balance
            student['statut'] = self._get_payment_status(balance, student['montant_total'])
        
        return students
    
    def get_classes(self) -> List[str]:
        """Récupère la liste de toutes les classes"""
        return self.student_repo.get_classes()
    
    def _get_payment_status(self, balance: float, total: float) -> str:
        """Détermine le statut de paiement"""
        if balance <= 0:
            return "Soldé"
        elif balance < total:
            return "Partiellement payé"
        else:
            return "Non payé"
