from repositories.payment_repository import PaymentRepository
from repositories.student_repository import StudentRepository
from typing import Optional, Dict, Any
from pathlib import Path
import os
import subprocess
import platform
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config import calculate_payment_status, format_montant
from database.database import USER_DATA_DIR

class ReceiptService:
    """Service pour la gestion des reçus de paiement et génération PDF"""
    
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.student_repo = StudentRepository()
        self.receipts_dir = USER_DATA_DIR / "receipts"
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        ink = colors.HexColor("#173B36")
        accent = colors.HexColor("#287A5D")
        muted = colors.HexColor("#63736F")
        border = colors.HexColor("#D9E5DF")
        pale = colors.HexColor("#F1F6F3")
        styles = getSampleStyleSheet()
        brand_style = ParagraphStyle(
            "ReceiptBrand", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=17, leading=20, textColor=colors.white,
        )
        brand_detail_style = ParagraphStyle(
            "ReceiptBrandDetail", parent=styles["Normal"], fontName="Helvetica",
            fontSize=8, leading=11, textColor=colors.HexColor("#D8E8E0"),
        )
        receipt_title_style = ParagraphStyle(
            "ReceiptTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, alignment=TA_RIGHT, textColor=colors.white,
        )
        section_style = ParagraphStyle(
            "ReceiptSection", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=9, leading=12, textColor=ink, spaceBefore=5, spaceAfter=7,
        )
        label_style = ParagraphStyle(
            "ReceiptLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=11, textColor=muted,
        )
        value_style = ParagraphStyle(
            "ReceiptValue", parent=styles["Normal"], fontName="Helvetica",
            fontSize=10, leading=14, textColor=ink,
        )
        meta_style = ParagraphStyle(
            "ReceiptMeta", parent=styles["Normal"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=muted,
        )
        amount_label_style = ParagraphStyle(
            "ReceiptAmountLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=11, textColor=accent,
        )
        amount_style = ParagraphStyle(
            "ReceiptAmount", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=20, leading=24, alignment=TA_RIGHT, textColor=ink,
        )
        thanks_style = ParagraphStyle(
            "ReceiptThanks", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=10, leading=14, alignment=TA_CENTER, textColor=ink,
        )
        note_style = ParagraphStyle(
            "ReceiptNote", parent=styles["Normal"], fontName="Helvetica",
            fontSize=8, leading=11, alignment=TA_CENTER, textColor=muted,
        )

        story = []
        brand_table = Table(
            [[
                Paragraph("EDUPAIE<br/><font size='8'>GESTION SCOLAIRE</font>", brand_style),
                Paragraph("REÇU DE<br/>PAIEMENT", receipt_title_style),
            ]],
            colWidths=[9.5*cm, 7.5*cm],
            rowHeights=[2.2*cm],
        )
        brand_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ink),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 14),
            ("RIGHTPADDING", (1, 0), (1, 0), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.extend([brand_table, Spacer(1, 0.45*cm)])

        receipt_meta = Table(
            [[
                Paragraph(
                    f"<b>N° DE REÇU</b><br/>{escape(str(receipt['numero_recu']))}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>DATE DU PAIEMENT</b><br/>{escape(str(receipt['date_paiement']))}",
                    meta_style,
                ),
            ]],
            colWidths=[9.5*cm, 7.5*cm],
        )
        receipt_meta.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), pale),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        story.extend([receipt_meta, Spacer(1, 0.55*cm)])

        amount_box = Table(
            [[
                Paragraph("MONTANT REÇU", amount_label_style),
                Paragraph(escape(format_montant(receipt["montant_paye"])), amount_style),
            ]],
            colWidths=[8*cm, 9*cm],
        )
        amount_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF4EE")),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.extend([amount_box, Spacer(1, 0.55*cm)])

        story.append(Paragraph("INFORMATIONS DE L'ÉLÈVE", section_style))
        student = receipt["eleve"]
        student_rows = [
            [
                Paragraph("NOM", label_style),
                Paragraph(escape(str(student["nom"])), value_style),
                Paragraph("PRÉNOM", label_style),
                Paragraph(escape(str(student["prenom"])), value_style),
            ],
            [
                Paragraph("CLASSE", label_style),
                Paragraph(escape(str(student["classe"])), value_style),
                Paragraph("ANNÉE SCOLAIRE", label_style),
                Paragraph(escape(str(student["annee_scolaire"])), value_style),
            ],
        ]
        student_table = Table(
            student_rows,
            colWidths=[2.4*cm, 5.6*cm, 3.0*cm, 6.0*cm],
        )
        student_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), pale),
            ("BACKGROUND", (2, 0), (2, -1), pale),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.extend([student_table, Spacer(1, 0.5*cm)])

        story.append(Paragraph("DÉTAILS DU RÈGLEMENT", section_style))
        status_style = ParagraphStyle(
            "ReceiptStatus", parent=value_style, fontName="Helvetica-Bold",
            textColor=self._get_status_color(receipt["statut"]),
        )
        payment_rows = [
            ("MODE DE PAIEMENT", self._format_payment_mode(receipt["mode_paiement"])),
            ("MONTANT TOTAL DÛ", format_montant(receipt["montant_total"])),
            ("SOLDE APRÈS PAIEMENT", format_montant(receipt["solde_apres_paiement"])),
            ("STATUT", receipt["statut"]),
        ]
        payment_table = Table(
            [[Paragraph(escape(label), label_style),
              Paragraph(escape(str(value)), status_style if label == "STATUT" else value_style)]
             for label, value in payment_rows],
            colWidths=[8.5*cm, 8.5*cm],
        )
        payment_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, border),
            ("BACKGROUND", (0, 3), (-1, 3), pale),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.extend([
            payment_table,
            Spacer(1, 0.75*cm),
            Paragraph("Merci pour votre paiement.", thanks_style),
            Spacer(1, 0.1*cm),
            Paragraph("Conservez ce reçu comme justificatif de règlement.", note_style),
        ])

        def draw_footer(canvas, document):
            canvas.saveState()
            canvas.setStrokeColor(border)
            canvas.setLineWidth(0.6)
            canvas.line(document.leftMargin, 1.55*cm, A4[0] - document.rightMargin, 1.55*cm)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(muted)
            canvas.drawString(document.leftMargin, 1.15*cm, "EduPaie | Reçu de paiement")
            canvas.drawRightString(A4[0] - document.rightMargin, 1.15*cm, "Document généré par EduPaie")
            canvas.restoreState()

        doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
        
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
