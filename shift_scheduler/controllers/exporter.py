"""
Export Controller
Handles exporting schedule results to various formats
"""

import csv
import json
from datetime import datetime
from typing import Dict, List
from models.optimization import ScheduleResult
from models.employee import Employee, EmployeeManager
from models.demand import DemandProfile


class ScheduleExporter:
    """Export schedule results to different formats"""
    
    def __init__(self, result: ScheduleResult, 
                 employee_manager: EmployeeManager,
                 demand_profile: DemandProfile):
        self.result = result
        self.employee_manager = employee_manager
        self.demand_profile = demand_profile
        self.emp_dict = {emp.id: emp for emp in employee_manager.get_all_employees()}
    
    def to_csv(self, filename: str):
        """Export schedule to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Planification des Quarts de Travail'])
            writer.writerow([f'Généré le: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
            writer.writerow([f'Coût total: ${self.result.total_cost:.2f}'])
            writer.writerow([])
            
            # Schedule details
            writer.writerow(['ID Employé', 'Nom', 'Horaires', 'Heures Total', 
                           'Taux Horaire', 'Coût'])
            
            for emp_id, shifts in self.result.schedule.items():
                if shifts and emp_id in self.emp_dict:
                    emp = self.emp_dict[emp_id]
                    hours = self.result.total_hours[emp_id]
                    cost = hours * emp.hourly_rate
                    shift_str = ", ".join([f"{s}:00-{e}:00" for s, e in shifts])
                    
                    writer.writerow([
                        emp_id,
                        emp.name,
                        shift_str,
                        hours,
                        f"${emp.hourly_rate:.2f}",
                        f"${cost:.2f}"
                    ])
            
            writer.writerow([])
            
            # Coverage analysis
            writer.writerow(['Analyse de Couverture'])
            writer.writerow(['Heure', 'Demande', 'Personnel Requis', 
                           'Personnel Planifié', 'Statut'])
            
            required = self.demand_profile.get_all_required_staff()
            
            for hour in sorted(self.result.coverage.keys()):
                demand = self.demand_profile.get_demand(hour)
                req = required[hour]
                actual = self.result.coverage[hour]
                
                if actual < req:
                    status = 'Sous-effectif'
                elif actual > req:
                    status = 'Sur-effectif'
                else:
                    status = 'Parfait'
                
                writer.writerow([
                    f"{hour}:00",
                    demand,
                    req,
                    actual,
                    status
                ])
    
    def to_json(self, filename: str):
        """Export schedule to JSON file"""
        data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_cost': self.result.total_cost,
                'solve_time': self.result.solve_time,
                'status': self.result.status
            },
            'employees': [],
            'coverage': {}
        }
        
        # Employee schedules
        for emp_id, shifts in self.result.schedule.items():
            if shifts and emp_id in self.emp_dict:
                emp = self.emp_dict[emp_id]
                hours = self.result.total_hours[emp_id]
                cost = hours * emp.hourly_rate
                
                data['employees'].append({
                    'id': emp_id,
                    'name': emp.name,
                    'shifts': [{'start': s, 'end': e} for s, e in shifts],
                    'total_hours': hours,
                    'hourly_rate': emp.hourly_rate,
                    'cost': cost
                })
        
        # Coverage data
        required = self.demand_profile.get_all_required_staff()
        for hour in sorted(self.result.coverage.keys()):
            data['coverage'][str(hour)] = {
                'demand': self.demand_profile.get_demand(hour),
                'required': required[hour],
                'scheduled': self.result.coverage[hour]
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def to_text(self, filename: str):
        """Export schedule to formatted text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("PLANIFICATION DES QUARTS DE TRAVAIL\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Coût total: ${self.result.total_cost:.2f}\n")
            f.write(f"Temps de calcul: {self.result.solve_time:.2f}s\n")
            f.write(f"Statut: {self.result.status}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("HORAIRES DES EMPLOYÉS\n")
            f.write("-" * 70 + "\n\n")
            
            for emp_id, shifts in self.result.schedule.items():
                if shifts and emp_id in self.emp_dict:
                    emp = self.emp_dict[emp_id]
                    hours = self.result.total_hours[emp_id]
                    cost = hours * emp.hourly_rate
                    
                    f.write(f"{emp.name} (#{emp_id})\n")
                    f.write(f"  Taux horaire: ${emp.hourly_rate:.2f}/h\n")
                    f.write(f"  Horaires: ")
                    
                    shift_strs = [f"{s}:00-{e}:00" for s, e in shifts]
                    f.write(", ".join(shift_strs) + "\n")
                    
                    f.write(f"  Total: {hours}h | Coût: ${cost:.2f}\n\n")
            
            f.write("\n" + "-" * 70 + "\n")
            f.write("ANALYSE DE COUVERTURE\n")
            f.write("-" * 70 + "\n\n")
            
            required = self.demand_profile.get_all_required_staff()
            
            f.write(f"{'Heure':<10} {'Demande':<10} {'Requis':<10} "
                   f"{'Planifié':<10} {'Statut':<15}\n")
            f.write("-" * 70 + "\n")
            
            for hour in sorted(self.result.coverage.keys()):
                demand = self.demand_profile.get_demand(hour)
                req = required[hour]
                actual = self.result.coverage[hour]
                
                if actual < req:
                    status = 'Sous-effectif'
                elif actual > req:
                    status = 'Sur-effectif'
                else:
                    status = 'Parfait'
                
                f.write(f"{hour}:00{'':<6} {demand:<10} {req:<10} "
                       f"{actual:<10} {status:<15}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            
            # Statistics
            total_emp = sum(1 for shifts in self.result.schedule.values() if shifts)
            total_hours = sum(self.result.total_hours.values())
            avg_hours = total_hours / total_emp if total_emp > 0 else 0
            
            shortage = sum(1 for h in self.result.coverage 
                          if self.result.coverage[h] < required[h])
            perfect = sum(1 for h in self.result.coverage 
                         if self.result.coverage[h] == required[h])
            surplus = sum(1 for h in self.result.coverage 
                         if self.result.coverage[h] > required[h])
            
            f.write("\nSTATISTIQUES\n")
            f.write("-" * 70 + "\n")
            f.write(f"Employés planifiés: {total_emp}\n")
            f.write(f"Heures totales: {total_hours:.1f}h\n")
            f.write(f"Moyenne par employé: {avg_hours:.1f}h\n")
            f.write(f"Couverture: {perfect}h parfait, {shortage}h sous-effectif, "
                   f"{surplus}h sur-effectif\n")
    
    def to_html(self, filename: str):
        """Export schedule to HTML file"""
        html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Planification des Quarts</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f7fa;
        }
        h1, h2 {
            color: #2d3748;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .metadata {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            background: white;
            border-collapse: collapse;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        th {
            background-color: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }
        tr:hover {
            background-color: #f7fafc;
        }
        .status-perfect { color: #48bb78; font-weight: bold; }
        .status-shortage { color: #f56565; font-weight: bold; }
        .status-surplus { color: #ed8936; font-weight: bold; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #718096;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📅 Planification des Quarts de Travail</h1>
        <p>Optimisation automatique avec Gurobi</p>
    </div>
"""
        
        # Metadata
        html += f"""
    <div class="metadata">
        <p><strong>Généré le:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p><strong>Coût total:</strong> ${self.result.total_cost:.2f}</p>
        <p><strong>Temps de calcul:</strong> {self.result.solve_time:.2f}s</p>
        <p><strong>Statut:</strong> {self.result.status}</p>
    </div>
"""
        
        # Employee schedules
        html += """
    <h2>Horaires des Employés</h2>
    <table>
        <thead>
            <tr>
                <th>Employé</th>
                <th>Horaires</th>
                <th>Heures Total</th>
                <th>Taux ($/h)</th>
                <th>Coût</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for emp_id, shifts in self.result.schedule.items():
            if shifts and emp_id in self.emp_dict:
                emp = self.emp_dict[emp_id]
                hours = self.result.total_hours[emp_id]
                cost = hours * emp.hourly_rate
                shift_str = ", ".join([f"{s}:00-{e}:00" for s, e in shifts])
                
                html += f"""
            <tr>
                <td><strong>{emp.name}</strong></td>
                <td>{shift_str}</td>
                <td>{hours}h</td>
                <td>${emp.hourly_rate:.2f}</td>
                <td>${cost:.2f}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
"""
        
        # Coverage analysis
        html += """
    <h2>Analyse de Couverture</h2>
    <table>
        <thead>
            <tr>
                <th>Heure</th>
                <th>Demande (clients)</th>
                <th>Personnel Requis</th>
                <th>Personnel Planifié</th>
                <th>Statut</th>
            </tr>
        </thead>
        <tbody>
"""
        
        required = self.demand_profile.get_all_required_staff()
        
        for hour in sorted(self.result.coverage.keys()):
            demand = self.demand_profile.get_demand(hour)
            req = required[hour]
            actual = self.result.coverage[hour]
            
            if actual < req:
                status = '<span class="status-shortage">Sous-effectif</span>'
            elif actual > req:
                status = '<span class="status-surplus">Sur-effectif</span>'
            else:
                status = '<span class="status-perfect">Parfait</span>'
            
            html += f"""
            <tr>
                <td>{hour}:00</td>
                <td>{demand}</td>
                <td>{req}</td>
                <td>{actual}</td>
                <td>{status}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
"""
        
        # Statistics
        total_emp = sum(1 for shifts in self.result.schedule.values() if shifts)
        total_hours = sum(self.result.total_hours.values())
        avg_hours = total_hours / total_emp if total_emp > 0 else 0
        
        shortage = sum(1 for h in self.result.coverage 
                      if self.result.coverage[h] < required[h])
        perfect = sum(1 for h in self.result.coverage 
                     if self.result.coverage[h] == required[h])
        surplus = sum(1 for h in self.result.coverage 
                     if self.result.coverage[h] > required[h])
        
        html += f"""
    <h2>Statistiques</h2>
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{total_emp}</div>
            <div class="stat-label">Employés planifiés</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_hours:.1f}h</div>
            <div class="stat-label">Heures totales</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_hours:.1f}h</div>
            <div class="stat-label">Moyenne par employé</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{perfect}h</div>
            <div class="stat-label">Couverture parfaite</div>
        </div>
    </div>
    
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)