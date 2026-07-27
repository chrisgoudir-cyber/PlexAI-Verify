import sys
from PySide6.QtWidgets import QApplication
from app.acquisition_dialog import AcquisitionDialog
from core.acquisition.models import MissingMovie

if __name__ == "__main__":
    app = QApplication(sys.argv)
    movies = [
        MissingMovie("Mission: Impossible - Fallout", 2018, "Mission: Impossible"),
        MissingMovie("Rocky V", 1990, "Rocky"),
        MissingMovie("Alien 3", 1992, "Alien"),
    ]
    dialog = AcquisitionDialog(movies)
    dialog.show()
    sys.exit(app.exec())
