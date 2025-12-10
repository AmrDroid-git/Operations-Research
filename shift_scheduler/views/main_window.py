"""
Main Window
Integrates all tabs and provides application structure
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QPushButton, QStatusBar,
                             QMenuBar, QMenu, QMessageBox, QFileDialog, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
from models.employee import EmployeeManager
from models.demand import DemandProfile
from views.employee_tab import EmployeeTab
from views.demand_tab import DemandTab
from views.schedule_tab import ScheduleTab
import json
import pickle
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Planificateur de Quarts - Retail Staff Scheduler")
        self.setMinimumSize(1200, 800)
        
        # Initialize data structures
        self.employee_manager = EmployeeManager()
        self.demand_profile = DemandProfile(
            store_open_hour=8,
            store_close_hour=20,
            staff_per_customer_ratio=0.05,
            min_staff_per_hour=1
        )
        
        # Current theme
        self.is_dark_theme = False
        
        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()
        
        # Load light theme on startup
        try:
            qss_file = self._get_resource_path('style.qss')
            self._load_stylesheet(qss_file)
        except Exception as e:
            print(f"Warning: Could not load theme: {e}")
        
        # Load sample data
        self.load_sample_data()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget for different sections
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Create tabs with actual implementations
        self.employees_tab = EmployeeTab(self.employee_manager)
        self.demand_tab = DemandTab(self.demand_profile)
        self.schedule_tab = ScheduleTab(self.employee_manager, self.demand_profile)
        
        # Connect signals
        self.employees_tab.employees_changed.connect(self.on_data_changed)
        self.demand_tab.demand_changed.connect(self.on_data_changed)
        
        # Wrap tabs in scroll areas so content fits smaller screens
        self.tabs.addTab(self._wrap_scroll(self.employees_tab), "👥 Employés")
        self.tabs.addTab(self._wrap_scroll(self.demand_tab), "📊 Demande")
        self.tabs.addTab(self._wrap_scroll(self.schedule_tab), "🗓️ Planification")
        
        main_layout.addWidget(self.tabs)
        
    def create_header(self):
        """Create application header"""
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Title
        title = QLabel("Planificateur de Quarts de Travail")
        title.setObjectName("headerTitle")
        title_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        title.setFont(title_font)
        
        # Subtitle
        subtitle = QLabel("Optimisation intelligente des horaires du personnel avec Gurobi")
        subtitle.setObjectName("headerSubtitle")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle.setFont(subtitle_font)
        
        # Layout for title and subtitle
        title_layout = QVBoxLayout()
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.setSpacing(2)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Theme toggle button
        self.theme_btn = QPushButton("🌙 Mode Sombre")
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        header_layout.addWidget(self.theme_btn)
        
        return header_widget
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&Fichier")
        
        new_action = QAction("Nouveau projet", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Ouvrir...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Enregistrer", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Enregistrer sous...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Sample data submenu
        sample_menu = file_menu.addMenu("Charger exemple")
        
        retail_action = QAction("Magasin détail (standard)", self)
        retail_action.triggered.connect(lambda: self.load_sample_data("retail"))
        sample_menu.addAction(retail_action)
        
        restaurant_action = QAction("Restaurant", self)
        restaurant_action.triggered.connect(lambda: self.load_sample_data("restaurant"))
        sample_menu.addAction(restaurant_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Quitter", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Édition")
        
        clear_action = QAction("Effacer toutes les données", self)
        clear_action.triggered.connect(self.clear_all_data)
        edit_menu.addAction(clear_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Aide")
        
        guide_action = QAction("Guide d'utilisation", self)
        guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(guide_action)
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")
        
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.is_dark_theme = not self.is_dark_theme
        
        try:
            if self.is_dark_theme:
                self.theme_btn.setText("☀️ Mode Clair")
                # Load dark theme
                qss_file = self._get_resource_path('style_dark.qss')
                self._load_stylesheet(qss_file)
                self.status_bar.showMessage("Thème sombre activé")
            else:
                self.theme_btn.setText("🌙 Mode Sombre")
                # Load light theme
                qss_file = self._get_resource_path('style.qss')
                self._load_stylesheet(qss_file)
                self.status_bar.showMessage("Thème clair activé")
        except Exception as e:
            QMessageBox.warning(self, "Erreur de thème",
                              f"Impossible de charger le thème:\n{str(e)}")
    
    def _get_resource_path(self, resource_name: str) -> str:
        """Get the absolute path to a resource file"""
        # Get the directory where main.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # Go up from views/ to root
        resource_path = os.path.join(project_root, 'resources', resource_name)
        return resource_path
    
    def _load_stylesheet(self, stylesheet_path: str):
        """Load and apply a QSS stylesheet"""
        if not os.path.exists(stylesheet_path):
            raise FileNotFoundError(f"Stylesheet not found: {stylesheet_path}")
        
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            stylesheet = f.read()
        
        QApplication.instance().setStyleSheet(stylesheet)

    def _wrap_scroll(self, widget: QWidget) -> QWidget:
        """Wrap a tab widget in a scroll area to allow vertical scrolling"""
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(widget)
        return scroll
    
    def on_data_changed(self):
        """Handle data changes"""
        self.status_bar.showMessage("Données modifiées", 3000)
    
    def new_project(self):
        """Create new project"""
        reply = QMessageBox.question(
            self, "Nouveau projet",
            "Créer un nouveau projet? Les données non sauvegardées seront perdues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_all_data()
            self.status_bar.showMessage("Nouveau projet créé")
    
    def open_project(self):
        """Open saved project"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir projet",
            "", "Projet Shift Scheduler (*.ssp);;Tous les fichiers (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                
                # Load employee data
                self.employee_manager.clear()
                for emp_data in data.get('employees', []):
                    self.employee_manager.add_employee(**emp_data)
                
                # Load demand data
                self.demand_profile = DemandProfile.from_dict(data.get('demand', {}))
                
                # Update tabs with new data
                self.demand_tab.demand_profile = self.demand_profile
                self.schedule_tab.demand_profile = self.demand_profile
                
                # Refresh all tabs to display new data
                self.employees_tab.refresh_table()
                self.demand_tab.load_demand_data()
                
                self.status_bar.showMessage(f"Projet chargé: {filename}")
                QMessageBox.information(self, "Succès", "Projet chargé avec succès!")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", 
                                   f"Impossible d'ouvrir le projet:\n{str(e)}")
    
    def save_project(self):
        """Save project with current filename"""
        if not hasattr(self, 'current_filename'):
            self.save_project_as()
        else:
            self._save_to_file(self.current_filename)
    
    def save_project_as(self):
        """Save project with new filename"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer projet",
            "", "Projet Shift Scheduler (*.ssp);;Tous les fichiers (*.*)"
        )
        
        if filename:
            self.current_filename = filename
            self._save_to_file(filename)
    
    def _save_to_file(self, filename: str):
        """Internal save method"""
        try:
            data = {
                'employees': [emp.to_dict() for emp in 
                            self.employee_manager.get_all_employees()],
                'demand': self.demand_profile.to_dict()
            }
            
            with open(filename, 'wb') as f:
                pickle.dump(data, f)
            
            self.status_bar.showMessage(f"Projet sauvegardé: {filename}")
            QMessageBox.information(self, "Succès", "Projet sauvegardé avec succès!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur",
                               f"Impossible de sauvegarder:\n{str(e)}")
    
    def clear_all_data(self):
        """Clear all employee and demand data"""
        self.employee_manager.clear()
        self.demand_profile = DemandProfile()
        self.employees_tab.refresh_table()
        self.demand_tab.reset_demand()
        self.status_bar.showMessage("Données effacées")
    
    def load_sample_data(self, data_type: str = "retail"):
        """Load sample data for testing"""
        # Clear existing data
        self.employee_manager.clear()
        
        if data_type == "retail":
            # Sample retail employees
            self.employee_manager.add_employee(
                "Marie Dubois", 18.50, max_hours_per_day=8,
                availability=set(range(8, 20)), skills=["Caisse", "Service client"]
            )
            self.employee_manager.add_employee(
                "Jean Martin", 16.00, max_hours_per_day=6,
                availability=set(range(9, 18)), skills=["Stock"]
            )
            self.employee_manager.add_employee(
                "Sophie Leroux", 22.00, max_hours_per_day=8,
                availability=set(range(8, 20)), skills=["Manager", "Caisse"]
            )
            self.employee_manager.add_employee(
                "Pierre Blanc", 15.50, max_hours_per_day=4,
                availability=set(range(14, 20)), skills=["Stock", "Merchandising"]
            )
            self.employee_manager.add_employee(
                "Emma Petit", 17.00, max_hours_per_day=8,
                availability=set(range(8, 17)), skills=["Service client", "Caisse"]
            )
            
            # Sample demand - bimodal pattern
            self.demand_profile.apply_pattern("bimodal")
            
        elif data_type == "restaurant":
            # Restaurant staff
            self.employee_manager.add_employee(
                "Chef Antoine", 25.00, max_hours_per_day=10,
                availability=set(range(10, 22)), skills=["Cuisine"]
            )
            self.employee_manager.add_employee(
                "Serveur Lucas", 14.00, max_hours_per_day=8,
                availability=set(range(11, 23)), skills=["Service"]
            )
            
            # Lunch and dinner peaks
            self.demand_profile.apply_pattern("bimodal")
        
        # Refresh UI
        self.employees_tab.refresh_table()
        self.demand_tab.load_demand_data()
        self.status_bar.showMessage(f"Données exemple '{data_type}' chargées")
    
    def show_user_guide(self):
        """Show user guide"""
        guide_text = """
        <h2>Guide d'utilisation</h2>
        
        <h3>1. Employés</h3>
        <p>Ajoutez vos employés avec leurs taux horaires, disponibilités et compétences.</p>
        
        <h3>2. Demande</h3>
        <p>Configurez la demande horaire attendue (nombre de clients par heure).</p>
        
        <h3>3. Planification</h3>
        <p>Cliquez sur "Optimiser" pour générer le planning optimal avec Gurobi.</p>
        
        <h3>Conseils</h3>
        <ul>
        <li>Définissez au moins 3-4 employés pour de bons résultats</li>
        <li>Assurez-vous que les disponibilités couvrent les heures d'ouverture</li>
        <li>Utilisez les motifs prédéfinis pour la demande</li>
        </ul>
        """
        
        QMessageBox.about(self, "Guide d'utilisation", guide_text)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "À propos",
                         "<h3>Planificateur de Quarts v1.0</h3>"
                         "<p>Application d'optimisation des horaires de travail pour le commerce de détail</p>"
                         "<p><b>Technologies:</b></p>"
                         "<ul>"
                         "<li>PyQt6 - Interface graphique</li>"
                         "<li>Gurobi - Optimisation mathématique</li>"
                         "<li>Python 3.8+</li>"
                         "</ul>"
                         "<p><b>Fonctionnalités:</b></p>"
                         "<ul>"
                         "<li>Gestion des employés et disponibilités</li>"
                         "<li>Configuration de la demande horaire</li>"
                         "<li>Optimisation automatique avec contraintes</li>"
                         "<li>Visualisation Gantt des horaires</li>"
                         "</ul>"
                         "<p>aziz haddadi © 2025</p>")