"""Application entry point for the Napkin Calculator."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from napkin_calc.ui.main_window import MainWindow
from napkin_calc.ui.theme import init_theme

_ICON_PATH = Path(__file__).parent / "resources" / "icon.png"


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Napkin Calculator")

    if _ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(_ICON_PATH)))

    init_theme()  # must be called before creating any widgets

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
