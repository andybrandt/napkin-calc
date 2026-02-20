"""Application entry point for the Napkin Calculator."""

import sys

from PySide6.QtWidgets import QApplication

from napkin_calc.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Napkin Calculator")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
