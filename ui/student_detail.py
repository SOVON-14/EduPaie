from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                     QTableWidget, QTableWidgetItem, QPushButton, 
                                     QHeaderView, QMessageBox, QTabWidget, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.payment_dialog import PaymentDialog
from config import format_montant

class StudentDetailDialog(QDialog):
    """Boîte de dialogue pour afficher les détails d'un élève"""
    
    def __init__(self, student_id, student_service, payment_service, receipt_service, parent=None):
        super().__init__(parent)
        self.student_id = student_id
        self.student_service = student_service
        self.payment_service = payment_service
        self.receipt_service = receipt_service
        self.init_ui()
        self.load_student_data()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Détails de l'élève")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Informations de l'élève
        self.student_info_label = QLabel()
        self.student_info_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.student_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.student_info_label)
        
        # Statistiques de paiement
        self.payment_stats_label = QLabel()
        self.payment_stats_label.setStyleSheet("color: blue; font-size: 11px;")
        self.payment_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.payment_stats_label)
        
        # Onglets
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Onglet Historique des paiements
        self.payments_tab = self.create_payments_tab()
        self.tabs.addTab(self.payments_tab, "Historique des paiements")
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        
        self.add_payment_btn = QPushButton("Enregistrer un paiement")
        self.add_payment_btn.clicked.connect(self.add_payment)
        button_layout.addWidget(self.add_payment_btn)
        
        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def create_payments_tab(self):
        """Crée l'onglet historique des paiements"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Table des paiements
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels([
            "Numéro de reçu", "Date", "Montant", "Mode", "Solde après", "Statut"
        ])
        self.payments_table.horizontalHeader().setStretchLastSection(True)
        self.payments_table.setSelectionBehavior(QTableWidget.SelectRows)
        # Correction IMP-02 de l'audit : cellules non éditables
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.payments_table)
        
        # Boutons pour les reçus
        receipt_buttons = QHBoxLayout()
        
        self.view_receipt_btn = QPushButton("Voir le reçu")
        self.view_receipt_btn.clicked.connect(self.view_receipt)
        receipt_buttons.addWidget(self.view_receipt_btn)
        
        self.print_receipt_btn = QPushButton("Imprimer le reçu")
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        receipt_buttons.addWidget(self.print_receipt_btn)
        
        layout.addLayout(receipt_buttons)
        
        return tab
    
    def load_student_data(self):
        """Charge les données de l'élève"""
        student = self.student_service.get_student(self.student_id)
        if not student:
            QMessageBox.warning(self, "Erreur", "Élève introuvable")
            self.reject()
            return
        
        # Afficher les informations de l'élève
        self.student_info_label.setText(
            f"{student['nom']} {student['prenom']} - {student['classe']} ({student['annee_scolaire']})"
        )
        
        # Afficher les statistiques de paiement
        self.payment_stats_label.setText(
            f"Total dû: {format_montant(student['montant_total'])} | "
            f"Total payé: {format_montant(student['total_paye'])} | "
            f"Solde: {format_montant(student['solde'])} | "
            f"Statut: {student['statut']}"
        )
        
        # Charger l'historique des paiements
        payments = self.payment_service.get_student_payments(self.student_id)
        
        self.payments_table.setRowCount(len(payments))
        
        for row, payment in enumerate(payments):
            self.payments_table.setItem(row, 0, QTableWidgetItem(payment['numero_recu']))
            self.payments_table.setItem(row, 1, QTableWidgetItem(payment['date']))
            self.payments_table.setItem(row, 2, QTableWidgetItem(format_montant(payment['montant'])))
            self.payments_table.setItem(row, 3, QTableWidgetItem(payment['mode_paiement']))
            self.payments_table.setItem(row, 4, QTableWidgetItem(format_montant(payment['solde_apres_paiement'])))
            self.payments_table.setItem(row, 5, QTableWidgetItem(payment['statut']))
    
    def add_payment(self):
        """Enregistre un nouveau paiement"""
        dialog = PaymentDialog(self, self.student_id, self.student_service, self.payment_service, self.receipt_service)
        if dialog.exec():
            QMessageBox.information(self, "Succès", "Paiement enregistré avec succès")
            self.load_student_data()
    
    def view_receipt(self):
        """Affiche le reçu du paiement sélectionné"""
        selected_rows = self.payments_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un paiement")
            return
        
        row = self.payments_table.currentRow()
        receipt_number = self.payments_table.item(row, 0).text()
        
        try:
            receipt = self.receipt_service.get_receipt_by_number(receipt_number)
            if receipt:
                receipt_info = (
                    f"Numéro: {receipt['numero_recu']}\n"
                    f"Date: {receipt['date_paiement']}\n"
                    f"Montant: {format_montant(receipt['montant_paye'])}\n"
                    f"Mode: {receipt['mode_paiement']}\n"
                    f"Élève: {receipt['eleve']['nom']} {receipt['eleve']['prenom']}\n"
                    f"Classe: {receipt['eleve']['classe']}\n"
                    f"Solde après: {format_montant(receipt['solde_apres_paiement'])}\n"
                    f"Statut: {receipt['statut']}"
                )
                QMessageBox.information(self, "Reçu", receipt_info)
            else:
                QMessageBox.warning(self, "Erreur", "Reçu introuvable")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la récupération du reçu: {str(e)}")
    
    def print_receipt(self):
        """Imprime le reçu du paiement sélectionné"""
        selected_rows = self.payments_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un paiement")
            return
        
        row = self.payments_table.currentRow()
        receipt_number = self.payments_table.item(row, 0).text()
        
        try:
            # Générer le PDF
            pdf_path = self.receipt_service.generate_pdf_receipt(receipt_number)
            
            # Demander si l'utilisateur veut ouvrir le fichier
            reply = QMessageBox.question(
                self,
                "Reçu généré",
                f"Reçu généré: {pdf_path}\nVoulez-vous ouvrir le fichier ?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import os
                import platform
                import subprocess
                
                if platform.system() == 'Windows':
                    os.startfile(pdf_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', pdf_path])
                else:  # Linux
                    subprocess.run(['xdg-open', pdf_path])
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du reçu: {str(e)}")
