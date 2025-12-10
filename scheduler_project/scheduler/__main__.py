from scheduler.gui import MainWindow
from PyQt6.QtWidgets import QApplication
from scheduler.utils import setup_logging
import sys

def run():
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    run()
