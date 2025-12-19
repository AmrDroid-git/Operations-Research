"""
Script de test rapide pour vérifier que tout fonctionne
À placer à la racine du projet
"""

import sys
import os

def test_imports():
    """Test 1: Vérifier que tous les modules peuvent être importés"""
    print("=" * 70)
    print("TEST 1: Vérification des imports")
    print("=" * 70)
    
    tests = {
        "PyQt6": "from PyQt6.QtWidgets import QApplication",
        "NumPy": "import numpy as np",
        "Matplotlib": "import matplotlib.pyplot as plt",
        "Gurobi": "import gurobipy as gp",
    }
    
    results = []
    for name, import_stmt in tests.items():
        try:
            exec(import_stmt)
            print(f"✅ {name}: OK")
            results.append(True)
        except Exception as e:
            print(f"❌ {name}: ERREUR - {str(e)}")
            results.append(False)
    
    print()
    return all(results)


def test_gurobi_license():
    """Test 2: Vérifier que Gurobi a une licence valide"""
    print("=" * 70)
    print("TEST 2: Vérification de la licence Gurobi")
    print("=" * 70)
    
    try:
        import gurobipy as gp
        
        # Créer un modèle simple pour tester la licence
        model = gp.Model("test")
        x = model.addVar(name="x")
        model.setObjective(x, gp.GRB.MINIMIZE)
        model.addConstr(x >= 1)
        model.setParam('OutputFlag', 0)
        model.optimize()
        
        if model.status == gp.GRB.OPTIMAL:
            print(f"✅ Licence Gurobi valide")
            print(f"   Version: {gp.gurobi.version()}")
            return True
        else:
            print(f"❌ Problème avec Gurobi (status: {model.status})")
            return False
            
    except Exception as e:
        print(f"❌ Erreur Gurobi: {str(e)}")
        print("   → Assurez-vous d'avoir activé votre licence avec 'grbgetkey'")
        return False


def test_geodesie_module():
    """Test 3: Vérifier que le module géodésie peut être importé"""
    print("\n" + "=" * 70)
    print("TEST 3: Import du module géodésie")
    print("=" * 70)
    
    try:
        # Vérifier que le dossier existe
        if not os.path.exists('geodesie_app'):
            print("❌ Le dossier 'geodesie_app' n'existe pas")
            print("   → Créez-le avec: mkdir geodesie_app")
            return False
        
        # Vérifier que __init__.py existe
        if not os.path.exists('geodesie_app/__init__.py'):
            print("❌ Le fichier 'geodesie_app/__init__.py' n'existe pas")
            print("   → Créez-le avec: touch geodesie_app/__init__.py")
            return False
        
        # Vérifier que geodesie_app.py existe
        if not os.path.exists('geodesie_app/geodesie_app.py'):
            print("❌ Le fichier 'geodesie_app/geodesie_app.py' n'existe pas")
            print("   → Copiez le code de l'application dans ce fichier")
            return False
        
        # Tenter l'import
        from geodesie_app.geodesie_app import GeodesieMainWindow
        print("✅ Module géodésie importé avec succès")
        print(f"   Classe trouvée: {GeodesieMainWindow.__name__}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'import: {str(e)}")
        return False


def test_gui_creation():
    """Test 4: Vérifier que l'interface peut être créée"""
    print("\n" + "=" * 70)
    print("TEST 4: Création de l'interface graphique")
    print("=" * 70)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from geodesie_app.geodesie_app import GeodesieMainWindow
        
        # Créer une application Qt (nécessaire pour créer des widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Créer la fenêtre
        window = GeodesieMainWindow()
        
        print("✅ Interface créée avec succès")
        print(f"   Titre: {window.windowTitle()}")
        print(f"   Taille: {window.width()}x{window.height()}")
        
        # Ne pas afficher la fenêtre, juste la créer
        window.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de création GUI: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_optimization_simple():
    """Test 5: Tester une optimisation simple"""
    print("\n" + "=" * 70)
    print("TEST 5: Test d'optimisation simple")
    print("=" * 70)
    
    try:
        import gurobipy as gp
        from gurobipy import GRB
        import numpy as np
        
        print("Création d'un problème de test (5 points, 4 stations)...")
        
        # Données simplifiées
        n_points = 5
        n_stations = 4
        
        np.random.seed(42)
        installation_costs = np.array([15.0, 20.0, 18.0, 22.0])
        
        # Matrice de couverture simple
        coverage_matrix = np.array([
            [1, 1, 0, 0],  # Point 0 couvert par stations 0,1
            [1, 0, 1, 0],  # Point 1 couvert par stations 0,2
            [0, 1, 1, 0],  # Point 2 couvert par stations 1,2
            [0, 0, 1, 1],  # Point 3 couvert par stations 2,3
            [0, 0, 0, 1],  # Point 4 couvert par station 3
        ])
        
        # Créer le modèle
        model = gp.Model("test_simple")
        model.setParam('OutputFlag', 0)
        
        x = model.addVars(n_stations, vtype=GRB.BINARY, name="station")
        
        model.setObjective(
            gp.quicksum(installation_costs[i] * x[i] for i in range(n_stations)),
            GRB.MINIMIZE
        )
        
        # Contraintes: chaque point doit être couvert
        for p in range(n_points):
            model.addConstr(
                gp.quicksum(coverage_matrix[p][i] * x[i] for i in range(n_stations)) >= 1
            )
        
        # Au moins 2 stations
        model.addConstr(gp.quicksum(x[i] for i in range(n_stations)) >= 2)
        
        print("Résolution...")
        model.optimize()
        
        if model.status == GRB.OPTIMAL:
            stations = [i for i in range(n_stations) if x[i].X > 0.5]
            print(f"✅ Solution optimale trouvée")
            print(f"   Stations installées: {stations}")
            print(f"   Coût: {model.objVal:.2f} k€")
            print(f"   Temps: {model.Runtime:.2f}s")
            return True
        else:
            print(f"❌ Pas de solution optimale (status: {model.status})")
            return False
            
    except Exception as e:
        print(f"❌ Erreur d'optimisation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_launcher_integration():
    """Test 6: Vérifier l'intégration avec le launcher"""
    print("\n" + "=" * 70)
    print("TEST 6: Intégration avec le launcher")
    print("=" * 70)
    
    try:
        # Vérifier que main_launcher.py existe
        if not os.path.exists('main_launcher.py'):
            print("⚠️  Fichier 'main_launcher.py' non trouvé")
            print("   Ce test est optionnel si vous n'utilisez pas le launcher")
            return True
        
        # Lire le contenu
        with open('main_launcher.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier la fonction open_geodesie
        if 'def open_geodesie(self):' in content:
            print("✅ Fonction 'open_geodesie' trouvée dans le launcher")
        else:
            print("⚠️  Fonction 'open_geodesie' non trouvée")
            print("   → Ajoutez-la au launcher")
        
        # Vérifier l'import
        if 'from geodesie_app.geodesie_app import GeodesieMainWindow' in content:
            print("✅ Import correct dans le launcher")
            return True
        else:
            print("⚠️  Import de géodésie non trouvé dans le launcher")
            return True  # Pas bloquant
            
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification: {str(e)}")
        return True  # Pas bloquant


def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "=" * 70)
    print("🧪 SUITE DE TESTS - APPLICATION GÉODÉSIE")
    print("=" * 70 + "\n")
    
    tests = [
        ("Imports des modules", test_imports),
        ("Licence Gurobi", test_gurobi_license),
        ("Module géodésie", test_geodesie_module),
        ("Interface graphique", test_gui_creation),
        ("Optimisation simple", test_optimization_simple),
        ("Intégration launcher", test_launcher_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE dans {name}: {str(e)}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    for name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{status:12} | {name}")
    
    total_success = sum(1 for _, s in results if s)
    total_tests = len(results)
    
    print("\n" + "-" * 70)
    print(f"Résultat global: {total_success}/{total_tests} tests réussis")
    
    if total_success == total_tests:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("Votre application est prête à être utilisée.")
    elif total_success >= total_tests - 1:
        print("\n✅ Tests principaux réussis")
        print("Vous pouvez utiliser l'application.")
    else:
        print("\n⚠️  Certains tests ont échoué")
        print("Vérifiez les erreurs ci-dessus avant de continuer.")
    
    print("=" * 70 + "\n")
    
    return total_success == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)