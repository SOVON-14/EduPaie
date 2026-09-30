from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                     QLineEdit, QDoubleSpinBox, QPushButton, QFormLayout, QComboBox)
from PySide6.QtCore import Qt
from config import MONTANT_MAX, FORMAT_MONTANT_SUFFIX
import re

class StudentDialog(QDialog):
    """Boîte de dialogue pour ajouter ou modifier un élève"""
    
    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.student_data = student_data
        self.init_ui()
        
        if student_data:
            self.set_student_data(student_data)
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Élève")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom de l'élève")
        form_layout.addRow("Nom *:", self.nom_input)
        
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom de l'élève")
        form_layout.addRow("Prénom *:", self.prenom_input)
        
        self.classe_input = QComboBox()
        self.classe_input.setEditable(True)
        self.classe_input.addItems([
            "6ème A", "6ème B", "6ème C",
            "5ème A", "5ème B", "5ème C",
            "4ème A", "4ème B", "4ème C",
            "3ème A", "3ème B", "3ème C",
            "2nde A", "2nde B", "2nde C",
            "1ère A", "1ère B", "1ère C",
            "Terminale A", "Terminale B", "Terminale C"
        ])
        form_layout.addRow("Classe *:", self.classe_input)
        
        self.annee_input = QLineEdit()
        self.annee_input.setPlaceholderText("Ex: 2024-2025")
        form_layout.addRow("Année scolaire *:", self.annee_input)
        
        self.montant_input = QDoubleSpinBox()
        self.montant_input.setRange(0, MONTANT_MAX)
        self.montant_input.setDecimals(0)
        self.montant_input.setSuffix(FORMAT_MONTANT_SUFFIX)
        form_layout.addRow("Montant total *:", self.montant_input)
        
        layout.addLayout(form_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def set_student_data(self, student_data):
        """Remplit le formulaire avec les données de l'élève"""
        self.nom_input.setText(student_data['nom'])
        self.prenom_input.setText(student_data['prenom'])
        
        # Pour la classe, chercher dans la liste ou ajouter comme texte personnalisé
        index = self.classe_input.findText(student_data['classe'])
        if index >= 0:
            self.classe_input.setCurrentIndex(index)
        else:
            self.classe_input.setEditText(student_data['classe'])
        
        self.annee_input.setText(student_data['annee_scolaire'])
        self.montant_input.setValue(student_data['montant_total'])
    
    def get_student_data(self):
        """Récupère les données du formulaire"""
        return {
            'nom': self.nom_input.text(),
            'prenom': self.prenom_input.text(),
            'classe': self.classe_input.currentText(),
            'annee_scolaire': self.annee_input.text(),
            'montant_total': self.montant_input.value()
        }
    
    def validate_and_accept(self):
        """Valide le formulaire et accepte"""
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        classe = self.classe_input.currentText().strip()
        annee = self.annee_input.text().strip()
        montant = self.montant_input.value()
        
        if not nom:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire")
            return
        
        if not prenom:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Le prénom est obligatoire")
            return
        
        if not classe:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "La classe est obligatoire")
            return
        
        if not annee:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "L'année scolaire est obligatoire")
            return
        
        # Validation du format de l'année scolaire (ex: 2024-2025)
        if not re.match(r'^\d{4}-\d{4}$', annee):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "L'année scolaire doit être au format YYYY-YYYY (ex: 2024-2025)")
            return
        
        if montant <= 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Le montant doit être positif")
            return
        
        self.accept()
