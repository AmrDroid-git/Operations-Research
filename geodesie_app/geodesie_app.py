"""
Application de Conception de Réseaux de Mesure Géodésique
Projet RO - PLNE avec Gurobi et PyQt6
Version compatible avec l'interface commune
"""

import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                             QTableWidget, QTableWidgetItem, QTextEdit, QGroupBox,
                             QMessageBox, QProgressBar, QTabWidget, QDoubleSpinBox,
                             QCheckBox, QComboBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import gurobipy as gp
from gurobipy import GRB


class OptimizationWorker(QThread):
    """Thread worker pour exécuter l'optimisation sans bloquer l'interface"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, data):
        super().__init__()
        self.data = data
        
    def run(self):
        try:
            self.progress.emit(10)
            result = self.solve_geodesic_network(self.data)
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def solve_geodesic_network(self, data):
        """
        Modélisation PLNE du problème de conception de réseau géodésique
        
        Variables de décision:
        - x[i]: variable binaire = 1 si station i est installée
        - y[i,j]: variable binaire = 1 si mesure entre stations i et j
        - z[i]: variable binaire = 1 si station i est une station de référence
        
        Fonction objectif: Minimiser le coût total
        - Coûts d'installation des stations
        - Coûts des mesures entre stations
        - Bonus pour la précision (qualité géométrique)
        
        Contraintes:
        - Couverture minimale de points
        - Nombre minimum de stations
        - Redondance des mesures pour précision
        - Contraintes de visibilité
        - Contraintes budgétaires
        - Contraintes de connectivité du réseau
        """
        
        n_points = data['n_points']
        n_potential_stations = data['n_stations']
        min_stations = data['min_stations']
        max_stations = data['max_stations']
        budget = data['budget']
        coverage_radius = data['coverage_radius']
        min_redundancy = data['min_redundancy']
        
        # Coûts
        installation_costs = data['installation_costs']
        measurement_costs = data['measurement_costs']
        
        # Matrices de distance et visibilité
        distances = data['distances']
        visibility = data['visibility']
        coverage_matrix = data['coverage_matrix']
        
        self.progress.emit(20)
        
        # Création du modèle Gurobi
        model = gp.Model("GeodesicNetwork")
        model.setParam('OutputFlag', 0)  # Désactiver l'affichage
        model.setParam('TimeLimit', 120)  # Limite de temps 2 minutes
        
        # Variables de décision
        # x[i] = 1 si station i est installée
        x = model.addVars(n_potential_stations, vtype=GRB.BINARY, name="station")
        
        # y[i,j] = 1 si mesure entre stations i et j
        y = model.addVars(n_potential_stations, n_potential_stations, 
                         vtype=GRB.BINARY, name="measurement")
        
        # z[i] = 1 si station i est une station de référence (haute précision)
        z = model.addVars(n_potential_stations, vtype=GRB.BINARY, name="reference")
        
        # w[p] = 1 si point p est couvert
        w = model.addVars(n_points, vtype=GRB.BINARY, name="covered")
        
        self.progress.emit(30)
        
        # Fonction objectif: Minimiser coûts - bonus précision
        installation_cost = gp.quicksum(installation_costs[i] * x[i] 
                                       for i in range(n_potential_stations))
        
        measurement_cost = gp.quicksum(measurement_costs[i][j] * y[i,j] 
                                      for i in range(n_potential_stations)
                                      for j in range(n_potential_stations) if i < j)
        
        reference_cost = gp.quicksum(installation_costs[i] * 0.5 * z[i] 
                                    for i in range(n_potential_stations))
        
        # Bonus pour qualité géométrique (angle optimal)
        precision_bonus = gp.quicksum(y[i,j] * (1.0 / (1.0 + distances[i][j])) * 100
                                     for i in range(n_potential_stations)
                                     for j in range(n_potential_stations) if i < j)
        
        model.setObjective(installation_cost + measurement_cost + reference_cost - precision_bonus, 
                          GRB.MINIMIZE)
        
        self.progress.emit(40)
        
        # CONTRAINTES
        
        # C1: Nombre de stations entre min et max
        model.addConstr(gp.quicksum(x[i] for i in range(n_potential_stations)) >= min_stations,
                       "min_stations")
        model.addConstr(gp.quicksum(x[i] for i in range(n_potential_stations)) <= max_stations,
                       "max_stations")
        
        # C2: Budget maximum
        model.addConstr(installation_cost + measurement_cost + reference_cost <= budget,
                       "budget_constraint")
        
        # C3: Couverture des points à mesurer
        for p in range(n_points):
            model.addConstr(gp.quicksum(coverage_matrix[p][i] * x[i] 
                                       for i in range(n_potential_stations)) >= 1,
                           f"coverage_point_{p}")
        
        # C4: Mesure possible uniquement si les deux stations existent
        for i in range(n_potential_stations):
            for j in range(i+1, n_potential_stations):
                model.addConstr(y[i,j] <= x[i], f"measure_station1_{i}_{j}")
                model.addConstr(y[i,j] <= x[j], f"measure_station2_{i}_{j}")
        
        # C5: Contrainte de visibilité
        for i in range(n_potential_stations):
            for j in range(i+1, n_potential_stations):
                if visibility[i][j] == 0:
                    model.addConstr(y[i,j] == 0, f"visibility_{i}_{j}")
        
        self.progress.emit(50)
        
        # C6: Redondance minimale - chaque station doit avoir au moins min_redundancy mesures
        for i in range(n_potential_stations):
            model.addConstr(gp.quicksum(y[i,j] for j in range(n_potential_stations) if j != i) 
                           >= min_redundancy * x[i],
                           f"redundancy_{i}")
        
        # C7: Au moins 25% des stations doivent être des références
        min_reference = int(0.25 * min_stations)
        model.addConstr(gp.quicksum(z[i] for i in range(n_potential_stations)) >= min_reference,
                       "min_reference_stations")
        
        # C8: Une station de référence doit être installée
        for i in range(n_potential_stations):
            model.addConstr(z[i] <= x[i], f"reference_requires_station_{i}")
        
        # C9: Connectivité du réseau - chaque station connectée à au moins 2 autres
        for i in range(n_potential_stations):
            model.addConstr(gp.quicksum(y[i,j] + y[j,i] 
                                       for j in range(n_potential_stations) if j != i) 
                           >= 2 * x[i],
                           f"connectivity_{i}")
        
        # C10: Distance maximale entre stations connectées (pour précision)
        max_measurement_distance = coverage_radius * 1.5
        for i in range(n_potential_stations):
            for j in range(i+1, n_potential_stations):
                if distances[i][j] > max_measurement_distance:
                    model.addConstr(y[i,j] == 0, f"max_distance_{i}_{j}")
        
        self.progress.emit(70)
        
        # Optimisation
        model.optimize()
        
        self.progress.emit(90)
        
        # Extraction des résultats
        if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
            result = {
                'status': 'optimal' if model.status == GRB.OPTIMAL else 'time_limit',
                'objective_value': model.objVal,
                'stations': [i for i in range(n_potential_stations) if x[i].X > 0.5],
                'references': [i for i in range(n_potential_stations) if z[i].X > 0.5],
                'measurements': [(i,j) for i in range(n_potential_stations) 
                               for j in range(i+1, n_potential_stations) 
                               if y[i,j].X > 0.5],
                'n_stations': sum(1 for i in range(n_potential_stations) if x[i].X > 0.5),
                'n_measurements': sum(1 for i in range(n_potential_stations) 
                                    for j in range(i+1, n_potential_stations) 
                                    if y[i,j].X > 0.5),
                'total_cost': model.objVal,
                'installation_cost': sum(installation_costs[i] for i in range(n_potential_stations) 
                                       if x[i].X > 0.5),
                'measurement_cost': sum(measurement_costs[i][j] 
                                      for i in range(n_potential_stations)
                                      for j in range(i+1, n_potential_stations) 
                                      if y[i,j].X > 0.5),
                'gap': model.MIPGap if hasattr(model, 'MIPGap') else 0,
                'solve_time': model.Runtime
            }
            return result
        else:
            raise Exception(f"Pas de solution trouvée. Statut: {model.status}")


class NetworkCanvas(FigureCanvas):
    """Canvas pour afficher le réseau géodésique"""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 6))
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def plot_network(self, data, result):
        """Dessiner le réseau géodésique optimisé"""
        self.axes.clear()
        
        n_stations = data['n_stations']
        n_points = data['n_points']
        
        # Générer positions pour visualisation
        np.random.seed(42)
        station_coords = np.random.rand(n_stations, 2) * 100
        point_coords = np.random.rand(n_points, 2) * 100
        
        # Dessiner les points à mesurer
        self.axes.scatter(point_coords[:, 0], point_coords[:, 1], 
                         c='lightblue', s=50, alpha=0.5, label='Points à mesurer')
        
        # Dessiner les stations installées
        installed_stations = result['stations']
        reference_stations = result['references']
        
        regular_stations = [s for s in installed_stations if s not in reference_stations]
        
        if regular_stations:
            self.axes.scatter(station_coords[regular_stations, 0], 
                            station_coords[regular_stations, 1],
                            c='green', s=200, marker='^', 
                            label='Stations régulières', zorder=5)
        
        if reference_stations:
            self.axes.scatter(station_coords[reference_stations, 0], 
                            station_coords[reference_stations, 1],
                            c='red', s=300, marker='*', 
                            label='Stations de référence', zorder=6)
        
        # Dessiner les mesures
        for i, j in result['measurements']:
            self.axes.plot([station_coords[i, 0], station_coords[j, 0]],
                          [station_coords[i, 1], station_coords[j, 1]],
                          'b-', alpha=0.3, linewidth=1)
        
        # Numéroter les stations
        for idx in installed_stations:
            self.axes.annotate(f'S{idx}', 
                             (station_coords[idx, 0], station_coords[idx, 1]),
                             fontsize=8, ha='center', va='center')
        
        self.axes.set_xlabel('X (km)')
        self.axes.set_ylabel('Y (km)')
        self.axes.set_title('Réseau Géodésique Optimisé')
        self.axes.legend()
        self.axes.grid(True, alpha=0.3)
        self.fig.tight_layout()
        self.draw()


class GeodesieMainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌍 Conception de Réseaux Géodésiques - PLNE")
        self.setGeometry(100, 100, 1400, 900)
        
        self.worker = None
        self.result = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Panneau gauche - Paramètres
        left_panel = self.create_parameters_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Panneau droit - Résultats et visualisation
        right_panel = self.create_results_panel()
        main_layout.addWidget(right_panel, 2)
        
    def create_parameters_panel(self):
        """Créer le panneau de paramètres"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Titre
        title = QLabel("⚙️ Paramètres du Problème")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Paramètres principaux
        params_group = QGroupBox("Paramètres Principaux")
        params_layout = QVBoxLayout()
        
        # Nombre de points à couvrir
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Points à mesurer:"))
        self.n_points_spin = QSpinBox()
        self.n_points_spin.setRange(5, 50)
        self.n_points_spin.setValue(15)
        h1.addWidget(self.n_points_spin)
        params_layout.addLayout(h1)
        
        # Nombre de stations potentielles
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Stations potentielles:"))
        self.n_stations_spin = QSpinBox()
        self.n_stations_spin.setRange(5, 30)
        self.n_stations_spin.setValue(12)
        h2.addWidget(self.n_stations_spin)
        params_layout.addLayout(h2)
        
        # Nombre minimum de stations
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Stations min:"))
        self.min_stations_spin = QSpinBox()
        self.min_stations_spin.setRange(3, 20)
        self.min_stations_spin.setValue(6)
        h3.addWidget(self.min_stations_spin)
        params_layout.addLayout(h3)
        
        # Nombre maximum de stations
        h4 = QHBoxLayout()
        h4.addWidget(QLabel("Stations max:"))
        self.max_stations_spin = QSpinBox()
        self.max_stations_spin.setRange(5, 25)
        self.max_stations_spin.setValue(10)
        h4.addWidget(self.max_stations_spin)
        params_layout.addLayout(h4)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Contraintes
        constraints_group = QGroupBox("Contraintes")
        constraints_layout = QVBoxLayout()
        
        # Budget
        h5 = QHBoxLayout()
        h5.addWidget(QLabel("Budget (k€):"))
        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setRange(50, 500)
        self.budget_spin.setValue(200)
        self.budget_spin.setSingleStep(10)
        h5.addWidget(self.budget_spin)
        constraints_layout.addLayout(h5)
        
        # Rayon de couverture
        h6 = QHBoxLayout()
        h6.addWidget(QLabel("Rayon couverture (km):"))
        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(5, 50)
        self.radius_spin.setValue(20)
        self.radius_spin.setSingleStep(5)
        h6.addWidget(self.radius_spin)
        constraints_layout.addLayout(h6)
        
        # Redondance minimale
        h7 = QHBoxLayout()
        h7.addWidget(QLabel("Redondance min:"))
        self.redundancy_spin = QSpinBox()
        self.redundancy_spin.setRange(2, 6)
        self.redundancy_spin.setValue(3)
        h7.addWidget(self.redundancy_spin)
        constraints_layout.addLayout(h7)
        
        constraints_group.setLayout(constraints_layout)
        layout.addWidget(constraints_group)
        
        # Options avancées
        advanced_group = QGroupBox("Options Avancées")
        advanced_layout = QVBoxLayout()
        
        self.terrain_check = QCheckBox("Terrain difficile (coûts +30%)")
        advanced_layout.addWidget(self.terrain_check)
        
        self.high_precision_check = QCheckBox("Haute précision (redondance +1)")
        advanced_layout.addWidget(self.high_precision_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("📊 Générer Données")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_data)
        buttons_layout.addWidget(self.generate_btn)
        
        self.solve_btn = QPushButton("🚀 Résoudre")
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.solve_btn.clicked.connect(self.solve_problem)
        self.solve_btn.setEnabled(False)
        buttons_layout.addWidget(self.solve_btn)
        
        layout.addLayout(buttons_layout)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
        
    def create_results_panel(self):
        """Créer le panneau de résultats"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Onglets
        self.tabs = QTabWidget()
        
        # Onglet résultats textuels
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        results_title = QLabel("📈 Résultats de l'Optimisation")
        results_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        results_layout.addWidget(results_title)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                background-color: #f5f5f5;
                color: #000000;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        self.tabs.addTab(results_tab, "📊 Résultats")
        
        # Onglet visualisation
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        
        self.network_canvas = NetworkCanvas()
        viz_layout.addWidget(self.network_canvas)
        
        self.tabs.addTab(viz_tab, "🗺️ Visualisation")
        
        layout.addWidget(self.tabs)
        
        return panel
        
    def generate_data(self):
        """Générer les données du problème"""
        try:
            n_points = self.n_points_spin.value()
            n_stations = self.n_stations_spin.value()
            min_stations = self.min_stations_spin.value()
            max_stations = self.max_stations_spin.value()
            budget = self.budget_spin.value()
            coverage_radius = self.radius_spin.value()
            redundancy = self.redundancy_spin.value()
            
            # Validation
            if min_stations > max_stations:
                QMessageBox.warning(self, "Erreur", 
                                  "Le nombre minimum de stations doit être ≤ au maximum")
                return
            
            if max_stations > n_stations:
                QMessageBox.warning(self, "Erreur", 
                                  "Le nombre maximum de stations doit être ≤ aux stations potentielles")
                return
            
            # Ajustements selon options
            if self.high_precision_check.isChecked():
                redundancy += 1
            
            # Génération des données
            np.random.seed(42)
            
            # Coûts d'installation (10-30k€)
            base_installation = np.random.uniform(10, 30, n_stations)
            if self.terrain_check.isChecked():
                base_installation *= 1.3
            
            # Matrice de distances entre stations
            station_positions = np.random.rand(n_stations, 2) * 100
            distances = np.zeros((n_stations, n_stations))
            for i in range(n_stations):
                for j in range(n_stations):
                    distances[i][j] = np.linalg.norm(station_positions[i] - station_positions[j])
            
            # Coûts de mesure basés sur la distance
            measurement_costs = np.zeros((n_stations, n_stations))
            for i in range(n_stations):
                for j in range(n_stations):
                    if i != j:
                        measurement_costs[i][j] = 2 + distances[i][j] * 0.1
            
            # Matrice de visibilité (80% de visibilité aléatoire)
            visibility = np.random.choice([0, 1], size=(n_stations, n_stations), p=[0.2, 0.8])
            np.fill_diagonal(visibility, 0)
            
            # Rendre la matrice symétrique
            for i in range(n_stations):
                for j in range(i+1, n_stations):
                    visibility[j][i] = visibility[i][j]
            
            # Matrice de couverture (point-station)
            point_positions = np.random.rand(n_points, 2) * 100
            coverage_matrix = np.zeros((n_points, n_stations))
            for p in range(n_points):
                for s in range(n_stations):
                    dist = np.linalg.norm(point_positions[p] - station_positions[s])
                    if dist <= coverage_radius:
                        coverage_matrix[p][s] = 1
            
            # Vérifier que chaque point peut être couvert
            for p in range(n_points):
                if np.sum(coverage_matrix[p]) == 0:
                    # Forcer au moins une station à couvrir ce point
                    closest_station = np.argmin([np.linalg.norm(point_positions[p] - station_positions[s]) 
                                                for s in range(n_stations)])
                    coverage_matrix[p][closest_station] = 1
            
            self.data = {
                'n_points': n_points,
                'n_stations': n_stations,
                'min_stations': min_stations,
                'max_stations': max_stations,
                'budget': budget,
                'coverage_radius': coverage_radius,
                'min_redundancy': redundancy,
                'installation_costs': base_installation,
                'measurement_costs': measurement_costs,
                'distances': distances,
                'visibility': visibility,
                'coverage_matrix': coverage_matrix
            }
            
            self.solve_btn.setEnabled(True)
            self.results_text.setText("Données générées avec succès!\n\n" +
                                     "=" * 50 + "\n" +
                                     f"Points à mesurer: {n_points}\n" +
                                     f"Stations potentielles: {n_stations}\n" +
                                     f"Budget: {budget}k€\n" +
                                     f"Rayon de couverture: {coverage_radius}km\n" +
                                     f"Redondance minimale: {redundancy}\n" +
                                     "=" * 50 + "\n\n" +
                                     "Cliquez sur '🚀 Résoudre' pour optimiser le réseau.")
            
            QMessageBox.information(self, "Succès", 
                                  "Données générées avec succès!\nVous pouvez maintenant lancer l'optimisation.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def solve_problem(self):
        """Lancer la résolution du problème"""
        if not hasattr(self, 'data'):
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord générer les données")
            return
        
        self.solve_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.results_text.setText("Résolution en cours...\n\nVeuillez patienter, Gurobi optimise votre réseau géodésique.")
        
        # Créer et lancer le worker thread
        self.worker = OptimizationWorker(self.data)
        self.worker.finished.connect(self.on_optimization_finished)
        self.worker.error.connect(self.on_optimization_error)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.start()
    
    def on_optimization_finished(self, result):
        """Traiter les résultats de l'optimisation"""
        self.result = result
        self.solve_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        
        # Afficher les résultats
        text = "=" * 70 + "\n"
        text += "RÉSULTATS DE L'OPTIMISATION DU RÉSEAU GÉODÉSIQUE\n"
        text += "=" * 70 + "\n\n"
        
        text += f"Statut: {result['status'].upper()}\n"
        text += f"Temps de résolution: {result['solve_time']:.2f} secondes\n"
        text += f"📊 Gap d'optimalité: {result['gap']*100:.2f}%\n\n"
        
        text += "-" * 70 + "\n"
        text += "📡 CONFIGURATION DU RÉSEAU\n"
        text += "-" * 70 + "\n"
        text += f"Nombre de stations installées: {result['n_stations']}\n"
        text += f"Stations: {', '.join(['S' + str(s) for s in result['stations']])}\n"
        text += f"Stations de référence: {', '.join(['S' + str(s) for s in result['references']])}\n"
        text += f"Nombre de mesures: {result['n_measurements']}\n\n"
        
        text += "-" * 70 + "\n"
        text += "ANALYSE DES COÛTS\n"
        text += "-" * 70 + "\n"
        text += f"Coût total: {result['total_cost']:.2f} k€\n"
        text += f"  ├─ Installation: {result['installation_cost']:.2f} k€\n"
        text += f"  └─ Mesures: {result['measurement_cost']:.2f} k€\n"
        text += f"Budget disponible: {self.data['budget']:.2f} k€\n"
        text += f"Budget restant: {self.data['budget'] - result['installation_cost'] - result['measurement_cost']:.2f} k€\n"
        text += f"Taux d'utilisation: {(result['installation_cost'] + result['measurement_cost']) / self.data['budget'] * 100:.1f}%\n\n"
        
        text += "-" * 70 + "\n"
        text += "DÉTAIL DES MESURES\n"
        text += "-" * 70 + "\n"
        for idx, (i, j) in enumerate(result['measurements'][:20], 1):
            text += f"{idx:2d}. S{i} ↔ S{j} (distance: {self.data['distances'][i][j]:.1f}km)\n"
        if len(result['measurements']) > 20:
            text += f"... et {len(result['measurements']) - 20} autres mesures\n"
        
        text += "\n" + "=" * 70 + "\n"
        text += "📊 INDICATEURS DE QUALITÉ\n"
        text += "=" * 70 + "\n"
        avg_redundancy = result['n_measurements'] / result['n_stations'] if result['n_stations'] > 0 else 0
        text += f"Redondance moyenne: {avg_redundancy:.1f} mesures/station\n"
        text += f"Ratio stations de référence: {len(result['references']) / result['n_stations'] * 100:.1f}%\n"
        text += f"Densité du réseau: {result['n_measurements'] / (result['n_stations'] * (result['n_stations'] - 1) / 2) * 100:.1f}%\n"
        
        text += "\n" + "=" * 70 + "\n"
        
        self.results_text.setText(text)
        
        # Visualiser le réseau
        self.network_canvas.plot_network(self.data, result)
        self.tabs.setCurrentIndex(1)  # Basculer vers l'onglet visualisation
        
        # Message de succès
        QMessageBox.information(self, "Optimisation Réussie", 
                              f"Solution optimale trouvée!\n\n"
                              f"Stations installées: {result['n_stations']}\n"
                              f"Coût total: {result['total_cost']:.2f} k€\n"
                              f"Temps: {result['solve_time']:.2f}s")
        
    def on_optimization_error(self, error_msg):
        """Gérer les erreurs d'optimisation"""
        self.solve_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Erreur d'optimisation", error_msg)
        self.results_text.setText(f"ERREUR:\n{error_msg}")


def main():
    app = QApplication(sys.argv)
    window = GeodesieMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()