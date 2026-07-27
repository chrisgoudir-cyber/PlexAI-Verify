from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from plexai_verify.app.modern_window import ModernMainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PlexAI Verify")
    app.setOrganizationName("PlexAI Verify")
    window = ModernMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
