from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QDate, QTime
from Amr_Work.events_backend import EventsBackend
from Amr_Work.calendar_dialog import CalendarDialog
from gurobipy import Model, GRB, quicksum



class AddEventDialog(QtWidgets.QDialog):
    """Small dialog to add a single event for a given date."""

    def __init__(self, date_str: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add Event for {date_str}")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        info_label = QtWidgets.QLabel(f"Add a new event for date: {date_str}")
        info_label.setStyleSheet("font-weight:600; color:#1976d2;")
        layout.addWidget(info_label)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setMinimumHeight(32)
        form_layout.addRow("Event name:", self.name_edit)

        time_widget = QtWidgets.QWidget()
        time_layout = QtWidgets.QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)

        self.start_time_edit = QtWidgets.QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")
        self.start_time_edit.setTime(QTime(8, 0))
        self.end_time_edit = QtWidgets.QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")
        self.end_time_edit.setTime(QTime(9, 0))

        time_layout.addWidget(QtWidgets.QLabel("Start:"))
        time_layout.addWidget(self.start_time_edit)
        time_layout.addWidget(QtWidgets.QLabel("End:"))
        time_layout.addWidget(self.end_time_edit)

        form_layout.addRow("Duration:", time_widget)
        layout.addLayout(form_layout)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.handle_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def handle_accept(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Missing Data", "Please enter an event name.")
            return
        self.accept()

    def get_values(self):
        name = self.name_edit.text().strip()
        start_str = self.start_time_edit.time().toString("HH:mm")
        end_str = self.end_time_edit.time().toString("HH:mm")
        return name, start_str, end_str

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        # Set a clean system font application-wide for a modern look
        QtWidgets.QApplication.setFont(QtGui.QFont("Segoe UI", 10))
        # Optional: enable AA_UseHighDpiPixmaps if available (safe).
        # Different PyQt6/PySide6 builds expose the flag under
        # either `Qt.AA_UseHighDpiPixmaps` or `Qt.ApplicationAttribute.AA_UseHighDpiPixmaps`.
        # Try both and ignore if unavailable.
        try:
            QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        except Exception:
            try:
                QtWidgets.QApplication.setAttribute(
                    QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
                )
            except Exception:
                pass

        # ----- Central widget -----
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.centralwidget.setStyleSheet("""
            /* High-Contrast Accessible Theme (Light) */
            QWidget { background: #ffffff; }

            /* Left menu: charcoal with white text */
            #leftMenu {
                background: #111827; /* charcoal */
                border-right: 1px solid rgba(0,0,0,0.08);
            }
            /* Logo frame: light card with left accent bar and soft gradient */
            #logoFrame {
                border-radius: 12px;
                padding: 14px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fbfdff, stop:1 #ffffff);
                border: 1px solid rgba(11,18,26,0.06);
                border-left: 6px solid #0b61d8; /* accent bar */
            }
            #logoText { color: #07121a; font-weight: 900; font-size: 18px; padding: 6px 8px; }
            /* Small menu icon button inside logo frame */
            #menuButton {
                background: #0b61d8;
                color: #ffffff;
                border-radius: 8px;
                font-weight: 900;
                font-size: 20px;
                border: none;
                min-width: 44px;
                min-height: 44px;
            }
            #menuButton:hover { background: #2b78f0; }

            /* Left menu buttons - white tiles with dark text for readability */
            #leftMenu QPushButton {
                background: #ffffff;
                color: #07121a;
                border: 1px solid rgba(11,18,26,0.06);
                text-align: left;
                padding: 10px 14px;
                font-size: 15px;
                font-weight: 800;
                border-radius: 8px;
                margin: 6px 6px; /* spacing between buttons */
            }
            #leftMenu QPushButton:hover {
                background: #f3f4f6;
                border: 1px solid rgba(11,18,26,0.12);
            }

            /* Strong explicit nav button style (keeps text readable) */
            #pushButton_5, #pushButton_6, #pushButton_7, #pushButton_8, #pushButton_9 {
                background: transparent;
                color: #ffffff;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 15px;
                font-weight: 800;
                text-align: left;
            }
            #pushButton_5:hover, #pushButton_6:hover, #pushButton_7:hover, #pushButton_8:hover, #pushButton_9:hover {
                background: rgba(255,255,255,0.08);
            }

            /* Calendar button: bold orange tile with dark text for accessibility */
            #pushButton_4 {
                background: #ff7a00; /* orange */
                color: #07121a; /* very dark for contrast */
                border-radius: 10px;
                padding: 8px 10px;
                font-weight: 900;
                font-size: 14px;
            }
            #pushButton_4:hover { background: #ff912b; }

            /* Main body */
            #mainBody { background: transparent; }

            /* Date display: white card with strong border for visibility */
            #dateDisplay {
                background-color: #ffffff;
                border: 2px solid #0b1726;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 900;
                color: #0b1726;
            }

            /* Main action buttons: distinct accessible accents */
            #mainBody QPushButton {
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 800;
                color: #ffffff;
                border: none;
                font-size: 13px;
            }
            /* Refresh: blue */
            #pushButton_3 { background: #0b61d8; }
            #pushButton_3:hover { background: #2b78f0; }
            /* Add Events: green */
            #pushButton_2 { background: #16a34a; }
            #pushButton_2:hover { background: #3ac06b; }
            /* Delete Selected: orange tile but with dark text */
            #pushButton_delete_selected { background: #ff7a00; color: #07121a; }
            #pushButton_delete_selected:hover { background: #ff912b; }
            /* Delete All: red */
            #pushButton { background: #ef4444; }
            #pushButton:hover { background: #f87171; }

            /* Table - refined appearance */
            QTableWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #ffffff, stop:1 #fbfdff);
                border-radius: 12px;
                padding: 6px;
                gridline-color: rgba(11,18,26,0.04);
                color: #0b1726;
            }
            QTableWidget::item {
                padding: 14px 12px;
                border-bottom: 1px solid rgba(11,18,26,0.04);
            }
            QTableWidget::item:hover {
                background: #f8fafc;
            }
            QTableWidget::item:selected {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #fde68a, stop:1 #fcd34d);
                color: #07121a;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f1f5f9, stop:1 #e6eef8);
                color: #0b1726;
                padding: 12px 10px;
                font-weight: 900;
                border: none;
                border-bottom: 1px solid rgba(11,18,26,0.06);
                text-transform: none;
            }
            QTableCornerButton::section { background: transparent; }

            /* Credits link in left menu */
            #creditsLabel { color: #cfe8ff; font-weight: 700; }
            #creditsLabel a { color: #cfe8ff; text-decoration: none; }

            /* Focus outlines for keyboard users */
            QPushButton:focus, QLineEdit:focus, QTableWidget:focus { outline: 3px solid rgba(11,23,38,0.12); }
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
        self.frame.setMinimumHeight(120)
        self.frame.setMaximumHeight(160)

        self.logoLayout = QtWidgets.QVBoxLayout(self.frame)
        self.logoLayout.setContentsMargins(12, 12, 12, 12)

        # Replace logo label with a compact menu icon button to indicate the sidebar
        self.menuButton = QtWidgets.QPushButton()
        self.menuButton.setObjectName("menuButton")
        self.menuButton.setText("☰")
        self.menuButton.setToolTip("Menu")
        self.menuButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.menuButton.setFixedSize(48, 48)
        self.menuButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # center the button in the logo frame
        self.logoLayout.addStretch()
        self.logoLayout.addWidget(self.menuButton, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.logoLayout.addStretch()

        # subtle shadow under logo frame to add depth
        logo_shadow = QtWidgets.QGraphicsDropShadowEffect(self.frame)
        logo_shadow.setBlurRadius(28)
        logo_shadow.setOffset(0, 8)
        logo_shadow.setColor(QtGui.QColor(3, 18, 36, 90))
        self.frame.setGraphicsEffect(logo_shadow)

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
        self.pushButton_4.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.buttonsLayout.addWidget(self.pushButton_4)

        self.pushButton_7 = QtWidgets.QPushButton()
        self.pushButton_7.setObjectName("pushButton_7")
        self.pushButton_7.setMinimumHeight(40)
        self.pushButton_7.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_7.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.buttonsLayout.addWidget(self.pushButton_7)

        self.pushButton_6 = QtWidgets.QPushButton()
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_6.setMinimumHeight(40)
        self.pushButton_6.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_6.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.buttonsLayout.addWidget(self.pushButton_6)

        self.pushButton_5 = QtWidgets.QPushButton()
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_5.setMinimumHeight(40)
        self.pushButton_5.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_5.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.buttonsLayout.addWidget(self.pushButton_5)

        self.pushButton_8 = QtWidgets.QPushButton()
        self.pushButton_8.setObjectName("pushButton_8")
        self.pushButton_8.setMinimumHeight(40)
        self.pushButton_8.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_8.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.buttonsLayout.addWidget(self.pushButton_8)

        self.pushButton_9 = QtWidgets.QPushButton()
        self.pushButton_9.setObjectName("pushButton_9")
        self.pushButton_9.setMinimumHeight(40)
        self.pushButton_9.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_9.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
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
        # Text/links styled via stylesheet for consistency
        self.label_2.setText('<a href="https://github.com/AmrDroid-git">💻 Created By AmrDroid</a>')
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

        # Make table rows and headers visually nicer
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setDefaultSectionSize(46)
        header.setMinimumHeight(48)
        header.setStretchLastSection(True)
        self.tableWidget.setWordWrap(False)

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
                None, "No Events", "No events found for this day to solve."
            )
            return

        # ---------- 1. parse durations -> numeric intervals ----------
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

        # ---------- 2. build conflict graph ----------
        def overlap(ev1, ev2):
            s1, e1 = ev1
            s2, e2 = ev2
            return (s1 < e2) and (s2 < e1)

        E = []
        from itertools import combinations
        for u, v in combinations(V, 2):
            if overlap(event_times[u], event_times[v]):
                E.append((u, v))

        # ---------- 3. OPTIMAL colouring with Gurobi ----------
        K = len(V)  # upper bound on colours
        m = Model("colour")
        m.Params.OutputFlag = 0  # silent

        # x[v,k] = 1 if vertex v gets colour k
        x = m.addVars(V, range(K), vtype=GRB.BINARY, name="x")
        # y[k] = 1 if colour k is used
        y = m.addVars(range(K), vtype=GRB.BINARY, name="y")

        # each event gets exactly one colour
        m.addConstrs((quicksum(x[v, k] for k in range(K)) == 1 for v in V), name="assign")

        # link x to y
        m.addConstrs((x[v, k] <= y[k] for v in V for k in range(K)), name="link")

        # adjacent vertices cannot share a colour
        for u, v in E:
            for k in range(K):
                m.addConstr(x[u, k] + x[v, k] <= y[k], name=f"conflict_{u}_{v}_{k}")

        m.setObjective(quicksum(y[k] for k in range(K)), GRB.MINIMIZE)
        m.optimize()

        # ---------- 4. read solution ----------
        colours = {}
        for v in V:
            colours[v] = next(k for k in range(K) if x[v, k].X > 0.5)

        # ---------- 5. map colours -> class labels ----------
        # Create mapping from used colors (0, 1, 2, ...) to class labels (A1, A2, A3, ...)
        used_colors = sorted(set(c for c in range(K) if y[c].X > 0.5))
        colour_to_class = {used_colors[i]: f"A{i+1}" for i in range(len(used_colors))}

        for e in events:
            e["class"] = colour_to_class[colours[e["event"]]]

        # ---------- 6. save & reload ----------
        self.events_backend.all_events_data[date_str] = events
        self.events_backend.save_json_data()
        self.load_events_for_current_date()

        QtWidgets.QMessageBox.information(
            None, "Solved", "Classes were reassigned successfully using conflict solving."
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