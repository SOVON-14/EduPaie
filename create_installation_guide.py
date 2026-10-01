from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_installation_guide():
    """Crée un guide d'installation pour l'exécutable EduPaie"""
    doc = Document()
    
    # Titre
    title = doc.add_heading('GUIDE D\'INSTALLATION - EDU PAIE', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    # Introduction
    doc.add_heading('1. INTRODUCTION', level=1)
    doc.add_paragraph(
        'Ce guide explique comment installer et utiliser l\'application EduPaie '
        'sur un ordinateur Windows sans Python préinstallé.'
    )
    
    # Fichiers nécessaires
    doc.add_heading('2. FICHIERS NÉCESSAIRES', level=1)
    doc.add_paragraph('Pour utiliser EduPaie, vous avez besoin des fichiers suivants :')
    
    table = doc.add_table(rows=3, cols=2)
    table.style = 'Table Grid'
    
    table.rows[0].cells[0].text = 'Fichier'
    table.rows[0].cells[1].text = 'Description'
    for cell in table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    table.rows[1].cells[0].text = 'EduPaie.exe'
    table.rows[1].cells[1].text = 'L\'exécutable principal de l\'application'
    
    table.rows[2].cells[0].text = 'edupaie.db'
    table.rows[2].cells[1].text = 'La base de données (créée automatiquement au premier lancement)'
    
    doc.add_paragraph()
    
    # Installation
    doc.add_heading('3. INSTALLATION', level=1)
    
    doc.add_heading('3.1. Où placer les fichiers', level=2)
    doc.add_paragraph('Il est recommandé de créer un dossier dédié pour EduPaie, par exemple :')
    doc.add_paragraph('C:\\Program Files\\EduPaie\\')
    doc.add_paragraph('ou')
    doc.add_paragraph('C:\\EduPaie\\')
    doc.add_paragraph()
    doc.add_paragraph('Placez les fichiers comme suit :')
    doc.add_paragraph('• EduPaie.exe : dans le dossier principal')
    doc.add_paragraph('• Le dossier data (avec edupaie.db) sera créé automatiquement')
    
    doc.add_heading('3.2. Premier lancement', level=2)
    doc.add_paragraph('Au premier lancement :')
    doc.add_paragraph('1. Double-cliquez sur EduPaie.exe')
    doc.add_paragraph('2. L\'application se lancera et créera automatiquement la base de données')
    doc.add_paragraph('3. L\'interface principale apparaîtra')
    
    doc.add_heading('3.3. Pare-feu Windows', level=2)
    doc.add_paragraph('Si Windows Defender ou un autre antivirus bloque l\'exécutable :')
    doc.add_paragraph('1. Cliquez sur "Plus d\'informations"')
    doc.add_paragraph('2. Sélectionnez "Autoriser sur l\'appareil"')
    doc.add_paragraph('3. Confirmez l\'action')
    
    # Utilisation
    doc.add_heading('4. UTILISATION', level=1)
    doc.add_paragraph('Pour utiliser l\'application, reportez-vous au Manuel_Utilisateur_EduPaie.docx')
    doc.add_paragraph('qui explique en détail :')
    doc.add_paragraph('• Comment enregistrer un élève')
    doc.add_paragraph('• Comment enregistrer un paiement')
    doc.add_paragraph('• Comment imprimer un reçu')
    doc.add_paragraph('• Comment utiliser le tableau de bord')
    
    # Dossiers créés automatiquement
    doc.add_heading('5. DOSSIERS CRÉÉS AUTOMATIQUEMENT', level=1)
    doc.add_paragraph('L\'application créera automatiquement les dossiers suivants :')
    doc.add_paragraph('• data/ : Contient la base de données edupaie.db')
    doc.add_paragraph('• receipts/ : Contient les reçus PDF générés')
    doc.add_paragraph('• Il est recommandé de ne pas déplacer ces dossiers')
    
    # Sauvegarde
    doc.add_heading('6. SAUVEGARDE', level=1)
    doc.add_paragraph('Pour sauvegarder vos données :')
    doc.add_paragraph('1. Copiez régulièrement le dossier data/')
    doc.add_paragraph('2. Copiez également le dossier receipts/ pour les reçus')
    doc.add_paragraph('3. Stockez les copies sur un disque externe ou le cloud')
    
    # Désinstallation
    doc.add_heading('7. DÉSINSTALLATION', level=1)
    doc.add_paragraph('Pour désinstaller l\'application :')
    doc.add_paragraph('1. Supprimez le dossier EduPaie')
    doc.add_paragraph('2. Videz la corbeille')
    
    # Support
    doc.add_heading('8. SUPPORT', level=1)
    doc.add_paragraph('En cas de problème :')
    doc.add_paragraph('• Vérifiez que Windows est à jour')
    doc.add_paragraph('• Assurez-vous d\'avoir les droits administrateur')
    doc.add_paragraph('• Vérifiez que votre antivirus n\' bloque pas l\'application')
    
    doc.add_paragraph()
    doc.add_paragraph()
    footer = doc.add_paragraph('© 2024 - EduPaie - Système de Gestion des Frais de Scolarité')
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].italic = True
    
    # Sauvegarder
    doc.save('Guide_Installation_EduPaie.docx')
    print('Guide d\'installation créé avec succès : Guide_Installation_EduPaie.docx')

if __name__ == '__main__':
    create_installation_guide()
