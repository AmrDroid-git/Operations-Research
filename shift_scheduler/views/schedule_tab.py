"""
Schedule Tab
UI for running optimization and viewing results
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QGridLayout, QComboBox,
                             QSpinBox, QCheckBox, QProgressBar, QTextEdit,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QHeaderView, QScrollArea, QAbstractScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from models.optimization import ShiftScheduler, ScheduleResult
from models.employee import EmployeeManager
from models.demand import DemandProfile


class OptimizationThread(QThread):
    """Thread for running optimization without freezing UI"""
    
    finished = pyqtSignal(object)  # Emits ScheduleResult
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, scheduler, params):
        super().__init__()
        self.scheduler = scheduler
        self.params = params
    
    def run(self):
        try:
            self.progress.emit("Construction du modèle...")
            # Only pass model-related parameters; keep solve-only options separate
            build_params = {k: v for k, v in self.params.items() if k != 'time_limit'}
            self.scheduler.build_model(**build_params)
            
            self.progress.emit("Optimisation en cours...")
            result = self.scheduler.solve(time_limit=self.params.get('time_limit', 60))
            
            self.progress.emit("Terminé!")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class ScheduleGanttChart(QWidget):
    """Gantt chart visualization of schedule"""
    
    def __init__(self):
        super().__init__()
        self.schedule_result = None
        self.employee_manager = None
        self.demand_profile = None
        self.setMinimumHeight(300)
    
    def set_data(self, result: ScheduleResult, emp_mgr: EmployeeManager, 
                 demand: DemandProfile):
        """Set schedule data and redraw"""
        self.schedule_result = result
        self.employee_manager = emp_mgr
        self.demand_profile = demand
        self.update()
    
    def paintEvent(self, event):
        """Draw Gantt chart"""
        if not self.schedule_result or not self.employee_manager:
            return
        
        from PyQt6.QtGui import QPainter, QPen, QBrush
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        margin_left = 150
        margin_top = 40
        margin_bottom = 30
        margin_right = 20
        
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        # Get employees with shifts
        emp_dict = {emp.id: emp for emp in self.employee_manager.get_all_employees()}
        scheduled_emps = [emp_id for emp_id in self.schedule_result.schedule 
                         if self.schedule_result.schedule[emp_id]]
        
        if not scheduled_emps:
            painter.drawText(width//2 - 100, height//2, 
                           "Aucun horaire à afficher")
            return
        
        row_height = chart_height / max(len(scheduled_emps), 1)
        
        # Time range
        open_h = self.demand_profile.store_open_hour
        close_h = self.demand_profile.store_close_hour
        hours_range = close_h - open_h
        hour_width = chart_width / hours_range
        
        # Draw title
        painter.setPen(QColor("#2d3748"))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 10, width, 30, Qt.AlignmentFlag.AlignCenter,
                        "Planning Optimisé")
        
        # Draw time axis
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#718096"))
        
        for i, hour in enumerate(range(open_h, close_h + 1)):
            x = margin_left + i * hour_width
            painter.drawLine(int(x), margin_top, int(x), height - margin_bottom)
            painter.drawText(int(x) - 15, height - margin_bottom + 5, 30, 20,
                           Qt.AlignmentFlag.AlignCenter, f"{hour}h")
        
        # Draw employee rows
        for i, emp_id in enumerate(scheduled_emps):
            y = margin_top + i * row_height
            
            # Employee name
            emp = emp_dict.get(emp_id)
            if emp:
                painter.setPen(QColor("#2d3748"))
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(5, int(y + row_height/2 - 10), margin_left - 10, 20,
                               Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                               emp.name)
                font.setBold(False)
                painter.setFont(font)
            
            # Draw shifts
            shifts = self.schedule_result.schedule[emp_id]
            for start, end in shifts:
                x_start = margin_left + (start - open_h) * hour_width
                x_end = margin_left + (end - open_h) * hour_width
                shift_width = x_end - x_start
                
                # Shift bar
                painter.setBrush(QBrush(QColor("#667eea")))
                painter.setPen(QPen(QColor("#5568d3"), 2))
                painter.drawRoundedRect(int(x_start + 2), int(y + 5),
                                       int(shift_width - 4), int(row_height - 10),
                                       5, 5)
                
                # Shift time text
                painter.setPen(QColor("white"))
                font.setBold(True)
                painter.setFont(font)
                shift_text = f"{start}:00-{end}:00"
                painter.drawText(int(x_start), int(y + 5), 
                               int(shift_width), int(row_height - 10),
                               Qt.AlignmentFlag.AlignCenter, shift_text)
                font.setBold(False)
                painter.setFont(font)


class ScheduleTab(QWidget):
    """Main schedule optimization tab"""
    
    def __init__(self, employee_manager: EmployeeManager, 
                 demand_profile: DemandProfile):
        super().__init__()
        self.employee_manager = employee_manager
        self.demand_profile = demand_profile
        self.scheduler = None
        self.result = None
        self.optimization_thread = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Génération de Planning")
        header.setObjectName("tabHeader")
        header_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Configuration Group
        config_group = QGroupBox("Paramètres d'optimisation")
        config_layout = QGridLayout()
        
        # Objective
        config_layout.addWidget(QLabel("Objectif:"), 0, 0)
        self.objective_combo = QComboBox()
        self.objective_combo.setMinimumWidth(220)
        self.objective_combo.addItems([
            "Minimiser le coût",
            "Maximiser la couverture"
        ])
        config_layout.addWidget(self.objective_combo, 0, 1)
        
        # Min shift length
        config_layout.addWidget(QLabel("Durée min. quart:"), 1, 0)
        self.min_shift_spin = QSpinBox()
        self.min_shift_spin.setMinimumWidth(220)
        self.min_shift_spin.setRange(2, 8)
        self.min_shift_spin.setValue(4)
        self.min_shift_spin.setSuffix(" heures")
        config_layout.addWidget(self.min_shift_spin, 1, 1)
        
        # Max shift length
        config_layout.addWidget(QLabel("Durée max. quart:"), 2, 0)
        self.max_shift_spin = QSpinBox()
        self.max_shift_spin.setMinimumWidth(220)
        self.max_shift_spin.setRange(4, 12)
        self.max_shift_spin.setValue(8)
        self.max_shift_spin.setSuffix(" heures")
        config_layout.addWidget(self.max_shift_spin, 2, 1)
        
        # Time limit
        config_layout.addWidget(QLabel("Temps limite:"), 3, 0)
        self.time_limit_spin = QSpinBox()
        self.time_limit_spin.setMinimumWidth(220)
        self.time_limit_spin.setRange(10, 300)
        self.time_limit_spin.setValue(60)
        self.time_limit_spin.setSuffix(" secondes")
        config_layout.addWidget(self.time_limit_spin, 3, 1)
        
        # Allow overtime
        self.overtime_check = QCheckBox("Autoriser les heures supplémentaires")
        config_layout.addWidget(self.overtime_check, 4, 0, 1, 2)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Optimize button
        optimize_layout = QHBoxLayout()
        self.optimize_btn = QPushButton("🚀 Optimiser le Planning")
        self.optimize_btn.setObjectName("primaryButton")
        self.optimize_btn.setMinimumHeight(52)
        self.optimize_btn.clicked.connect(self.run_optimization)
        optimize_layout.addWidget(self.optimize_btn)
        layout.addLayout(optimize_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #667eea; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Results section
        results_group = QGroupBox("Résultats")
        results_layout = QVBoxLayout()
        
        # Gantt chart
        self.gantt_chart = ScheduleGanttChart()
        results_layout.addWidget(self.gantt_chart)
        
        # Summary table
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(4)
        self.summary_table.setHorizontalHeaderLabels([
            "Employé", "Horaires", "Heures Total", "Coût"
        ])
        self.summary_table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        header = self.summary_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.summary_table.setMinimumHeight(220)
        results_layout.addWidget(self.summary_table)
        
        # Statistics
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(
            "background-color: #edf2f7; padding: 15px; "
            "border-radius: 8px; color: #2d3748; font-size: 11pt;"
        )
        results_layout.addWidget(self.stats_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
    
    def run_optimization(self):
        """Start optimization process"""
        # Validation
        if len(self.employee_manager) == 0:
            QMessageBox.warning(self, "Erreur", 
                              "Aucun employé défini! Ajoutez des employés d'abord.")
            return
        
        if self.demand_profile.get_total_daily_customers() == 0:
            QMessageBox.warning(self, "Erreur",
                              "Aucune demande définie! Configurez la demande d'abord.")
            return
        
        # Disable button
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Préparation de l'optimisation...")
        
        # Get parameters
        objective_map = {
            "Minimiser le coût": "minimize_cost",
            "Maximiser la couverture": "maximize_coverage"
        }
        
        params = {
            'objective': objective_map[self.objective_combo.currentText()],
            'min_shift_length': self.min_shift_spin.value(),
            'max_shift_length': self.max_shift_spin.value(),
            'allow_overtime': self.overtime_check.isChecked(),
            'time_limit': self.time_limit_spin.value()
        }
        
        # Create scheduler
        employees = self.employee_manager.get_all_employees()
        self.scheduler = ShiftScheduler(employees, self.demand_profile)
        
        # Run in thread
        self.optimization_thread = OptimizationThread(self.scheduler, params)
        self.optimization_thread.finished.connect(self.on_optimization_finished)
        self.optimization_thread.progress.connect(self.on_optimization_progress)
        self.optimization_thread.error.connect(self.on_optimization_error)
        self.optimization_thread.start()
    
    def on_optimization_progress(self, message: str):
        """Update progress message"""
        self.status_label.setText(message)
    
    def on_optimization_finished(self, result: ScheduleResult):
        """Handle optimization completion"""
        self.result = result
        self.progress_bar.setVisible(False)
        self.optimize_btn.setEnabled(True)
        
        if result.status != "Optimal" and result.status != "Time Limit Reached":
            QMessageBox.warning(self, "Attention",
                              f"L'optimisation n'a pas trouvé de solution optimale.\n"
                              f"Status: {result.status}")
            self.status_label.setText(f"❌ {result.status}")
            return
        
        self.status_label.setText(
            f"✅ Optimisation terminée en {result.solve_time:.2f}s | "
            f"Coût total: ${result.total_cost:.2f}"
        )
        
        # Update visualizations
        self.update_gantt_chart()
        self.update_summary_table()
        self.update_statistics()
        
        QMessageBox.information(self, "Succès",
                              f"Planning optimisé avec succès!\n\n"
                              f"Coût total: ${result.total_cost:.2f}\n"
                              f"Temps de calcul: {result.solve_time:.2f}s")
    
    def on_optimization_error(self, error_msg: str):
        """Handle optimization error"""
        self.progress_bar.setVisible(False)
        self.optimize_btn.setEnabled(True)
        self.status_label.setText(f"❌ Erreur: {error_msg}")
        QMessageBox.critical(self, "Erreur d'optimisation", error_msg)
    
    def update_gantt_chart(self):
        """Update Gantt chart with results"""
        self.gantt_chart.set_data(self.result, self.employee_manager, 
                                 self.demand_profile)
    
    def update_summary_table(self):
        """Update summary table with employee assignments"""
        self.summary_table.setRowCount(0)
        
        emp_dict = {emp.id: emp for emp in self.employee_manager.get_all_employees()}
        
        for emp_id, shifts in self.result.schedule.items():
            if shifts and emp_id in emp_dict:
                emp = emp_dict[emp_id]
                row = self.summary_table.rowCount()
                self.summary_table.insertRow(row)
                
                # Name
                self.summary_table.setItem(row, 0, QTableWidgetItem(emp.name))
                
                # Shifts
                shift_str = ", ".join([f"{s}:00-{e}:00" for s, e in shifts])
                self.summary_table.setItem(row, 1, QTableWidgetItem(shift_str))
                
                # Hours
                hours = self.result.total_hours[emp_id]
                self.summary_table.setItem(row, 2, QTableWidgetItem(f"{hours}h"))
                
                # Cost
                cost = hours * emp.hourly_rate
                self.summary_table.setItem(row, 3, QTableWidgetItem(f"${cost:.2f}"))
    
    def update_statistics(self):
        """Update statistics display"""
        total_emp_scheduled = sum(1 for shifts in self.result.schedule.values() if shifts)
        total_emp = len(self.employee_manager)
        total_hours = sum(self.result.total_hours.values())
        avg_hours = total_hours / total_emp_scheduled if total_emp_scheduled > 0 else 0
        
        # Coverage analysis
        required = self.demand_profile.get_all_required_staff()
        coverage = self.result.coverage
        
        shortage_hours = sum(1 for h in coverage if coverage[h] < required[h])
        perfect_hours = sum(1 for h in coverage if coverage[h] == required[h])
        surplus_hours = sum(1 for h in coverage if coverage[h] > required[h])
        
        self.stats_label.setText(
            f"📊 Statistiques du Planning\n\n"
            f"Employés planifiés: {total_emp_scheduled}/{total_emp} | "
            f"Heures totales: {total_hours:.1f}h | "
            f"Moyenne: {avg_hours:.1f}h/employé\n"
            f"Couverture: {perfect_hours}h parfait, "
            f"{shortage_hours}h sous-effectif, "
            f"{surplus_hours}h sur-effectif\n"
            f"Coût total: ${self.result.total_cost:.2f}"
        )