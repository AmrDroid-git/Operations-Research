"""
Demand Profile Tab
UI for configuring hourly customer demand
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QSpinBox, QDoubleSpinBox, QPushButton,
                             QGroupBox, QGridLayout, QComboBox, QMessageBox,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from models.demand import DemandProfile


class DemandBarChart(QWidget):
    """Custom widget to visualize demand as a bar chart"""
    
    def __init__(self, demand_profile: DemandProfile):
        super().__init__()
        self.demand_profile = demand_profile
        self.setMinimumHeight(200)
        
    def set_demand_profile(self, demand_profile: DemandProfile):
        """Update demand profile and redraw"""
        self.demand_profile = demand_profile
        self.update()
    
    def paintEvent(self, event):
        """Draw the bar chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.demand_profile or not self.demand_profile.hourly_demand:
            return
        
        # Get dimensions
        width = self.width()
        height = self.height()
        margin = 40
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        # Get data
        hours = sorted(self.demand_profile.hourly_demand.keys())
        demands = [self.demand_profile.hourly_demand[h] for h in hours]
        max_demand = max(demands) if demands else 1
        
        if max_demand == 0:
            max_demand = 1
        
        bar_width = chart_width / len(hours) * 0.8
        spacing = chart_width / len(hours)
        
        # Draw axes
        painter.setPen(QPen(QColor("#cbd5e0"), 2))
        painter.drawLine(margin, height - margin, width - margin, height - margin)  # X-axis
        painter.drawLine(margin, margin, margin, height - margin)  # Y-axis
        
        # Draw bars
        for i, (hour, demand) in enumerate(zip(hours, demands)):
            bar_height = (demand / max_demand) * chart_height
            x = margin + i * spacing + (spacing - bar_width) / 2
            y = height - margin - bar_height
            
            # Color gradient based on demand level
            if demand < max_demand * 0.3:
                color = QColor("#48bb78")  # Green - low
            elif demand < max_demand * 0.7:
                color = QColor("#ed8936")  # Orange - medium
            else:
                color = QColor("#f56565")  # Red - high
            
            painter.fillRect(int(x), int(y), int(bar_width), int(bar_height), color)
            
            # Draw hour label
            painter.setPen(QColor("#4a5568"))
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(int(x), height - margin + 15, int(bar_width), 20,
                           Qt.AlignmentFlag.AlignCenter, f"{hour}h")
            
            # Draw demand value on top of bar if space allows
            if bar_height > 20:
                painter.setPen(QColor("white"))
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(int(x), int(y) + 5, int(bar_width), 20,
                               Qt.AlignmentFlag.AlignCenter, str(demand))
        
        # Draw Y-axis labels
        painter.setPen(QColor("#4a5568"))
        font = painter.font()
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        
        for i in range(5):
            value = int(max_demand * i / 4)
            y_pos = height - margin - (chart_height * i / 4)
            painter.drawText(5, int(y_pos) - 10, margin - 10, 20,
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           str(value))
        
        # Title
        painter.setPen(QColor("#2d3748"))
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 5, width, 30, Qt.AlignmentFlag.AlignCenter,
                        "Profil de Demande Horaire")


class DemandTab(QWidget):
    """Main demand profile configuration tab"""
    
    demand_changed = pyqtSignal()
    
    def __init__(self, demand_profile: DemandProfile):
        super().__init__()
        self.demand_profile = demand_profile
        self.hour_sliders = {}
        self.hour_spinboxes = {}
        self.init_ui()
        self.load_demand_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Profil de Demande")
        header.setObjectName("tabHeader")
        header_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Configuration section
        config_group = QGroupBox("Configuration du magasin")
        config_layout = QGridLayout()
        
        # Store hours
        config_layout.addWidget(QLabel("Heure d'ouverture:"), 0, 0)
        self.open_hour_spin = QSpinBox()
        self.open_hour_spin.setMinimumWidth(140)
        self.open_hour_spin.setRange(0, 23)
        self.open_hour_spin.setValue(self.demand_profile.store_open_hour)
        self.open_hour_spin.setSuffix(":00")
        self.open_hour_spin.valueChanged.connect(self.update_store_hours)
        config_layout.addWidget(self.open_hour_spin, 0, 1)
        
        config_layout.addWidget(QLabel("Heure de fermeture:"), 0, 2)
        self.close_hour_spin = QSpinBox()
        self.close_hour_spin.setMinimumWidth(140)
        self.close_hour_spin.setRange(1, 24)
        self.close_hour_spin.setValue(self.demand_profile.store_close_hour)
        self.close_hour_spin.setSuffix(":00")
        self.close_hour_spin.valueChanged.connect(self.update_store_hours)
        config_layout.addWidget(self.close_hour_spin, 0, 3)
        
        # Staffing ratio
        config_layout.addWidget(QLabel("Personnel par client:"), 1, 0)
        self.ratio_spin = QDoubleSpinBox()
        self.ratio_spin.setMinimumWidth(140)
        self.ratio_spin.setRange(0.01, 1.0)
        self.ratio_spin.setSingleStep(0.01)
        self.ratio_spin.setDecimals(3)
        self.ratio_spin.setValue(self.demand_profile.staff_per_customer_ratio)
        self.ratio_spin.valueChanged.connect(self.update_ratio)
        config_layout.addWidget(self.ratio_spin, 1, 1)
        
        # Min staff
        config_layout.addWidget(QLabel("Personnel minimum:"), 1, 2)
        self.min_staff_spin = QSpinBox()
        self.min_staff_spin.setMinimumWidth(140)
        self.min_staff_spin.setRange(0, 20)
        self.min_staff_spin.setValue(self.demand_profile.min_staff_per_hour)
        self.min_staff_spin.valueChanged.connect(self.update_min_staff)
        config_layout.addWidget(self.min_staff_spin, 1, 3)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Chart visualization
        self.chart = DemandBarChart(self.demand_profile)
        layout.addWidget(self.chart)
        
        # Pattern selection
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Motif prédéfini:"))
        
        self.pattern_combo = QComboBox()
        self.pattern_combo.setMinimumWidth(200)
        self.pattern_combo.addItems([
            "Personnalisé",
            "Plat",
            "Pic matinal",
            "Pic déjeuner",
            "Pic soirée",
            "Bimodal (déjeuner + soirée)",
            "Week-end"
        ])
        self.pattern_combo.currentTextChanged.connect(self.apply_pattern)
        pattern_layout.addWidget(self.pattern_combo)
        
        scale_btn = QPushButton("Échelle x2")
        scale_btn.setMinimumHeight(40)
        scale_btn.setMinimumWidth(120)
        scale_btn.clicked.connect(lambda: self.scale_demand(2.0))
        pattern_layout.addWidget(scale_btn)
        
        half_btn = QPushButton("Échelle ÷2")
        half_btn.setMinimumHeight(40)
        half_btn.setMinimumWidth(120)
        half_btn.clicked.connect(lambda: self.scale_demand(0.5))
        pattern_layout.addWidget(half_btn)
        
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.setMinimumHeight(40)
        reset_btn.setMinimumWidth(140)
        reset_btn.clicked.connect(self.reset_demand)
        pattern_layout.addWidget(reset_btn)
        
        pattern_layout.addStretch()
        layout.addLayout(pattern_layout)
        
        # Hourly demand controls
        demand_group = QGroupBox("Demande par heure (nombre de clients)")
        
        # Scrollable area for sliders
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizeAdjustPolicy(QScrollArea.SizeAdjustPolicy.AdjustToContents)
        
        scroll_widget = QWidget()
        sliders_layout = QGridLayout(scroll_widget)
        sliders_layout.setSpacing(10)
        
        # Create slider for each hour
        hours = range(self.demand_profile.store_open_hour,
                     self.demand_profile.store_close_hour)
        
        for i, hour in enumerate(hours):
            # Hour label
            hour_label = QLabel(f"{hour}:00")
            hour_label.setMinimumWidth(50)
            sliders_layout.addWidget(hour_label, i, 0)
            
            # Slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 200)
            slider.setValue(0)
            slider.valueChanged.connect(
                lambda val, h=hour: self.update_demand_from_slider(h, val)
            )
            self.hour_sliders[hour] = slider
            sliders_layout.addWidget(slider, i, 1)
            
            # SpinBox
            spinbox = QSpinBox()
            spinbox.setRange(0, 500)
            spinbox.setValue(0)
            spinbox.valueChanged.connect(
                lambda val, h=hour: self.update_demand_from_spinbox(h, val)
            )
            self.hour_spinboxes[hour] = spinbox
            sliders_layout.addWidget(spinbox, i, 2)
            
            # Required staff label
            req_label = QLabel("→ 0 employés")
            req_label.setMinimumWidth(120)
            req_label.setStyleSheet("color: #667eea; font-weight: bold;")
            req_label.setObjectName(f"req_label_{hour}")
            sliders_layout.addWidget(req_label, i, 3)
        
        scroll.setWidget(scroll_widget)
        
        demand_layout = QVBoxLayout()
        demand_layout.addWidget(scroll)
        demand_group.setLayout(demand_layout)
        
        layout.addWidget(demand_group)
        
        # Summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            "background-color: #edf2f7; padding: 10px; "
            "border-radius: 5px; color: #2d3748;"
        )
        layout.addWidget(self.summary_label)
        
        self.update_summary()
    
    def load_demand_data(self):
        """Load demand data into UI controls"""
        for hour in self.hour_sliders:
            demand = self.demand_profile.get_demand(hour)
            self.hour_sliders[hour].setValue(demand)
            self.hour_spinboxes[hour].setValue(demand)
            self.update_required_label(hour)
    
    def update_demand_from_slider(self, hour: int, value: int):
        """Update demand when slider changes"""
        self.hour_spinboxes[hour].blockSignals(True)
        self.hour_spinboxes[hour].setValue(value)
        self.hour_spinboxes[hour].blockSignals(False)
        
        self.demand_profile.set_demand(hour, value)
        self.update_required_label(hour)
        self.update_chart()
        self.update_summary()
        self.demand_changed.emit()
    
    def update_demand_from_spinbox(self, hour: int, value: int):
        """Update demand when spinbox changes"""
        self.hour_sliders[hour].blockSignals(True)
        self.hour_sliders[hour].setValue(value)
        self.hour_sliders[hour].blockSignals(False)
        
        self.demand_profile.set_demand(hour, value)
        self.update_required_label(hour)
        self.update_chart()
        self.update_summary()
        self.demand_changed.emit()
    
    def update_required_label(self, hour: int):
        """Update required staff label for an hour"""
        required = self.demand_profile.calculate_required_staff(hour)
        label = self.findChild(QLabel, f"req_label_{hour}")
        if label:
            label.setText(f"→ {required} employé{'s' if required > 1 else ''}")
    
    def update_store_hours(self):
        """Update store operating hours"""
        try:
            open_h = self.open_hour_spin.value()
            close_h = self.close_hour_spin.value()
            
            if close_h <= open_h:
                QMessageBox.warning(self, "Erreur",
                                  "L'heure de fermeture doit être après l'ouverture!")
                return
            
            self.demand_profile.store_open_hour = open_h
            self.demand_profile.store_close_hour = close_h
            
            # Rebuild UI with new hours
            # For simplicity, just show message
            QMessageBox.information(self, "Info",
                                  "Veuillez redémarrer l'application pour appliquer "
                                  "les nouvelles heures d'ouverture.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
    
    def update_ratio(self):
        """Update staff per customer ratio"""
        self.demand_profile.staff_per_customer_ratio = self.ratio_spin.value()
        for hour in self.hour_sliders:
            self.update_required_label(hour)
        self.update_summary()
        self.demand_changed.emit()
    
    def update_min_staff(self):
        """Update minimum staff requirement"""
        self.demand_profile.min_staff_per_hour = self.min_staff_spin.value()
        for hour in self.hour_sliders:
            self.update_required_label(hour)
        self.update_summary()
        self.demand_changed.emit()
    
    def apply_pattern(self, pattern_name: str):
        """Apply predefined demand pattern"""
        if pattern_name == "Personnalisé":
            return
        
        pattern_map = {
            "Plat": "flat",
            "Pic matinal": "morning_peak",
            "Pic déjeuner": "lunch_peak",
            "Pic soirée": "evening_peak",
            "Bimodal (déjeuner + soirée)": "bimodal",
            "Week-end": "weekend"
        }
        
        if pattern_name in pattern_map:
            self.demand_profile.apply_pattern(pattern_map[pattern_name])
            self.load_demand_data()
            self.update_chart()
            self.update_summary()
            self.demand_changed.emit()
    
    def scale_demand(self, factor: float):
        """Scale all demand values"""
        self.demand_profile.scale_demand(factor)
        self.load_demand_data()
        self.update_chart()
        self.update_summary()
        self.demand_changed.emit()
    
    def reset_demand(self):
        """Reset all demand to zero"""
        for hour in self.hour_sliders:
            self.demand_profile.set_demand(hour, 0)
        self.load_demand_data()
        self.update_chart()
        self.update_summary()
        self.demand_changed.emit()
    
    def update_chart(self):
        """Refresh the demand chart"""
        self.chart.update()
    
    def update_summary(self):
        """Update summary statistics"""
        total_customers = self.demand_profile.get_total_daily_customers()
        avg_demand = self.demand_profile.get_average_hourly_demand()
        required_staff = self.demand_profile.get_all_required_staff()
        total_staff_hours = sum(required_staff.values())
        
        peak_hours = self.demand_profile.get_peak_hours(3)
        peak_text = ", ".join([f"{h}h ({d} clients)" for h, d in peak_hours])
        
        self.summary_label.setText(
            f"📊 Total clients: {total_customers} | "
            f"Moyenne: {avg_demand:.1f}/h | "
            f"Heures personnel requises: {total_staff_hours}h | "
            f"Pics: {peak_text}"
        )