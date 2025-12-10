"""
Employee Management Tab
UI for managing employee data and availability
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QLabel,
                             QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox,
                             QCheckBox, QGridLayout, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from models.employee import Employee, EmployeeManager


class EmployeeDialog(QDialog):
    """Dialog for adding/editing employees"""
    
    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.employee = employee
        self.is_edit = employee is not None
        self.setWindowTitle("Modifier l'employé" if self.is_edit else "Nouvel employé")
        self.setMinimumWidth(500)
        self.init_ui()
        
        if self.is_edit:
            self.load_employee_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Basic Info Group
        basic_group = QGroupBox("Informations de base")
        basic_layout = QGridLayout()
        
        # Name
        basic_layout.addWidget(QLabel("Nom:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Prénom Nom")
        basic_layout.addWidget(self.name_edit, 0, 1)
        
        # Hourly Rate
        basic_layout.addWidget(QLabel("Taux horaire ($):"), 1, 0)
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(10.0, 100.0)
        self.rate_spin.setValue(15.0)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setSuffix(" $/h")
        basic_layout.addWidget(self.rate_spin, 1, 1)
        
        # Max hours per day
        basic_layout.addWidget(QLabel("Max heures/jour:"), 2, 0)
        self.max_hours_day = QSpinBox()
        self.max_hours_day.setRange(1, 12)
        self.max_hours_day.setValue(8)
        self.max_hours_day.setSuffix(" h")
        basic_layout.addWidget(self.max_hours_day, 2, 1)
        
        # Max hours per week
        basic_layout.addWidget(QLabel("Max heures/semaine:"), 3, 0)
        self.max_hours_week = QSpinBox()
        self.max_hours_week.setRange(1, 60)
        self.max_hours_week.setValue(40)
        self.max_hours_week.setSuffix(" h")
        basic_layout.addWidget(self.max_hours_week, 3, 1)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Availability Group
        avail_group = QGroupBox("Disponibilité (heures)")
        avail_layout = QVBoxLayout()
        
        self.availability_checks = {}
        hours_layout = QGridLayout()
        
        for i, hour in enumerate(range(6, 23)):
            checkbox = QCheckBox(f"{hour}:00")
            self.availability_checks[hour] = checkbox
            hours_layout.addWidget(checkbox, i // 6, i % 6)
        
        avail_layout.addLayout(hours_layout)
        
        # Quick select buttons
        quick_btns = QHBoxLayout()
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.clicked.connect(self.select_all_hours)
        clear_all_btn = QPushButton("Tout désélectionner")
        clear_all_btn.clicked.connect(self.clear_all_hours)
        quick_btns.addWidget(select_all_btn)
        quick_btns.addWidget(clear_all_btn)
        avail_layout.addLayout(quick_btns)
        
        avail_group.setLayout(avail_layout)
        layout.addWidget(avail_group)
        
        # Skills Group
        skills_group = QGroupBox("Compétences")
        skills_layout = QGridLayout()
        
        self.skill_checks = {}
        skills = ["Caisse", "Stock", "Service client", "Manager", "Merchandising", "Inventaire"]
        for i, skill in enumerate(skills):
            checkbox = QCheckBox(skill)
            self.skill_checks[skill] = checkbox
            skills_layout.addWidget(checkbox, i // 3, i % 3)
        
        skills_group.setLayout(skills_layout)
        layout.addWidget(skills_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def select_all_hours(self):
        for checkbox in self.availability_checks.values():
            checkbox.setChecked(True)
    
    def clear_all_hours(self):
        for checkbox in self.availability_checks.values():
            checkbox.setChecked(False)
    
    def load_employee_data(self):
        """Load existing employee data into form"""
        self.name_edit.setText(self.employee.name)
        self.rate_spin.setValue(self.employee.hourly_rate)
        self.max_hours_day.setValue(self.employee.max_hours_per_day)
        self.max_hours_week.setValue(self.employee.max_hours_per_week)
        
        # Set availability checkboxes
        for hour in self.employee.availability:
            if hour in self.availability_checks:
                self.availability_checks[hour].setChecked(True)
        
        # Set skill checkboxes
        for skill, checkbox in self.skill_checks.items():
            if skill in self.employee.skills:
                checkbox.setChecked(True)
    
    def get_employee_data(self):
        """Get employee data from form"""
        availability = set(
            hour for hour, checkbox in self.availability_checks.items()
            if checkbox.isChecked()
        )
        
        skills = [
            skill for skill, checkbox in self.skill_checks.items()
            if checkbox.isChecked()
        ]
        
        return {
            'name': self.name_edit.text().strip(),
            'hourly_rate': self.rate_spin.value(),
            'max_hours_per_day': self.max_hours_day.value(),
            'max_hours_per_week': self.max_hours_week.value(),
            'availability': availability,
            'skills': skills
        }


class EmployeeTab(QWidget):
    """Main employee management tab"""
    
    employees_changed = pyqtSignal()
    
    def __init__(self, employee_manager: EmployeeManager):
        super().__init__()
        self.employee_manager = employee_manager
        self.init_ui()
        self.refresh_table()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Gestion des Employés")
        header.setObjectName("tabHeader")
        header_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Stats row
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #718096; font-size: 11pt;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("➕ Ajouter")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self.add_employee)
        add_btn.setMinimumHeight(40)
        
        edit_btn = QPushButton("✏️ Modifier")
        edit_btn.clicked.connect(self.edit_employee)
        edit_btn.setMinimumHeight(40)
        
        delete_btn = QPushButton("🗑️ Supprimer")
        delete_btn.clicked.connect(self.delete_employee)
        delete_btn.setMinimumHeight(40)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Taux ($/h)", "Max h/jour", "Disponibilité", "Compétences"
        ])
        
        # Style table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_employee)
        
        layout.addWidget(self.table)
        
        self.update_stats()
    
    def refresh_table(self):
        """Refresh employee table"""
        self.table.setRowCount(0)
        
        for emp in self.employee_manager.get_all_employees():
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(emp.id)))
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(emp.name))
            
            # Rate
            self.table.setItem(row, 2, QTableWidgetItem(f"${emp.hourly_rate:.2f}"))
            
            # Max hours
            self.table.setItem(row, 3, QTableWidgetItem(f"{emp.max_hours_per_day}h"))
            
            # Availability
            avail_count = len(emp.availability)
            avail_text = f"{avail_count} heures"
            self.table.setItem(row, 4, QTableWidgetItem(avail_text))
            
            # Skills
            skills_text = ", ".join(emp.skills) if emp.skills else "Aucune"
            self.table.setItem(row, 5, QTableWidgetItem(skills_text))
        
        self.update_stats()
    
    def update_stats(self):
        """Update statistics display"""
        count = len(self.employee_manager)
        avg_rate = self.employee_manager.get_average_hourly_rate()
        capacity = self.employee_manager.get_total_labor_capacity()
        
        self.stats_label.setText(
            f"📊 {count} employés | Taux moyen: ${avg_rate:.2f}/h | "
            f"Capacité totale: {capacity}h/jour"
        )
    
    def add_employee(self):
        """Add new employee"""
        dialog = EmployeeDialog(self)
        if dialog.exec():
            data = dialog.get_employee_data()
            
            if not data['name']:
                QMessageBox.warning(self, "Erreur", "Le nom est requis!")
                return
            
            try:
                self.employee_manager.add_employee(**data)
                self.refresh_table()
                self.employees_changed.emit()
                QMessageBox.information(self, "Succès", 
                                      f"Employé {data['name']} ajouté!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur: {str(e)}")
    
    def edit_employee(self):
        """Edit selected employee"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aucune sélection", 
                              "Veuillez sélectionner un employé!")
            return
        
        row = selected[0].row()
        emp_id = int(self.table.item(row, 0).text())
        employee = self.employee_manager.get_employee(emp_id)
        
        if employee:
            dialog = EmployeeDialog(self, employee)
            if dialog.exec():
                data = dialog.get_employee_data()
                
                # Update employee
                employee.name = data['name']
                employee.hourly_rate = data['hourly_rate']
                employee.max_hours_per_day = data['max_hours_per_day']
                employee.max_hours_per_week = data['max_hours_per_week']
                employee.availability = data['availability']
                employee.skills = data['skills']
                
                self.refresh_table()
                self.employees_changed.emit()
                QMessageBox.information(self, "Succès", "Employé modifié!")
    
    def delete_employee(self):
        """Delete selected employee"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aucune sélection",
                              "Veuillez sélectionner un employé!")
            return
        
        row = selected[0].row()
        emp_id = int(self.table.item(row, 0).text())
        employee = self.employee_manager.get_employee(emp_id)
        
        if employee:
            reply = QMessageBox.question(
                self, "Confirmation",
                f"Supprimer {employee.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.employee_manager.remove_employee(emp_id)
                self.refresh_table()
                self.employees_changed.emit()
                QMessageBox.information(self, "Succès", "Employé supprimé!")