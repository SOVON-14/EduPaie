from repositories.student_repository import StudentRepository
from repositories.payment_repository import PaymentRepository
from services.dashboard_service import DashboardService
from pathlib import Path
import logging
from datetime import datetime
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from config import format_montant
from database.database import USER_DATA_DIR

logger = logging.getLogger(__name__)


class ReportService:
    """Service pour la génération de rapports PDF"""
    
    def __init__(self):
        self.student_repo = StudentRepository()
        self.payment_repo = PaymentRepository()
        self.dashboard_service = DashboardService()
        self.reports_dir = USER_DATA_DIR / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_dashboard_report(self, output_path: str = None) -> str:
        """Génère un rapport PDF du tableau de bord global.
        
        Args:
            output_path: Chemin de sortie du PDF (optionnel)
            
        Returns:
            Chemin du fichier PDF généré
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.reports_dir / f"rapport_tableau_bord_{timestamp}.pdf")
        
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
        ink = colors.HexColor("#173B36")
        accent = colors.HexColor("#287A5D")
        muted = colors.HexColor("#63736F")
        border = colors.HexColor("#D9E5DF")
        pale = colors.HexColor("#F1F6F3")
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, alignment=TA_CENTER, textColor=ink, spaceAfter=0.5*cm
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle", parent=styles["Normal"], fontName="Helvetica",
            fontSize=11, leading=14, alignment=TA_CENTER, textColor=muted, spaceAfter=1*cm
        )
        section_style = ParagraphStyle(
            "ReportSection", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=ink, spaceBefore=0.8*cm, spaceAfter=0.4*cm
        )
        label_style = ParagraphStyle(
            "ReportLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=9, leading=12, textColor=muted
        )
        value_style = ParagraphStyle(
            "ReportValue", parent=styles["Normal"], fontName="Helvetica",
            fontSize=10, leading=13, textColor=ink
        )
        
        story = []
        
        # Titre
        story.append(Paragraph("RAPPORT DU TABLEAU DE BORD", title_style))
        story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", subtitle_style))
        
        # Statistiques globales
        stats = self.dashboard_service.get_overview_stats()
        story.append(Paragraph("STATISTIQUES GLOBALES", section_style))
        
        stats_data = [
            ("Nombre total d'élèves", str(stats['nombre_total_eleves'])),
            ("Total encaissé", format_montant(stats['total_encaisse'])),
            ("Total restant dû", format_montant(stats['total_restant_du'])),
            ("Élèves soldés", str(stats['nombre_eleves_soldes'])),
            ("Élèves partiellement payés", str(stats['nombre_eleves_partiellement_payes'])),
            ("Élèves non payés", str(stats['nombre_eleves_non_payes']))
        ]
        
        stats_rows = [
            [Paragraph(escape(label), label_style), Paragraph(escape(value), value_style)]
            for label, value in stats_data
        ]
        
        stats_table = Table(stats_rows, colWidths=[10*cm, 7*cm])
        stats_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), pale),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(stats_table)
        
        # Statistiques par classe
        story.append(PageBreak())
        story.append(Paragraph("STATISTIQUES PAR CLASSE", section_style))
        
        class_stats = self.dashboard_service.get_class_stats()
        
        header_row = [
            Paragraph("Classe", label_style),
            Paragraph("Élèves", label_style),
            Paragraph("Encaissé", label_style),
            Paragraph("Restant", label_style),
            Paragraph("Soldés", label_style)
        ]
        
        class_rows = [header_row]
        for stat in class_stats:
            class_rows.append([
                Paragraph(escape(stat['classe']), value_style),
                Paragraph(str(stat['nombre_eleves']), value_style),
                Paragraph(format_montant(stat['total_encaisse']), value_style),
                Paragraph(format_montant(stat['total_restant']), value_style),
                Paragraph(str(stat['nombre_soldes']), value_style)
            ])
        
        class_table = Table(class_rows, colWidths=[3*cm, 2*cm, 3*cm, 3*cm, 2*cm])
        class_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ink),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(class_table)
        
        # Footer
        def draw_footer(canvas, document):
            canvas.saveState()
            canvas.setStrokeColor(border)
            canvas.setLineWidth(0.6)
            canvas.line(document.leftMargin, 1.55*cm, A4[0] - document.rightMargin, 1.55*cm)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(muted)
            canvas.drawString(document.leftMargin, 1.15*cm, "EduPaie | Rapport du tableau de bord")
            canvas.drawRightString(A4[0] - document.rightMargin, 1.15*cm, f"Document généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            canvas.restoreState()
        
        doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
        
        logger.info(f"Rapport du tableau de bord généré: {output_path}")
        return output_path
    
    def generate_students_report(self, classe: str = None, output_path: str = None) -> str:
        """Génère un rapport PDF de la liste des élèves.
        
        Args:
            classe: Filtre par classe (optionnel)
            output_path: Chemin de sortie du PDF (optionnel)
            
        Returns:
            Chemin du fichier PDF généré
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            class_suffix = f"_{classe}" if classe else ""
            output_path = str(self.reports_dir / f"rapport_eleves{class_suffix}_{timestamp}.pdf")
        
        # Récupérer les élèves
        if classe:
            students = self.student_repo.get_by_class_with_payments(classe)
        else:
            students = self.student_repo.get_all_with_payments()
        
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
        ink = colors.HexColor("#173B36")
        accent = colors.HexColor("#287A5D")
        muted = colors.HexColor("#63736F")
        border = colors.HexColor("#D9E5DF")
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, alignment=TA_CENTER, textColor=ink, spaceAfter=0.5*cm
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle", parent=styles["Normal"], fontName="Helvetica",
            fontSize=11, leading=14, alignment=TA_CENTER, textColor=muted, spaceAfter=1*cm
        )
        label_style = ParagraphStyle(
            "ReportLabel", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=11, textColor=muted
        )
        value_style = ParagraphStyle(
            "ReportValue", parent=styles["Normal"], fontName="Helvetica",
            fontSize=9, leading=12, textColor=ink
        )
        
        story = []
        
        # Titre
        title = f"LISTE DES ÉLÈVES - {classe}" if classe else "LISTE DE TOUS LES ÉLÈVES"
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | {len(students)} élève(s)", subtitle_style))
        
        # Tableau des élèves
        header_row = [
            Paragraph("ID", label_style),
            Paragraph("Nom", label_style),
            Paragraph("Prénom", label_style),
            Paragraph("Classe", label_style),
            Paragraph("Année", label_style),
            Paragraph("Total dû", label_style),
            Paragraph("Payé", label_style),
            Paragraph("Restant", label_style),
            Paragraph("Statut", label_style)
        ]
        
        student_rows = [header_row]
        for student in students:
            total_paye = student.get('total_paye', 0)
            montant_total = student['montant_total']
            restant = montant_total - total_paye
            statut = "Soldé" if restant <= 0 else "Partiellement payé" if total_paye > 0 else "Non payé"
            
            statut_color = colors.green if statut == "Soldé" else colors.orange if statut == "Partiellement payé" else colors.red
            
            statut_style = ParagraphStyle(
                "ReportStatus", parent=value_style, fontName="Helvetica-Bold",
                textColor=statut_color
            )
            
            student_rows.append([
                Paragraph(str(student['id']), value_style),
                Paragraph(escape(student['nom']), value_style),
                Paragraph(escape(student['prenom']), value_style),
                Paragraph(escape(student['classe']), value_style),
                Paragraph(escape(student['annee_scolaire']), value_style),
                Paragraph(format_montant(montant_total), value_style),
                Paragraph(format_montant(total_paye), value_style),
                Paragraph(format_montant(restant), value_style),
                Paragraph(statut, statut_style)
            ])
        
        student_table = Table(
            student_rows,
            colWidths=[0.8*cm, 2.5*cm, 2.5*cm, 2*cm, 1.5*cm, 2*cm, 2*cm, 2*cm, 2*cm]
        )
        student_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ink),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.6, border),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, border),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(student_table)
        
        # Footer
        def draw_footer(canvas, document):
            canvas.saveState()
            canvas.setStrokeColor(border)
            canvas.setLineWidth(0.6)
            canvas.line(document.leftMargin, 1.55*cm, A4[0] - document.rightMargin, 1.55*cm)
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(muted)
            canvas.drawString(document.leftMargin, 1.15*cm, "EduPaie | Rapport des élèves")
            canvas.drawRightString(A4[0] - document.rightMargin, 1.15*cm, f"Document généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            canvas.restoreState()
        
        doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
        
        logger.info(f"Rapport des élèves généré: {output_path}")
        return output_path
