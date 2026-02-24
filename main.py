"""Nominis — main entry point."""

import sys
from PySide6.QtWidgets import QApplication
from database.db import init_db
from ui.main_window import MainWindow
from styles.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nominis")
    app.setStyleSheet(STYLESHEET)
    # Wayland: set app id for proper window decoration
    app.setDesktopFileName("nominis")

    init_db()

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
