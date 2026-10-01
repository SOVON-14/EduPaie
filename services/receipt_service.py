from repositories.payment_repository import PaymentRepository
from repositories.student_repository import StudentRepository
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import os
import subprocess
import platform
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config import format_montant
from config import format_montant, calculate_payment_status

class ReceiptService:
    """Service pour la gestion des reçus de paiement et génération PDF"""
    
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.student_repo = StudentRepository()
        self.receipts_dir = Path(__file__).parent.parent / "receipts"
        self.receipts_dir.mkdir(exist_ok=True)
    
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
            'statut': calculate_payment_status(solde_apres, student['montant_total'])
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
    
    def generate_pdf_receipt(self, numero_recu: str, output_path: Optional[str] = None) -> str:
        """
        Génère un reçu au format PDF
        
        Args:
            numero_recu: Numéro unique du reçu
            output_path: Chemin de sortie du PDF (optionnel)
            
        Returns:
            Chemin du fichier PDF généré
        """
        receipt = self.get_receipt_by_number(numero_recu)
        if not receipt:
            raise ValueError(f"Reçu {numero_recu} introuvable")
        
        # Définir le chemin de sortie
        if output_path is None:
            output_path = str(self.receipts_dir / f"{numero_recu}.pdf")
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=10
        )
        normal_style = styles['Normal']
        normal_style.fontSize = 11
        
        # Contenu du document
        story = []
        
        # Titre
        story.append(Paragraph("REÇU DE PAIEMENT", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Numéro de reçu et date
        story.append(Paragraph(f"<b>Numéro de reçu :</b> {receipt['numero_recu']}", normal_style))
        story.append(Paragraph(f"<b>Date :</b> {receipt['date_paiement']}", normal_style))
        story.append(Spacer(1, 1*cm))
        
        # Informations de l'élève
        story.append(Paragraph("INFORMATIONS DE L'ÉLÈVE", header_style))
        
        student_data = [
            ['Nom :', receipt['eleve']['nom']],
            ['Prénom :', receipt['eleve']['prenom']],
            ['Classe :', receipt['eleve']['classe']],
            ['Année scolaire :', receipt['eleve']['annee_scolaire']]
        ]
        
        student_table = Table(student_data, colWidths=[4*cm, 6*cm])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
        ]))
        story.append(student_table)
        story.append(Spacer(1, 1*cm))
        
        # Détails du paiement
        story.append(Paragraph("DÉTAILS DU PAIEMENT", header_style))
        
        payment_data = [
            ['Montant payé :', format_montant(receipt['montant_paye'])],
            ['Mode de paiement :', self._format_payment_mode(receipt['mode_paiement'])],
            ['Montant total dû :', format_montant(receipt['montant_total'])],
            ['Solde restant :', format_montant(receipt['solde_apres_paiement'])],
            ['Statut :', receipt['statut']]
        ]
        
        payment_table = Table(payment_data, colWidths=[4*cm, 6*cm])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (1, 4), (1, 4), self._get_status_color(receipt['statut'])),
            ('FONTNAME', (1, 4), (1, 4), 'Helvetica-Bold')
        ]))
        story.append(payment_table)
        story.append(Spacer(1, 2*cm))
        
        # Footer
        story.append(Paragraph("Merci pour votre paiement.", normal_style))
        story.append(Paragraph("Ce document sert de preuve de paiement.", normal_style))
        
        # Générer le PDF
        doc.build(story)
        
        return output_path
    
    def print_receipt(self, numero_recu: str) -> bool:
        """
        Imprime directement un reçu
        
        Args:
            numero_recu: Numéro unique du reçu
            
        Returns:
            True si l'impression a réussi, False sinon
        """
        try:
            # Générer le PDF
            pdf_path = self.generate_pdf_receipt(numero_recu)
            
            # Ouvrir le PDF avec le visionneur par défaut (qui permet l'impression)
            if platform.system() == 'Windows':
                os.startfile(pdf_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path])
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path])
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'impression: {e}")
            return False
    
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
        """Détermine le statut de paiement."""
        return calculate_payment_status(balance, total)
    
    def _format_payment_mode(self, mode: str) -> str:
        """Formate le mode de paiement pour l'affichage"""
        modes = {
            'especes': 'Espèces',
            'cheque': 'Chèque',
            'virement': 'Virement bancaire',
            'mobile_money': 'Mobile Money'
        }
        return modes.get(mode, mode)
    
    def _get_status_color(self, status: str) -> colors.Color:
        """Retourne la couleur selon le statut"""
        if status == "Soldé":
            return colors.green
        elif status == "Partiellement payé":
            return colors.orange
        else:
            return colors.red
