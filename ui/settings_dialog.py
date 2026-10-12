from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                                     QPushButton, QFileDialog, QMessageBox, QGroupBox, QFormLayout)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt
from services.settings_service import SettingsService
from pathlib import Path


class SettingsDialog(QDialog):
    """Boîte de dialogue pour la gestion des paramètres de l'établissement"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_service = SettingsService()
        self.signature_path = None
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Paramètres de l'établissement")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Informations de l'établissement
        etablissement_group = QGroupBox("Informations de l'établissement")
        etablissement_layout = QFormLayout()
        
        self.etablissement_nom_input = QLineEdit()
        self.etablissement_nom_input.setPlaceholderText("Nom de l'établissement")
        etablissement_layout.addRow("Nom de l'établissement:", self.etablissement_nom_input)
        
        self.directeur_nom_input = QLineEdit()
        self.directeur_nom_input.setPlaceholderText("Nom du directeur")
        etablissement_layout.addRow("Nom du directeur:", self.directeur_nom_input)
        
        etablissement_group.setLayout(etablissement_layout)
        layout.addWidget(etablissement_group)
        
        # Signature du directeur
        signature_group = QGroupBox("Signature du directeur")
        signature_layout = QVBoxLayout()
        
        # Aperçu de la signature
        self.signature_preview = QLabel("Aucune signature sélectionnée")
        self.signature_preview.setAlignment(Qt.AlignCenter)
        self.signature_preview.setMinimumHeight(100)
        self.signature_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5;")
        signature_layout.addWidget(self.signature_preview)
        
        # Boutons pour la signature
        signature_buttons = QHBoxLayout()
        
        self.upload_signature_btn = QPushButton("Importer une signature")
        self.upload_signature_btn.clicked.connect(self.upload_signature)
        signature_buttons.addWidget(self.upload_signature_btn)
        
        self.export_svg_btn = QPushButton("Exporter en SVG")
        self.export_svg_btn.clicked.connect(self.export_signature_svg)
        self.export_svg_btn.setEnabled(False)
        signature_buttons.addWidget(self.export_svg_btn)
        
        self.clear_signature_btn = QPushButton("Supprimer")
        self.clear_signature_btn.clicked.connect(self.clear_signature)
        self.clear_signature_btn.setEnabled(False)
        signature_buttons.addWidget(self.clear_signature_btn)
        
        signature_layout.addLayout(signature_buttons)
        signature_group.setLayout(signature_layout)
        layout.addWidget(signature_group)
        
        # Boutons de validation
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Charge les paramètres actuels"""
        self.etablissement_nom_input.setText(self.settings_service.get_etablissement_nom())
        self.directeur_nom_input.setText(self.settings_service.get_directeur_nom())
        
        signature_path = self.settings_service.get_signature_path()
        if signature_path and Path(signature_path).exists():
            self.signature_path = signature_path
            self.load_signature_preview(signature_path)
            self.export_svg_btn.setEnabled(True)
            self.clear_signature_btn.setEnabled(True)
    
    def load_signature_preview(self, image_path: str):
        """Charge l'aperçu de la signature"""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Redimensionner pour l'aperçu
            scaled_pixmap = pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.signature_preview.setPixmap(scaled_pixmap)
            self.signature_preview.setText("")
        else:
            self.signature_preview.setText("Impossible de charger l'image")
    
    def upload_signature(self):
        """Importe une image de signature"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une image de signature",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            try:
                # Sauvegarder l'image
                saved_path = self.settings_service.save_signature_image(file_path)
                self.signature_path = saved_path
                self.load_signature_preview(saved_path)
                self.export_svg_btn.setEnabled(True)
                self.clear_signature_btn.setEnabled(True)
                QMessageBox.information(self, "Succès", "Signature importée avec succès")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import: {str(e)}")
    
    def export_signature_svg(self):
        """Exporte la signature en format SVG"""
        if not self.signature_path:
            QMessageBox.warning(self, "Avertissement", "Aucune signature à exporter")
            return
        
        try:
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer la signature SVG",
                f"{Path(self.signature_path).stem}.svg",
                "Fichiers SVG (*.svg)"
            )
            
            if output_path:
                svg_path = self.settings_service.convert_signature_to_svg(
                    image_path=self.signature_path,
                    output_path=output_path
                )
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Signature exportée en SVG:\n{svg_path}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def clear_signature(self):
        """Supprime la signature"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir supprimer la signature ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.signature_path = None
            self.settings_service.set_signature_path("")
            self.signature_preview.clear()
            self.signature_preview.setText("Aucune signature sélectionnée")
            self.signature_preview.setPixmap(QPixmap())
            self.export_svg_btn.setEnabled(False)
            self.clear_signature_btn.setEnabled(False)
    
    def save_settings(self):
        """Enregistre les paramètres"""
        etablissement_nom = self.etablissement_nom_input.text().strip()
        directeur_nom = self.directeur_nom_input.text().strip()
        
        if not etablissement_nom:
            QMessageBox.warning(self, "Avertissement", "Le nom de l'établissement est obligatoire")
            return
        
        try:
            self.settings_service.set_etablissement_nom(etablissement_nom)
            self.settings_service.set_directeur_nom(directeur_nom)
            
            if self.signature_path:
                self.settings_service.set_signature_path(self.signature_path)
            
            QMessageBox.information(self, "Succès", "Paramètres enregistrés avec succès")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
