from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from crackecraft import __version__
from crackecraft.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("CrackeCraft")
    app.setOrganizationName("CrackeCraft")
    app.setApplicationVersion(__version__)
    app.setFont(QFont("Segoe UI", 10))
    try:
        window = MainWindow()
    except Exception as exc:
        QMessageBox.critical(None, "No se pudo iniciar CrackeCraft", str(exc))
        raise
    window.show()
    sys.exit(app.exec())
