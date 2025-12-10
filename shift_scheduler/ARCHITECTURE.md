# 🏗️ Architecture Technique

Documentation de l'architecture du Planificateur de Quarts de Travail.

## 📐 Vue d'ensemble

L'application suit une architecture **MVC (Model-View-Controller)** adaptée pour PyQt6:

```
┌─────────────────────────────────────────────────┐
│                   Main.py                       │
│           (Application Entry Point)             │
└───────────────────┬─────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼────┐          ┌────▼────┐
    │  Views  │◄────────►│ Models  │
    │  (UI)   │          │ (Data)  │
    └────┬────┘          └────┬────┘
         │                     │
         └──────────┬──────────┘
                    │
              ┌─────▼──────┐
              │Controllers │
              │ (Logic)    │
              └────────────┘
```

## 🗂️ Structure des dossiers

```
shift_scheduler/
│
├── 📄 main.py                      # Point d'entrée de l'application
│   └── Initialise QApplication, charge le style, lance MainWindow
│
├── 📁 models/                      # MODÈLES DE DONNÉES
│   ├── __init__.py                # Exports du package
│   ├── employee.py                # Classes Employee et EmployeeManager
│   ├── demand.py                  # Classe DemandProfile
│   └── optimization.py            # ShiftScheduler (Gurobi)
│
├── 📁 views/                       # INTERFACE UTILISATEUR
│   ├── __init__.py                # Exports du package
│   ├── main_window.py             # Fenêtre principale + menus
│   ├── employee_tab.py            # Gestion des employés
│   ├── demand_tab.py              # Configuration de la demande
│   └── schedule_tab.py            # Optimisation et visualisation
│
├── 📁 controllers/                 # LOGIQUE MÉTIER
│   ├── __init__.py                # Exports du package
│   └── exporter.py                # Export des résultats
│
└── 📁 resources/                   # RESSOURCES
    └── style.qss                 # Feuille de style Qt
```

## 🧩 Composants principaux

### 1. Models (Modèles de données)

#### `models/employee.py`
```python
Employee (dataclass)
├── Attributs
│   ├── id: int
│   ├── name: str
│   ├── hourly_rate: float
│   ├── max_hours_per_day: int
│   ├── availability: Set[int]  # Heures disponibles
│   └── skills: List[str]
│
└── Méthodes
    ├── is_available(hour) → bool
    ├── has_skill(skill) → bool
    └── get_daily_cost(hours) → float

EmployeeManager
├── employees: List[Employee]
└── Méthodes CRUD
    ├── add_employee(...) → Employee
    ├── remove_employee(id) → bool
    ├── get_employee(id) → Employee
    └── get_all_employees() → List[Employee]
```

**Responsabilités:**
- Stockage des données employés
- Validation des données
- Opérations CRUD
- Calculs de capacité et coûts

#### `models/demand.py`
```python
DemandProfile (dataclass)
├── Attributs
│   ├── store_open_hour: int
│   ├── store_close_hour: int
│   ├── hourly_demand: Dict[int, int]  # heure → clients
│   ├── staff_per_customer_ratio: float
│   └── min_staff_per_hour: int
│
└── Méthodes
    ├── set_demand(hour, count)
    ├── get_demand(hour) → int
    ├── calculate_required_staff(hour) → int
    ├── apply_pattern(name)  # Motifs prédéfinis
    └── scale_demand(factor)
```

**Responsabilités:**
- Gestion de la demande horaire
- Calcul du personnel requis
- Motifs de demande prédéfinis
- Analyse des pics d'activité

#### `models/optimization.py`
```python
ShiftScheduler
├── Attributs
│   ├── employees: List[Employee]
│   ├── demand: DemandProfile
│   ├── model: gp.Model (Gurobi)
│   └── variables: Dict
│
└── Méthodes
    ├── build_model(...) → Model
    ├── solve(time_limit) → ScheduleResult
    └── get_solution_summary() → str

ScheduleResult (dataclass)
├── schedule: Dict[emp_id, List[shifts]]
├── total_cost: float
├── total_hours: Dict[emp_id, hours]
├── coverage: Dict[hour, staff_count]
└── objective_value: float
```

**Responsabilités:**
- Construction du modèle MILP Gurobi
- Définition des variables et contraintes
- Résolution du problème d'optimisation
- Extraction de la solution

**Modèle mathématique:**
```
Variables:
  x[e,h] ∈ {0,1}  : employé e travaille heure h
  y[e,h] ∈ {0,1}  : employé e commence quart à heure h
  s[h] ∈ ℤ+       : nombre d'employés à heure h

Objectif:
  min Σ(e,h) x[e,h] * rate[e] + penalties

Contraintes:
  1. s[h] = Σ(e) x[e,h]                    (comptage)
  2. Σ(h) x[e,h] ≤ max_hours[e]           (max heures)
  3. x[e,h] = 0 if e unavailable at h     (disponibilité)
  4. s[h] ≥ required[h]                    (couverture)
  5. Σ(h) y[e,h] ≤ 1                      (un seul quart)
  6. Continuité des quarts
```

### 2. Views (Interface utilisateur)

#### `views/main_window.py`
```python
MainWindow (QMainWindow)
├── Composants
│   ├── Header (gradient, titre)
│   ├── QTabWidget (onglets)
│   ├── MenuBar (Fichier, Édition, Aide)
│   └── StatusBar
│
├── Data
│   ├── employee_manager: EmployeeManager
│   └── demand_profile: DemandProfile
│
└── Méthodes
    ├── init_ui()
    ├── create_menu_bar()
    ├── save_project() / open_project()
    └── load_sample_data()
```

**Responsabilités:**
- Structure principale de l'application
- Gestion des onglets
- Menus et actions globales
- Sauvegarde/chargement de projets

#### `views/employee_tab.py`
```python
EmployeeTab (QWidget)
├── Composants UI
│   ├── QTableWidget (liste employés)
│   ├── Boutons: Ajouter, Modifier, Supprimer
│   └── Statistiques (nombre, taux moyen, capacité)
│
└── EmployeeDialog (QDialog)
    ├── Formulaire de saisie
    ├── Checkboxes disponibilité (par heure)
    └── Checkboxes compétences

Signaux:
  employees_changed: pyqtSignal()
```

**Responsabilités:**
- Affichage de la liste des employés
- Formulaire d'ajout/modification
- Gestion des disponibilités et compétences
- Statistiques en temps réel

#### `views/demand_tab.py`
```python
DemandTab (QWidget)
├── Composants UI
│   ├── DemandBarChart (graphique personnalisé)
│   ├── Configuration (heures, ratio, min staff)
│   ├── Sliders + SpinBoxes (demande par heure)
│   └── ComboBox motifs prédéfinis
│
└── DemandBarChart (QWidget)
    └── paintEvent() → Dessine graphique barres

Signaux:
  demand_changed: pyqtSignal()
```

**Responsabilités:**
- Visualisation graphique de la demande
- Configuration des paramètres du magasin
- Sliders interactifs pour chaque heure
- Application de motifs prédéfinis
- Calcul automatique du personnel requis

#### `views/schedule_tab.py`
```python
ScheduleTab (QWidget)
├── Composants UI
│   ├── Paramètres d'optimisation
│   ├── Bouton "Optimiser"
│   ├── ProgressBar
│   ├── ScheduleGanttChart (Gantt)
│   ├── QTableWidget (résumé)
│   └── Statistiques
│
├── OptimizationThread (QThread)
│   └── Exécute l'optimisation en arrière-plan
│
└── ScheduleGanttChart (QWidget)
    └── paintEvent() → Dessine diagramme Gantt

Signaux:
  OptimizationThread.finished
  OptimizationThread.progress
  OptimizationThread.error
```

**Responsabilités:**
- Configuration des paramètres d'optimisation
- Lancement de l'optimisation (thread)
- Visualisation Gantt des résultats
- Tableau récapitulatif des affectations
- Analyse de couverture

### 3. Controllers (Logique métier)

#### `controllers/exporter.py`
```python
ScheduleExporter
├── Données
│   ├── result: ScheduleResult
│   ├── employee_manager: EmployeeManager
│   └── demand_profile: DemandProfile
│
└── Méthodes
    ├── to_csv(filename)
    ├── to_json(filename)
    ├── to_text(filename)
    └── to_html(filename)
```

**Responsabilités:**
- Export multi-format des résultats
- Génération de rapports
- Formatage pour partage/impression

## 🔄 Flux de données

### Flux typique d'utilisation:

```
1. CONFIGURATION
   User Input (UI) → Views → Models
   
2. OPTIMISATION
   Views → Models (ShiftScheduler) → Gurobi → ScheduleResult
   
3. VISUALISATION
   ScheduleResult → Views (Gantt, Tables)
   
4. EXPORT
   ScheduleResult + Models → Controllers → Fichier
```

### Diagramme de séquence - Optimisation:

```
User          ScheduleTab    ShiftScheduler    Gurobi
 │                │               │              │
 │ Click "Optimize"│              │              │
 ├───────────────>│               │              │
 │                │ build_model() │              │
 │                ├──────────────>│              │
 │                │               │ create vars  │
 │                │               ├─────────────>│
 │                │               │ add constraints│
 │                │               ├─────────────>│
 │                │               │ set objective│
 │                │               ├─────────────>│
 │                │               │<─────────────┤
 │                │ solve()       │              │
 │                ├──────────────>│              │
 │                │               │ optimize()   │
 │                │               ├─────────────>│
 │                │               │              │
 │                │               │ (solving...) │
 │                │               │              │
 │                │               │<─────────────┤
 │                │<──────────────┤              │
 │                │ ScheduleResult│              │
 │<───────────────┤               │              │
 │   Display      │               │              │
```

## 🎨 Système de style

### Qt Style Sheets (QSS)

Le fichier `resources/style.qss` définit:

```css
/* Composants stylés */
- QMainWindow, QWidget
- QPushButton (standard, primary)
- QTableWidget
- QTabWidget
- QLabel (headers, subtitles)
- QLineEdit, QSpinBox
- QProgressBar
- QScrollBar
- QMenu, QMenuBar
```

**Palette de couleurs:**
```
Primary:   #667eea (violet)
Secondary: #764ba2 (violet foncé)
Success:   #48bb78 (vert)
Warning:   #ed8936 (orange)
Danger:    #f56565 (rouge)
Gray-50:   #f7fafc
Gray-100:  #edf2f7
Gray-800:  #2d3748
```

## 🧵 Threading

### Problème:
Gurobi peut prendre plusieurs secondes/minutes. Le thread principal UI doit rester réactif.

### Solution:
```python
class OptimizationThread(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)
    
    def run(self):
        # Heavy computation in background
        result = self.scheduler.solve()
        self.finished.emit(result)
```

**Avantages:**
- UI reste réactive
- Possibilité d'afficher une ProgressBar
- Annulation possible (avec implémentation)

## 💾 Persistance

### Format de sauvegarde (.ssp):

```python
# Structure du fichier
{
    'employees': [
        {
            'id': 1,
            'name': 'Sophie',
            'hourly_rate': 18.5,
            'availability': [8, 9, 10, ...],
            ...
        },
        ...
    ],
    'demand': {
        'store_open_hour': 8,
        'store_close_hour': 20,
        'hourly_demand': {8: 30, 9: 40, ...},
        ...
    }
}
```

**Sérialisation:** Python `pickle` (binaire, rapide)

**Alternative:** JSON (lisible, portable)

## ⚡ Performance

### Optimisations appliquées:

1. **Modèle Gurobi efficient:**
   - Variables binaires minimales
   - Contraintes linéaires seulement
   - Pas de contraintes quadratiques

2. **UI réactive:**
   - Threading pour calculs lourds
   - Mise à jour progressive des graphiques
   - Debouncing des sliders

3. **Mémoire:**
   - Pas de duplication inutile des données
   - Partage des références Models entre Views

### Limites de scalabilité:

| Métrique | Limite pratique | Temps résolution |
|----------|----------------|------------------|
| Employés | 20-30 | < 2 min |
| Heures/jour | 24 | < 1 min |
| Jours | 1 (actuel) | - |

**Pour améliorer:** Multi-threading Gurobi, simplification des contraintes

## 🧪 Tests

### Structure de tests (à implémenter):

```
tests/
├── test_models/
│   ├── test_employee.py
│   ├── test_demand.py
│   └── test_optimization.py
├── test_views/
│   └── test_ui_components.py
└── test_integration/
    └── test_full_workflow.py
```

### Tests critiques:

```python
# test_optimization.py
def test_simple_schedule():
    """Vérifie qu'un problème simple a une solution"""
    emp = Employee(1, "Test", 15.0, availability={8,9,10})
    demand = DemandProfile()
    demand.set_demand(8, 10)
    
    scheduler = ShiftScheduler([emp], demand)
    scheduler.build_model()
    result = scheduler.solve()
    
    assert result.status == "Optimal"
    assert result.total_cost > 0
```

## 🔒 Sécurité et validation

### Validation des données:

1. **Employee:**
   - Taux horaire > 0
   - Nom non vide
   - Heures max raisonnable

2. **Demand:**
   - Heures d'ouverture valides
   - Demande ≥ 0
   - Ratio cohérent

3. **Optimization:**
   - Au moins 1 employé
   - Demande configurée
   - Paramètres dans les limites

## 🚀 Extensions futures

### Architecture pour nouvelles fonctionnalités:

**Planning multi-jours:**
```python
# models/weekly_demand.py
class WeeklyDemandProfile:
    daily_profiles: Dict[str, DemandProfile]  # "monday" → profile

# models/optimization.py
class WeeklyScheduler(ShiftScheduler):
    def build_weekly_model(self):
        # Variables x[e,d,h] : employé e, jour d, heure h
        ...
```

**Préférences employés:**
```python
# models/employee.py
@dataclass
class Employee:
    ...
    preferred_days: Set[str]  # ["monday", "tuesday"]
    preferred_shifts: Set[str]  # ["morning", "evening"]
    
# Ajouter contraintes soft dans optimization.py
```

**API REST:**
```python
# api/routes.py
from flask import Flask
app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize_schedule():
    # Recevoir données JSON
    # Lancer optimisation
    # Retourner résultat JSON
```

## 📚 Références

### Documentation externe:

- **PyQt6:** https://doc.qt.io/qtforpython/
- **Gurobi Python API:** https://www.gurobi.com/documentation/
- **Python dataclasses:** https://docs.python.org/3/library/dataclasses.html

### Patterns utilisés:

- **MVC:** Séparation Model-View-Controller
- **Observer:** PyQt Signals/Slots
- **Factory:** Création d'objets Employee, Demand
- **Strategy:** Différents objectifs d'optimisation

---

**Maintenu par:** Haddadi Mohamed Aziz
**Dernière mise à jour:** December 2025