"""Static reference tables for system design interviews.

Displays:
- High Availability "Nines"
- Computational Resource Hierarchy
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import REFERENCE_LATENCY, REFERENCE_NINES


class ReferencePanel(QWidget):
    """Static reference guides."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        # -- Nines Table --
        nines_group = QGroupBox("High Availability Targets")
        nines_grid = QGridLayout()
        nines_grid.setSpacing(8)

        nines_grid.addWidget(self._header_label("Availability"), 0, 0)
        nines_grid.addWidget(self._header_label("Downtime per Year"), 0, 1)
        nines_grid.addWidget(self._header_label("Per Month"), 0, 2)
        nines_grid.addWidget(self._header_label("Per Day"), 0, 3)

        for row, entry in enumerate(REFERENCE_NINES, start=1):
            nines_grid.addWidget(QLabel(entry["availability"]), row, 0)
            nines_grid.addWidget(QLabel(entry["year"]), row, 1)
            nines_grid.addWidget(QLabel(entry["month"]), row, 2)
            nines_grid.addWidget(QLabel(entry["day"]), row, 3)

        nines_group.setLayout(nines_grid)
        outer_layout.addWidget(nines_group)

        # -- Latency Hierarchy --
        latency_group = QGroupBox("System Latency Comparison")
        latency_grid = QGridLayout()
        latency_grid.setSpacing(8)

        latency_grid.addWidget(self._header_label("Operation"), 0, 0)
        latency_grid.addWidget(self._header_label("Latency"), 0, 1)
        latency_grid.addWidget(self._header_label("Relative Cost"), 0, 2)

        for row, entry in enumerate(REFERENCE_LATENCY, start=1):
            latency_grid.addWidget(QLabel(entry["operation"]), row, 0)
            latency_grid.addWidget(QLabel(entry["latency"]), row, 1)
            latency_grid.addWidget(QLabel(entry["cost"]), row, 2)

        latency_group.setLayout(latency_grid)
        outer_layout.addWidget(latency_group)

    @staticmethod
    def _header_label(text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label
