# main_launcher.py
import sys
import os
from PyQt6 import QtWidgets, QtCore, QtGui
from Amr_Work.AmrMainWindow import Ui_MainWindow
from pathlib import Path
from PyQt6 import QtGui

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


class AmrWorkWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """Concrete window that your AmrMainWindow.ui describes."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class Launcher(QtWidgets.QMainWindow):
    """Main entry window – 5 buttons with beautiful modern design."""
    def __init__(self):
        super().__init__()
        ICON_LAUNCHER = QtGui.QIcon(str(Path(__file__).with_name("templates") / "main-icon.ico"))
        self.setWindowTitle("Full-Team Project Launcher")
        self.resize(900, 650)
        
        # Modern Material Design color scheme
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #ffffff);
            }
        """)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        self.setWindowIcon(ICON_LAUNCHER)

        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(30)

        # Header container with gradient
        header_container = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        header_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976d2, stop:1 #1565c0);
                border-radius: 15px;
                padding: 30px;
            }
        """)

        # Title
        title = QtWidgets.QLabel("🚀 Project Launcher")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 36px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QtWidgets.QLabel("Select a module to begin your work")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                font-weight: 500;
            }
        """)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_container)

        # Button grid
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(18)
        grid.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(grid)

        # Styles for active buttons
        active_button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
                color: white;
                border: 2px solid #1565c0;
                border-radius: 12px;
                padding: 25px;
                font-size: 16px;
                font-weight: 600;
                min-height: 90px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196f3, stop:1 #1976d2);
                border: 2px solid #2196f3;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1565c0, stop:1 #0d47a1);
                padding-top: 27px;
                padding-bottom: 23px;
            }
        """

        # Buttons
        self.my_work_btn = QtWidgets.QPushButton("📅 Events Management\nwith Graph Coloring")
        self.my_work_btn.setStyleSheet(active_button_style)
        self.my_work_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

        self.btn5 = QtWidgets.QPushButton("🏥 Scheduler\nPatient Imaging")
        self.btn5.setStyleSheet(active_button_style)
        self.btn5.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        
        self.shift_scheduler_btn = QtWidgets.QPushButton("🗓️ Shift Scheduler\nRetail Staff Planning")
        self.shift_scheduler_btn.setStyleSheet(active_button_style)
        self.shift_scheduler_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        
        self.puzzle_btn = QtWidgets.QPushButton("🧩 Sliding Puzzle")
        self.puzzle_btn.setStyleSheet(active_button_style)
        self.puzzle_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

        # Add buttons to grid
        grid.addWidget(self.my_work_btn, 0, 0)
        grid.addWidget(self.btn5, 0, 1)
        grid.addWidget(self.shift_scheduler_btn, 1, 0)
        grid.addWidget(self.puzzle_btn, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        main_layout.addStretch()

        # Footer with info
        footer_container = QtWidgets.QWidget()
        footer_layout = QtWidgets.QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(8)
        footer_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

        footer_text = QtWidgets.QLabel("💡 Tip: Click on blue buttons to access active modules")
        footer_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        footer_text.setStyleSheet("""
            QLabel {
                color: #1976d2;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        footer_layout.addWidget(footer_text)

        version = QtWidgets.QLabel("v1.0.0 | Full-Team Operations Research")
        version.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("""
            QLabel {
                color: #9e9e9e;
                font-size: 11px;
            }
        """)
        footer_layout.addWidget(version)

        main_layout.addWidget(footer_container)

        # Signals
        self.my_work_btn.clicked.connect(self.open_amr_work)
        self.btn5.clicked.connect(self.open_scheduler)
        self.shift_scheduler_btn.clicked.connect(self.open_shift_scheduler)
        self.puzzle_btn.clicked.connect(self.open_puzzle)

    def open_amr_work(self):
        if not hasattr(self, 'amr_window'):
            self.amr_window = AmrWorkWindow()
        self.amr_window.showMaximized()
        self.amr_window.raise_()

    def open_scheduler(self):
        # Directly import your scheduler window
        from scheduler_project.scheduler.gui import MainWindow as SchedulerWindow

        if not hasattr(self, 'scheduler_window'):
            self.scheduler_window = SchedulerWindow()
        self.scheduler_window.show()
        self.scheduler_window.raise_()

    def open_puzzle(self):
        """Open the sliding puzzle solver application"""
        try:
            from puzzle.main_window import MainWindow as PuzzleWindow
            if not hasattr(self, 'puzzle_window'):
                self.puzzle_window = PuzzleWindow()
            self.puzzle_window.show()
            self.puzzle_window.raise_()
        except Exception as e:
            error_msg = QtWidgets.QMessageBox(self)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"Failed to open Puzzle Solver:\n{str(e)}")
            error_msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            error_msg.exec()

    def open_shift_scheduler(self):
        """Open the shift scheduler application"""
        try:
            # Add shift_scheduler to path to ensure relative imports work
            shift_scheduler_dir = os.path.join(os.path.dirname(__file__), 'shift_scheduler')
            if shift_scheduler_dir not in sys.path:
                sys.path.insert(0, shift_scheduler_dir)
            
            # Import the shift scheduler MainWindow
            # Note: This import works because shift_scheduler uses relative imports
            # and we've added its directory to sys.path
            from views.main_window import MainWindow as ShiftSchedulerWindow
            
            if not hasattr(self, 'shift_scheduler_window'):
                self.shift_scheduler_window = ShiftSchedulerWindow()
            self.shift_scheduler_window.show()
            self.shift_scheduler_window.raise_()
        except Exception as e:
            error_msg = QtWidgets.QMessageBox(self)
            error_msg.setWindowTitle("Error")
            error_msg.setText(f"Failed to open Shift Scheduler:\n{str(e)}")
            error_msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
            error_msg.exec()





if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
