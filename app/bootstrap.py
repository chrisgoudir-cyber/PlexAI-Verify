import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from core.infrastructure.database import Database
from core.services.maintenance_service import MaintenanceService

def run():
    app=QApplication(sys.argv)
    app.setApplicationName('PlexAI Verify X Pro')
    base=Path(__file__).resolve().parents[1]
    db=Database(base/'data'/'plexai_verify_x.db')
    db.initialize()
    window=MainWindow(db, MaintenanceService(db))
    window.show()
    return app.exec()
