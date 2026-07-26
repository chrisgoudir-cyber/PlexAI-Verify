import sys

from PySide6.QtWidgets import QApplication

from app.database import init_database
from app.main_window import MainWindow

init_database()

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())