from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                     QDoubleSpinBox, QComboBox, QPushButton, QFormLayout)
from PySide6.QtCore import Qt
from config import MONTANT_MAX, FORMAT_MONTANT_SUFFIX, format_montant

class PaymentDialog(QDialog):
    """Boîte de dialogue pour enregistrer un paiement"""
    
    def __init__(self, parent, student_id, student_service, payment_service, receipt_service=None):
        super().__init__(parent)
        self.student_id = student_id
        self.student_service = student_service
        self.payment_service = payment_service
        self.receipt_service = receipt_service
        self.init_ui()
        self.load_student_info()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Informations de l'élève
        self.student_info_label = QLabel()
        self.student_info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.student_info_label)
        
        # Solde actuel
        self.balance_label = QLabel()
        self.balance_label.setStyleSheet("color: blue; font-size: 11px;")
        layout.addWidget(self.balance_label)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.montant_input = QDoubleSpinBox()
        # Plafond aligné sur le montant total possible (corrige IMP-03)
        self.montant_input.setRange(0.01, MONTANT_MAX)
        self.montant_input.setDecimals(0)
        self.montant_input.setSuffix(FORMAT_MONTANT_SUFFIX)
        self.montant_input.setFocus()
        # Ne pas ajuster le maximum ici, sera ajusté dynamiquement dans load_student_info
        form_layout.addRow("Montant *:", self.montant_input)
        
        self.mode_input = QComboBox()
        self.mode_input.addItem("Espèces", "especes")
        self.mode_input.addItem("Chèque", "cheque")
        self.mode_input.addItem("Virement", "virement")
        self.mode_input.addItem("Mobile Money", "mobile_money")
        form_layout.addRow("Mode de paiement *:", self.mode_input)
        
        layout.addLayout(form_layout)
        
        # Avertissement
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red; font-size: 10px;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("Enregistrer")
        self.ok_btn.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Connecter le changement de montant pour la validation
        self.montant_input.valueChanged.connect(self.validate_amount)
    
    def load_student_info(self):
        """Charge les informations de l'élève"""
        student = self.student_service.get_student(self.student_id)
        if student:
            self.student_info_label.setText(
                f"Élève: {student['nom']} {student['prenom']} - {student['classe']}"
            )
            self.balance_label.setText(
                f"Solde restant: {format_montant(student['solde'])} / {format_montant(student['montant_total'])}"
            )
            self.max_amount = student['solde']
            # Ajuster dynamiquement le maximum du spinbox au solde restant
            self.montant_input.setMaximum(self.max_amount)
        else:
            # Élève introuvable : fermer le dialogue avec un message d'erreur
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Élève introuvable. Il a peut-être été supprimé.")
            self.reject()
    
    def validate_amount(self):
        """Valide le montant saisi"""
        montant = self.montant_input.value()
        
        if montant > self.max_amount:
            self.warning_label.setText(
                f"Attention: Le montant ({format_montant(montant)}) dépasse le solde restant ({format_montant(self.max_amount)})"
            )
            self.ok_btn.setEnabled(False)
        else:
            self.warning_label.clear()
            self.ok_btn.setEnabled(True)
    
    def validate_and_accept(self):
        """Valide le formulaire et accepte"""
        montant = self.montant_input.value()
        mode = self.mode_input.currentData()
        
        if montant <= 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", "Le montant doit être positif")
            return
        
        if montant > self.max_amount:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Erreur", 
                f"Le montant ({format_montant(montant)}) dépasse le solde restant ({format_montant(self.max_amount)})"
            )
            return
        
        try:
            result = self.payment_service.create_payment(self.student_id, montant, mode)
            
            # Demander si l'utilisateur veut générer le reçu
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Reçu",
                "Paiement enregistré avec succès. Voulez-vous générer le reçu PDF ?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    if self.receipt_service:
                        pdf_path = self.receipt_service.generate_pdf_receipt(
                            result['payment']['numero_recu']
                        )
                        QMessageBox.information(
                            self,
                            "Reçu généré",
                            f"Reçu généré: {pdf_path}"
                        )
                    else:
                        QMessageBox.warning(self, "Erreur", "Service de reçu non disponible")
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Erreur lors de la génération du reçu: {str(e)}")
            
            self.accept()
            
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", str(e))
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
