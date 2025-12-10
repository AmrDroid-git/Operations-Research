from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QDate, QTime
from Amr_Work.events_backend import EventsBackend
from Amr_Work.calendar_dialog import CalendarDialog





class AddEventDialog(QtWidgets.QDialog):
    """Small dialog to add a single event for a given date."""

    def __init__(self, date_str: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add Event for {date_str}")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            AddEventDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-size: 13px;
            }
            QLineEdit, QTimeEdit {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
                font-size: 13px;
                selection-background-color: #1976d2;
            }
            QLineEdit:focus, QTimeEdit:focus {
                border: 2px solid #1976d2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                color: #2c3e50;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e9ecef, stop:1 #dee2e6);
                border: 2px solid #1976d2;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Info label with better styling
        info_label = QtWidgets.QLabel(f"Add a new event for date: {date_str}")
        info_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1976d2;")
        layout.addWidget(info_label)

        # Form layout
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # Event name
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setMinimumHeight(35)
        form_layout.addRow("Event name:", self.name_edit)

        # Duration: start & end time
        time_widget = QtWidgets.QWidget()
        time_layout = QtWidgets.QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(12)

        self.start_time_edit = QtWidgets.QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(8, 0))
        self.start_time_edit.setMinimumHeight(35)

        self.end_time_edit = QtWidgets.QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(9, 0))
        self.end_time_edit.setMinimumHeight(35)

        time_layout.addWidget(QtWidgets.QLabel("Start:"))
        time_layout.addWidget(self.start_time_edit)
        time_layout.addWidget(QtWidgets.QLabel("End:"))
        time_layout.addWidget(self.end_time_edit)

        form_layout.addRow("Duration:", time_widget)

        layout.addLayout(form_layout)
        layout.addSpacing(10)

        # Buttons with better styling
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setMinimumHeight(40)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setMinimumHeight(40)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        
        # Style OK button
        ok_button = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
                color: white;
                border: 2px solid #1565c0;
                border-radius: 6px;
                padding: 10px 30px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        
        buttons.accepted.connect(self.handle_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def handle_accept(self):
        """Validate and accept dialog."""
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(
                self,
                "Missing Data",
                "Please enter an event name."
            )
            return

        # (Optional) could also verify start < end here
        self.accept()

    def get_values(self):
        """Return (event_name, start_str, end_str)."""
        name = self.name_edit.text().strip()
        start_str = self.start_time_edit.time().toString("HH:mm")
        end_str = self.end_time_edit.time().toString("HH:mm")
        return name, start_str, end_str


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        
        # ----- Central widget -----
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Global style with enhanced modern design
        self.centralwidget.setStyleSheet("""
            #leftMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
                border-right: 4px solid #0d47a1;
            }
            #mainBody {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #ffffff);
            }
            #logoFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.2), stop:1 rgba(255, 255, 255, 0.1));
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 15px;
            }
            #logoText {
                background: transparent;
                border: none;
                color: white;
            }
            #leftMenu QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15), stop:1 rgba(255, 255, 255, 0.08));
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.25);
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 20px;
            }
            #leftMenu QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25), stop:1 rgba(255, 255, 255, 0.15));
                border: 2px solid rgba(255, 255, 255, 0.5);
                margin-left: 3px;
                margin-right: -3px;
            }
            #leftMenu QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
                margin-left: 0px;
                margin-right: 0px;
            }
            #dateDisplay {
                background-color: white;
                border: 3px solid #1976d2;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                color: #1976d2;
                min-width: 140px;
                max-width: 140px;
            }
            #mainBody QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                color: #2c3e50;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 600;
                min-height: 38px;
            }
            #mainBody QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f0f0, stop:1 #e8e8e8);
                border: 2px solid #1976d2;
                color: #1976d2;
            }
            #mainBody QPushButton:pressed {
                background-color: #d8d8d8;
            }
            #pushButton_3 {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
                color: white;
                border: 2px solid #1565c0;
            }
            #pushButton_3:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
            }
            #pushButton_2 {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388e3c);
                color: white;
                border: 2px solid #388e3c;
            }
            #pushButton_2:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #4CAF50);
            }
            #pushButton_delete_selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff9800, stop:1 #f57c00);
                color: white;
                border: 2px solid #f57c00;
            }
            #pushButton_delete_selected:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffb74d, stop:1 #ff9800);
            }
            #pushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f44336, stop:1 #d32f2f);
                color: white;
                border: 2px solid #c62828;
            }
            #pushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef5350, stop:1 #f44336);
            }
            QTableWidget {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: white;
                gridline-color: #f0f0f0;
                selection-background-color: #e3f2fd;
                selection-color: #1976d2;
            }
            QTableWidget::item {
                padding: 12px 10px;
                border-bottom: 1px solid #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #eef2f5);
                padding: 13px 10px;
                border: none;
                border-bottom: 4px solid #1976d2;
                border-right: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
                border-right: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #bdbdbd;
                min-height: 25px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #1976d2;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            #creditsFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15), stop:1 rgba(255, 255, 255, 0.05));
                border: 2px solid rgba(255, 255, 255, 0.25);
                border-radius: 10px;
            }
            #creditsLabel {
                color: white;
                font-size: 12px;
                font-weight: 500;
                padding: 10px;
            }
            #creditsLabel:hover {
                color: #e3f2fd;
            }
            #buttonsFrame {
                background-color: transparent;
            }
        """)
        
        # Main layout
        self.fullWindow = QtWidgets.QHBoxLayout(self.centralwidget)
        self.fullWindow.setContentsMargins(0, 0, 0, 0)
        self.fullWindow.setSpacing(0)
        self.fullWindow.setObjectName("fullWindow")
        
        # ----- Left menu -----
        self.leftMenu = QtWidgets.QWidget()
        self.leftMenu.setObjectName("leftMenu")
        self.leftMenu.setMinimumWidth(200)
        self.leftMenu.setMaximumWidth(240)
        
        self.leftMenuLayout = QtWidgets.QVBoxLayout(self.leftMenu)
        self.leftMenuLayout.setContentsMargins(15, 20, 15, 20)
        self.leftMenuLayout.setSpacing(12)
        
        # Logo frame
        self.frame = QtWidgets.QFrame()
        self.frame.setObjectName("logoFrame")
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setMinimumHeight(110)
        self.frame.setMaximumHeight(130)
        
        self.logoLayout = QtWidgets.QVBoxLayout(self.frame)
        self.logoLayout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QtWidgets.QTextEdit()
        self.label.setObjectName("logoText")
        self.label.setHtml("""
            <div style="text-align: center; font-size: 18px; font-weight: bold; 
                        color: white; line-height: 1.4; font-family: 'Segoe UI', Arial;">
                📅<br>Events<br>Management
            </div>
        """)
        self.label.setReadOnly(True)
        self.label.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.label.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.label.setFixedHeight(90)
        self.logoLayout.addWidget(self.label)
        
        # Buttons frame
        self.frame_2 = QtWidgets.QFrame()
        self.frame_2.setObjectName("buttonsFrame")
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        
        self.buttonsLayout = QtWidgets.QVBoxLayout(self.frame_2)
        self.buttonsLayout.setContentsMargins(0, 8, 0, 8)
        self.buttonsLayout.setSpacing(8)
        
        self.pushButton_4 = QtWidgets.QPushButton()
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_4.setMinimumHeight(40)
        self.pushButton_4.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttonsLayout.addWidget(self.pushButton_4)
        
        self.pushButton_7 = QtWidgets.QPushButton()
        self.pushButton_7.setObjectName("pushButton_7")
        self.pushButton_7.setMinimumHeight(40)
        self.pushButton_7.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttonsLayout.addWidget(self.pushButton_7)
        
        self.pushButton_6 = QtWidgets.QPushButton()
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_6.setMinimumHeight(40)
        self.pushButton_6.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttonsLayout.addWidget(self.pushButton_6)
        
        self.pushButton_5 = QtWidgets.QPushButton()
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_5.setMinimumHeight(40)
        self.pushButton_5.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttonsLayout.addWidget(self.pushButton_5)
        
        self.pushButton_8 = QtWidgets.QPushButton()
        self.pushButton_8.setObjectName("pushButton_8")
        self.pushButton_8.setMinimumHeight(40)
        self.pushButton_8.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttonsLayout.addWidget(self.pushButton_8)
        
        self.pushButton_9 = QtWidgets.QPushButton()
        self.pushButton_9.setObjectName("pushButton_9")
        self.pushButton_9.setMinimumHeight(40)
        self.pushButton_9.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttonsLayout.addWidget(self.pushButton_9)
        
        self.buttonsLayout.addStretch()
        
        # Credits frame
        self.creditsFrame = QtWidgets.QFrame()
        self.creditsFrame.setObjectName("creditsFrame")
        self.creditsFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.creditsFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        
        self.creditsLayout = QtWidgets.QVBoxLayout(self.creditsFrame)
        self.creditsLayout.setContentsMargins(12, 12, 12, 12)
        
        self.label_2 = QtWidgets.QLabel()
        self.label_2.setObjectName("creditsLabel")
        self.label_2.setText(
            '<a href="https://github.com/AmrDroid-git" style="color: white; text-decoration: none;">'
            '💻 Created By AmrDroid</a>'
        )
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.creditsLayout.addWidget(self.label_2)
        
        self.leftMenuLayout.addWidget(self.frame)
        self.leftMenuLayout.addWidget(self.frame_2)
        self.leftMenuLayout.addStretch()
        self.leftMenuLayout.addWidget(self.creditsFrame)
        
        # ----- Main body -----
        self.mainBody = QtWidgets.QWidget()
        self.mainBody.setObjectName("mainBody")
        
        self.mainBodyLayout = QtWidgets.QVBoxLayout(self.mainBody)
        self.mainBodyLayout.setContentsMargins(25, 25, 25, 25)
        self.mainBodyLayout.setSpacing(15)
        
        # Top bar: date + buttons
        self.buttons_Add_Delete_refresh = QtWidgets.QHBoxLayout()
        self.buttons_Add_Delete_refresh.setSpacing(10)
        
        self.date_display = QtWidgets.QLineEdit()
        self.date_display.setObjectName("dateDisplay")
        self.date_display.setFixedWidth(150)
        self.date_display.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.date_display.setReadOnly(True)
        self.buttons_Add_Delete_refresh.addWidget(self.date_display)
        
        self.pushButton_3 = QtWidgets.QPushButton()
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_3.setMinimumWidth(110)
        self.pushButton_3.setMinimumHeight(38)
        self.pushButton_3.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttons_Add_Delete_refresh.addWidget(self.pushButton_3)
        
        self.pushButton_2 = QtWidgets.QPushButton()
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setMinimumWidth(120)
        self.pushButton_2.setMinimumHeight(38)
        self.pushButton_2.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttons_Add_Delete_refresh.addWidget(self.pushButton_2)

        # ⭐ NEW BUTTON: Delete Selected Event (inserted before Delete All)
        self.pushButton_delete_selected = QtWidgets.QPushButton()
        self.pushButton_delete_selected.setObjectName("pushButton_delete_selected")
        self.pushButton_delete_selected.setMinimumWidth(160)
        self.pushButton_delete_selected.setMinimumHeight(38)
        self.pushButton_delete_selected.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttons_Add_Delete_refresh.addWidget(self.pushButton_delete_selected)
        
        self.pushButton = QtWidgets.QPushButton()
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setMinimumWidth(150)
        self.pushButton.setMinimumHeight(38)
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.buttons_Add_Delete_refresh.addWidget(self.pushButton)
        
        self.buttons_Add_Delete_refresh.addStretch()
        
        # Table
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget.setShowGrid(True)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setMinimumHeight(300)
        
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        self.tableWidget.setColumnWidth(0, 200)
        self.tableWidget.setColumnWidth(1, 120)
        self.tableWidget.setColumnWidth(2, 100)
        
        self.mainBodyLayout.addLayout(self.buttons_Add_Delete_refresh)
        self.mainBodyLayout.addWidget(self.tableWidget)
        
        # Put both sides into main layout
        self.fullWindow.addWidget(self.leftMenu, 1)
        self.fullWindow.addWidget(self.mainBody, 4)
        
        MainWindow.setCentralWidget(self.centralwidget)

        # Translate texts
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # ---- Extra setup (logic) ----
        self.update_date_display(QDate.currentDate())
        self.events_backend = EventsBackend()
        self.connect_signals()
        self.load_events_for_current_date()
    
    # ------------------------------------------------------------------
    # Texts
    # ------------------------------------------------------------------
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Events Management System"))
        
        self.pushButton_4.setText(_translate("MainWindow", "📅 Open Calendar"))
        self.pushButton_5.setText(_translate("MainWindow", "📍 Today"))
        self.pushButton_6.setText(_translate("MainWindow", "➡️ Tomorrow"))
        self.pushButton_7.setText(_translate("MainWindow", "⏩ Overmorrow"))
        self.pushButton_8.setText(_translate("MainWindow", "⬅️ Yesterday"))
        self.pushButton_9.setText(_translate("MainWindow", "⏪ Two Days Ago"))
        self.pushButton_3.setText(_translate("MainWindow", "🔄 Refresh"))
        self.pushButton_2.setText(_translate("MainWindow", "➕ Add Events"))

        # Text for new button
        self.pushButton_delete_selected.setText(_translate("MainWindow", "🗑️ Delete Selected"))

        self.pushButton.setText(_translate("MainWindow", "🗑️ Delete All Events"))
        
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Event"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Duration"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Class"))
    
    # ------------------------------------------------------------------
    # Logic helpers
    # ------------------------------------------------------------------
    def connect_signals(self):
        """Connect all signals and slots."""
        # Date navigation + calendar
        self.pushButton_4.clicked.connect(self.show_calendar_dialog)
        self.pushButton_5.clicked.connect(lambda: self.set_date_and_load(0))   # Today
        self.pushButton_6.clicked.connect(lambda: self.set_date_and_load(1))   # Tomorrow
        self.pushButton_7.clicked.connect(lambda: self.set_date_and_load(2))   # Overmorrow
        self.pushButton_8.clicked.connect(lambda: self.set_date_and_load(-1))  # Yesterday
        self.pushButton_9.clicked.connect(lambda: self.set_date_and_load(-2))  # Two days ago
        
        # Refresh table
        self.pushButton_3.clicked.connect(self.solve_and_assign_classes_for_day)
        
        # Add events
        self.pushButton_2.clicked.connect(self.handle_add_event_clicked)

        # Delete selected event
        self.pushButton_delete_selected.clicked.connect(self.delete_selected_event)
        
        # Delete all events for current date
        self.pushButton.clicked.connect(self.delete_all_events_for_current_date)
    
    def update_date_display(self, date: QDate):
        """Update the date display in yyyy-MM-dd format."""
        self.date_display.setText(date.toString("yyyy-MM-dd"))
    
    def set_date_and_load(self, days: int):
        """Set date relative to today and load events."""
        new_date = QDate.currentDate().addDays(days)
        self.update_date_display(new_date)
        self.load_events_for_current_date()
    
    def load_events_for_current_date(self):
        """Load and display events for the current date in the display."""
        date_str = self.date_display.text()
        if not date_str:
            self.update_date_display(QDate.currentDate())
            date_str = self.date_display.text()
        
        count = self.events_backend.populate_table(self.tableWidget, date_str)
        print(f"Loaded {count} events for {date_str}")
    
    def refresh_events_display(self):
        self.load_events_for_current_date()
    
    def delete_all_events_for_current_date(self):
        date_str = self.date_display.text()
        if not date_str:
            return

        # --- CONFIRMATION POPUP ---
        reply = QtWidgets.QMessageBox.question(
            None,
            "Confirm Delete",
            f"Are you sure you want to delete ALL events for this date?\n\n{date_str}",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        # If user clicked NO → stop here
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # If user clicked YES → delete
        self.events_backend.delete_all_events_for_date(date_str)
        self.load_events_for_current_date()

    # ------------------------------------------------------------------
    # Delete single selected event
    # ------------------------------------------------------------------
    def delete_selected_event(self):
        """Delete the currently selected event (row) from table and JSON."""
        row = self.tableWidget.currentRow()

        if row < 0:
            QtWidgets.QMessageBox.warning(
                None,
                "No Event Selected",
                "Please select an event from the table first."
            )
            return

        item_event = self.tableWidget.item(row, 0)
        item_duration = self.tableWidget.item(row, 1)
        item_class = self.tableWidget.item(row, 2)

        event_name = item_event.text() if item_event else ""
        duration = item_duration.text() if item_duration else ""
        class_name = item_class.text() if item_class else ""
        date_str = self.date_display.text()

        # Confirmation popup with full message
        reply = QtWidgets.QMessageBox.question(
            None,
            "Confirm Delete Event",
            f"Are you sure you want to delete the event \"{event_name}\" "
            f"with duration \"{duration}\" for day \"{date_str}\" in class \"{class_name}\"?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Remove from backend JSON data
        events = self.events_backend.all_events_data.get(date_str, [])
        for idx, e in enumerate(events):
            if (
                e.get("event") == event_name and
                e.get("duration") == duration and
                e.get("class") == class_name
            ):
                del events[idx]
                break

        self.events_backend.save_json_data()

        # Remove row from table
        self.tableWidget.removeRow(row)
    
    # ------------------------------------------------------------------
    # Add Event button handler (NEW)
    # ------------------------------------------------------------------
    def handle_add_event_clicked(self):
        """Open dialog to add a new event for the current date."""
        date_str = self.date_display.text()
        if not date_str:
            QtWidgets.QMessageBox.warning(
                None,
                "No Date Selected",
                "Please select a date first."
            )
            return

        dialog = AddEventDialog(date_str, self.mainBody)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            event_name, start_str, end_str = dialog.get_values()
            duration = f"{start_str} -> {end_str}"

            # Save in JSON with class "A null"
            self.events_backend.add_event(date_str, event_name, duration, "A null")

            # Reload table
            self.load_events_for_current_date()
    
    # ------------------------------------------------------------------
    # Calendar integration
    # ------------------------------------------------------------------
    def show_calendar_dialog(self):
        """Open the calendar dialog and react to the selected date."""
        current_date = QDate.fromString(self.date_display.text(), "yyyy-MM-dd")
        if not current_date.isValid():
            current_date = QDate.currentDate()
        
        dialog = CalendarDialog(self.mainBody, current_date)
        dialog.date_selected.connect(self.handle_calendar_date_selected)
        dialog.exec()
    
    def handle_calendar_date_selected(self, selected_date: QDate):
        """Update date and reload events after calendar selection."""
        self.update_date_display(selected_date)
        self.load_events_for_current_date()


    def solve_and_assign_classes_for_day(self):
        """Solve time conflicts and assign new classes A1, A2, ... for this day."""
        
        date_str = self.date_display.text()
        if not date_str:
                    return

        events = self.events_backend.all_events_data.get(date_str, [])

        if not events:
                    QtWidgets.QMessageBox.information(
                            None,
                            "No Events",
                            "No events found for this day to solve."
                    )
                    return

        # ---------------------------------------------------------
        # 1. Convert "HH:mm -> HH:mm" into numeric intervals
        # ---------------------------------------------------------
        def parse_time(t):
                    h, m = t.split(":")
                    return int(h) + int(m) / 60

        event_times = {}
        for e in events:
                    start_str, end_str = e["duration"].split(" -> ")
                    start = parse_time(start_str)
                    end = parse_time(end_str)
                    event_times[e["event"]] = (start, end)

        V = list(event_times.keys())

        # ---------------------------------------------------------
        # 2. Build conflict graph
        # ---------------------------------------------------------
        def overlap(ev1, ev2):
                    s1, e1 = ev1
                    s2, e2 = ev2
                    return (s1 < e2) and (s2 < e1)

        E = []
        from itertools import combinations
        for u, v in combinations(V, 2):
                    if overlap(event_times[u], event_times[v]):
                            E.append((u, v))

        # ---------------------------------------------------------
        # 3. Greedy Graph Coloring (no Gurobi required)
        # ---------------------------------------------------------
        colors = {}   # event -> color index

        for v in V:
                    forbidden = set()
                    for (u, w) in E:
                            if u == v and w in colors:
                                        forbidden.add(colors[w])
                            if w == v and u in colors:
                                        forbidden.add(colors[u])

                    c = 0
                    while c in forbidden:
                            c += 1

                    colors[v] = c

        # ---------------------------------------------------------
        # 4. Convert colors to classes A1, A2, A3 ...
        # ---------------------------------------------------------
        color_to_class = {}
        for c in set(colors.values()):
                    color_to_class[c] = f"A{c + 1}"

        # ---------------------------------------------------------
        # 5. Write new classes back into JSON
        # ---------------------------------------------------------
        for e in events:
                    e["class"] = color_to_class[colors[e["event"]]]

        self.events_backend.all_events_data[date_str] = events
        self.events_backend.save_json_data()

        # ---------------------------------------------------------
        # 6. Reload table
        # ---------------------------------------------------------
        self.load_events_for_current_date()

        QtWidgets.QMessageBox.information(
                    None,
                    "Solved",
                    "Classes were reassigned successfully using conflict solving."
        )









# Optional: entry point to run directly
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    MainWindow.showMaximized()   # or showFullScreen()

    sys.exit(app.exec())