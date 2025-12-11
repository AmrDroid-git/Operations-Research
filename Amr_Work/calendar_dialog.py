from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QDate, pyqtSignal, Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel


class ModernCalendarDialog(QtWidgets.QDialog):
    """Modern calendar dialog with improved design."""
    
    date_selected = pyqtSignal(QDate)
    
    def __init__(self, parent=None, current_date=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date")
        self.setModal(True)
        self.setMinimumSize(450, 400)
        
        self.selected_date = current_date if current_date else QDate.currentDate()
        
        # slight drop shadow for dialog to float above content
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 8)
        shadow.setColor(QtGui.QColor(10, 25, 55, 90))
        self.setGraphicsEffect(shadow)
        
        # stronger header font for clarity
        self._header_font = QtGui.QFont("Segoe UI", 12, QtGui.QFont.Weight.DemiBold)
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header label
        self.date_label = QLabel(self.selected_date.toString("dddd, MMMM d, yyyy"))
        self.date_label.setFont(getattr(self, "_header_font", QtGui.QFont("Segoe UI", 12)))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setObjectName("dateLabel")
        main_layout.addWidget(self.date_label)
        
        # Calendar
        self.calendar = QtWidgets.QCalendarWidget()
        self.calendar.setSelectedDate(self.selected_date)
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(
            QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.calendar.clicked.connect(self.on_date_clicked)
        main_layout.addWidget(self.calendar)
        
        # Quick buttons
        quick_buttons_layout = QHBoxLayout()
        quick_buttons_layout.setSpacing(10)
        
        today_btn = QPushButton("Today")
        today_btn.setObjectName("quickButton")
        today_btn.clicked.connect(self.select_today)
        
        yesterday_btn = QPushButton("Yesterday")
        yesterday_btn.setObjectName("quickButton")
        yesterday_btn.clicked.connect(self.select_yesterday)
        
        tomorrow_btn = QPushButton("Tomorrow")
        tomorrow_btn.setObjectName("quickButton")
        tomorrow_btn.clicked.connect(self.select_tomorrow)
        
        quick_buttons_layout.addWidget(yesterday_btn)
        quick_buttons_layout.addWidget(today_btn)
        quick_buttons_layout.addWidget(tomorrow_btn)
        main_layout.addLayout(quick_buttons_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        
        select_btn = QPushButton("Select Date")
        select_btn.setObjectName("selectButton")
        select_btn.setDefault(True)
        select_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(select_btn)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            
            #dateLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1e293b;
                padding: 15px;
                background-color: white;
                border-radius: 10px;
                border: 2px solid #e2e8f0;
            }
            
            QCalendarWidget {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 10px;
            }
            
            QCalendarWidget QToolButton {
                background-color: transparent;
                color: #1e293b;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QCalendarWidget QToolButton:hover {
                background-color: #f1f5f9;
            }
            
            QCalendarWidget QToolButton:pressed {
                background-color: #e2e8f0;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                color: #1e293b;
                background-color: white;
                selection-background-color: #3b82f6;
                selection-color: white;
                font-size: 13px;
            }
            
            QCalendarWidget QAbstractItemView:disabled {
                color: #cbd5e1;
            }
            
            #quickButton {
                background-color: white;
                color: #475569;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            
            #quickButton:hover {
                background-color: #f1f5f9;
                border-color: #cbd5e1;
            }
            
            #quickButton:pressed {
                background-color: #e2e8f0;
            }
            
            #selectButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-weight: 600;
                font-size: 14px;
            }
            
            #selectButton:hover {
                background-color: #2563eb;
            }
            
            #selectButton:pressed {
                background-color: #1d4ed8;
            }
            
            #cancelButton {
                background-color: white;
                color: #64748b;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 30px;
                font-weight: 600;
                font-size: 14px;
            }
            
            #cancelButton:hover {
                background-color: #f8fafc;
                border-color: #cbd5e1;
            }
        """)
    
    def on_date_clicked(self, date: QDate):
        self.selected_date = date
        self.date_label.setText(date.toString("dddd, MMMM d, yyyy"))
    
    def select_today(self):
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.on_date_clicked(today)
    
    def select_yesterday(self):
        yesterday = QDate.currentDate().addDays(-1)
        self.calendar.setSelectedDate(yesterday)
        self.on_date_clicked(yesterday)
    
    def select_tomorrow(self):
        tomorrow = QDate.currentDate().addDays(1)
        self.calendar.setSelectedDate(tomorrow)
        self.on_date_clicked(tomorrow)
    
    def accept(self):
        self.selected_date = self.calendar.selectedDate()
        self.date_selected.emit(self.selected_date)
        super().accept()
    
    def get_selected_date(self) -> QDate:
        return self.calendar.selectedDate()


class CalendarDialog(ModernCalendarDialog):
    """Thin alias for backwards compatibility."""
    pass
