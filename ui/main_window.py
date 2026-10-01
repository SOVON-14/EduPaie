from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                     QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                                     QTabWidget, QLineEdit, QComboBox, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from services.student_service import StudentService
from services.payment_service import PaymentService
from services.dashboard_service import DashboardService
from services.receipt_service import ReceiptService
from config import format_montant
from ui.student_dialog import StudentDialog
from ui.payment_dialog import PaymentDialog
from ui.student_detail import StudentDetailDialog

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application EduPaie"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduPaie - Gestion des frais de scolarité")
        self.setGeometry(100, 100, 1200, 800)
        
        # Services
        self.student_service = StudentService()
        self.payment_service = PaymentService()
        self.dashboard_service = DashboardService()
        self.receipt_service = ReceiptService()
        
        # Initialiser l'interface
        self.init_ui()
        self.load_dashboard_stats()
        # Charger la liste des élèves au démarrage (correction IMP-01 de l'audit :
        # la table des élèves restait vide à l'ouverture de l'application)
        self.load_students()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Titre
        title_label = QLabel("EduPaie - Gestion des frais de scolarité")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Onglets
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Onglet Tableau de bord
        self.dashboard_tab = self.create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "Tableau de bord")
        
        # Onglet Élèves
        self.students_tab = self.create_students_tab()
        self.tabs.addTab(self.students_tab, "Élèves")
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        
        self.add_student_btn = QPushButton("Ajouter un élève")
        self.add_student_btn.clicked.connect(self.add_student)
        button_layout.addWidget(self.add_student_btn)
        
        self.refresh_btn = QPushButton("Actualiser")
        self.refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_dashboard_tab(self):
        """Crée l'onglet tableau de bord"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Statistiques globales
        stats_label = QLabel("Statistiques globales")
        stats_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(stats_label)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Métrique", "Valeur"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stats_table.setMaximumHeight(200)
        layout.addWidget(self.stats_table)
        
        # Statistiques par classe
        class_label = QLabel("Statistiques par classe")
        class_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(class_label)
        
        self.class_table = QTableWidget()
        self.class_table.setColumnCount(5)
        self.class_table.setHorizontalHeaderLabels(["Classe", "Élèves", "Encaissé", "Restant", "Soldés"])
        self.class_table.horizontalHeader().setStretchLastSection(True)
        self.class_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.class_table)
        
        return tab
    
    def create_students_tab(self):
        """Crée l'onglet élèves"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtres
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Recherche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou prénom...")
        self.search_input.textChanged.connect(self.filter_students)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addWidget(QLabel("Classe:"))
        self.class_filter = QComboBox()
        self.class_filter.addItem("Toutes les classes")
        self.class_filter.currentTextChanged.connect(self.filter_students)
        filter_layout.addWidget(self.class_filter)
        
        filter_layout.addWidget(QLabel("Statut:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tous les statuts")
        self.status_filter.addItem("Soldé")
        self.status_filter.addItem("Partiellement payé")
        self.status_filter.addItem("Non payé")
        self.status_filter.currentTextChanged.connect(self.filter_students)
        filter_layout.addWidget(self.status_filter)
        
        layout.addLayout(filter_layout)
        
        # Table des élèves
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(7)
        self.students_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Classe", "Année", "Total dû", "Statut"
        ])
        self.students_table.horizontalHeader().setStretchLastSection(True)
        self.students_table.setSelectionBehavior(QTableWidget.SelectRows)
        # Correction IMP-02 de l'audit : les cellules ne doivent pas être
        # éditables (édition sans effet sur la base, source de confusion).
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.students_table.doubleClicked.connect(self.show_student_detail)
        layout.addWidget(self.students_table)
        
        # Boutons d'action pour les élèves
        student_buttons = QHBoxLayout()
        
        self.view_student_btn = QPushButton("Voir détails")
        self.view_student_btn.clicked.connect(self.show_selected_student_detail)
        student_buttons.addWidget(self.view_student_btn)
        
        self.edit_student_btn = QPushButton("Modifier")
        self.edit_student_btn.clicked.connect(self.edit_student)
        student_buttons.addWidget(self.edit_student_btn)
        
        self.delete_student_btn = QPushButton("Supprimer")
        self.delete_student_btn.clicked.connect(self.delete_student)
        student_buttons.addWidget(self.delete_student_btn)
        
        self.add_payment_btn = QPushButton("Enregistrer paiement")
        self.add_payment_btn.clicked.connect(self.add_payment)
        student_buttons.addWidget(self.add_payment_btn)
        
        layout.addLayout(student_buttons)
        
        return tab
    
    def load_dashboard_stats(self):
        """Charge les statistiques du tableau de bord"""
        # Statistiques globales
        stats = self.dashboard_service.get_overview_stats()
        
        self.stats_table.setRowCount(6)
        stats_data = [
            ("Nombre total d'élèves", str(stats['nombre_total_eleves'])),
            ("Total encaissé", format_montant(stats['total_encaisse'])),
            ("Total restant dû", format_montant(stats['total_restant_du'])),
            ("Élèves soldés", str(stats['nombre_eleves_soldes'])),
            ("Élèves partiellement payés", str(stats['nombre_eleves_partiellement_payes'])),
            ("Élèves non payés", str(stats['nombre_eleves_non_payes']))
        ]
        
        for row, (metric, value) in enumerate(stats_data):
            self.stats_table.setItem(row, 0, QTableWidgetItem(metric))
            self.stats_table.setItem(row, 1, QTableWidgetItem(value))
        
        # Statistiques par classe
        class_stats = self.dashboard_service.get_class_stats()
        
        self.class_table.setRowCount(len(class_stats))
        for row, stat in enumerate(class_stats):
            self.class_table.setItem(row, 0, QTableWidgetItem(stat['classe']))
            self.class_table.setItem(row, 1, QTableWidgetItem(str(stat['nombre_eleves'])))
            self.class_table.setItem(row, 2, QTableWidgetItem(format_montant(stat['total_encaisse'])))
            self.class_table.setItem(row, 3, QTableWidgetItem(format_montant(stat['total_restant'])))
            self.class_table.setItem(row, 4, QTableWidgetItem(str(stat['nombre_soldes'])))
    
    def load_students(self):
        """Charge la liste des élèves"""
        students = self.student_service.get_all_students()
        
        self.students_table.setRowCount(len(students))
        
        for row, student in enumerate(students):
            self.students_table.setItem(row, 0, QTableWidgetItem(str(student['id'])))
            self.students_table.setItem(row, 1, QTableWidgetItem(student['nom']))
            self.students_table.setItem(row, 2, QTableWidgetItem(student['prenom']))
            self.students_table.setItem(row, 3, QTableWidgetItem(student['classe']))
            self.students_table.setItem(row, 4, QTableWidgetItem(student['annee_scolaire']))
            self.students_table.setItem(row, 5, QTableWidgetItem(format_montant(student['montant_total'])))
            self.students_table.setItem(row, 6, QTableWidgetItem(student['statut']))
        
        # Mettre à jour le filtre de classe
        current_class = self.class_filter.currentText()
        self.class_filter.clear()
        self.class_filter.addItem("Toutes les classes")
        classes = self.student_service.get_classes()
        for classe in classes:
            self.class_filter.addItem(classe)
        
        # Restaurer la sélection si possible
        index = self.class_filter.findText(current_class)
        if index >= 0:
            self.class_filter.setCurrentIndex(index)
    
    def filter_students(self):
        """Filtre la liste des élèves"""
        search_text = self.search_input.text().lower()
        class_filter = self.class_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        students = self.student_service.get_all_students()
        
        filtered_students = []
        for student in students:
            # Filtre par recherche
            if search_text and search_text not in student['nom'].lower() and search_text not in student['prenom'].lower():
                continue
            
            # Filtre par classe
            if class_filter != "Toutes les classes" and student['classe'] != class_filter:
                continue
            
            # Filtre par statut
            if status_filter != "Tous les statuts" and student['statut'] != status_filter:
                continue
            
            filtered_students.append(student)
        
        self.students_table.setRowCount(len(filtered_students))
        
        for row, student in enumerate(filtered_students):
            self.students_table.setItem(row, 0, QTableWidgetItem(str(student['id'])))
            self.students_table.setItem(row, 1, QTableWidgetItem(student['nom']))
            self.students_table.setItem(row, 2, QTableWidgetItem(student['prenom']))
            self.students_table.setItem(row, 3, QTableWidgetItem(student['classe']))
            self.students_table.setItem(row, 4, QTableWidgetItem(student['annee_scolaire']))
            self.students_table.setItem(row, 5, QTableWidgetItem(format_montant(student['montant_total'])))
            self.students_table.setItem(row, 6, QTableWidgetItem(student['statut']))
    
    def add_student(self):
        """Ajoute un nouvel élève"""
        dialog = StudentDialog(self)
        if dialog.exec():
            student_data = dialog.get_student_data()
            try:
                student_id = self.student_service.create_student(
                    student_data['nom'],
                    student_data['prenom'],
                    student_data['classe'],
                    student_data['annee_scolaire'],
                    student_data['montant_total']
                )
                QMessageBox.information(self, "Succès", f"Élève créé avec succès (ID: {student_id})")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création: {str(e)}")
    
    def edit_student(self):
        """Modifie un élève sélectionné"""
        selected_rows = self.students_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un élève")
            return
        
        row = self.students_table.currentRow()
        student_id = int(self.students_table.item(row, 0).text())
        
        student = self.student_service.get_student(student_id)
        if not student:
            QMessageBox.warning(self, "Erreur", "Élève introuvable")
            return
        
        dialog = StudentDialog(self, student)
        if dialog.exec():
            student_data = dialog.get_student_data()
            try:
                success = self.student_service.update_student(
                    student_id,
                    student_data['nom'],
                    student_data['prenom'],
                    student_data['classe'],
                    student_data['annee_scolaire'],
                    student_data['montant_total']
                )
                if success:
                    QMessageBox.information(self, "Succès", "Élève modifié avec succès")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Erreur", "Erreur lors de la modification")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification: {str(e)}")
    
    def delete_student(self):
        """Supprime un élève sélectionné"""
        selected_rows = self.students_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un élève")
            return
        
        row = self.students_table.currentRow()
        student_id = int(self.students_table.item(row, 0).text())
        student_name = self.students_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer l'élève {student_name} ?\nCela supprimera également tous ses paiements.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.student_service.delete_student(student_id)
                if success:
                    QMessageBox.information(self, "Succès", "Élève supprimé avec succès")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Erreur", "Erreur lors de la suppression")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def add_payment(self):
        """Enregistre un paiement pour un élève sélectionné"""
        selected_rows = self.students_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un élève")
            return
        
        row = self.students_table.currentRow()
        student_id = int(self.students_table.item(row, 0).text())
        
        dialog = PaymentDialog(self, student_id, self.student_service, self.payment_service, self.receipt_service)
        if dialog.exec():
            QMessageBox.information(self, "Succès", "Paiement enregistré avec succès")
            self.refresh_data()
    
    def show_student_detail(self, item):
        """Affiche les détails d'un élève (double-clic)"""
        row = item.row()
        student_id = int(self.students_table.item(row, 0).text())
        self.show_student_detail_by_id(student_id)
    
    def show_selected_student_detail(self):
        """Affiche les détails de l'élève sélectionné"""
        selected_rows = self.students_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un élève")
            return
        
        row = self.students_table.currentRow()
        student_id = int(self.students_table.item(row, 0).text())
        self.show_student_detail_by_id(student_id)
    
    def show_student_detail_by_id(self, student_id):
        """Affiche les détails d'un élève par son ID"""
        dialog = StudentDetailDialog(student_id, self.student_service, self.payment_service, self.receipt_service, self)
        dialog.exec()
    
    def refresh_data(self):
        """Actualise toutes les données"""
        self.load_dashboard_stats()
        self.load_students()
