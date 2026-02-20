"""Traffic & Throughput panel – the first and primary calculator view.

Displays a grid of time-unit rows (Second … Year).  Each row has:
- A label for the time unit.
- A ``ReactiveNumberField`` where the user can type a rate.
- A read-only label showing the formatted value with scientific notation.

Editing any field recalculates all others via the ``CalculationEngine``.
"""

from decimal import Decimal
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import TIME_UNIT_ABBREVIATIONS, TimeUnit
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.formatting.display_formatter import DisplayFormatter
from napkin_calc.ui.widgets import ReactiveNumberField

# The order in which time units appear in the grid (top to bottom)
_UNIT_ORDER = [
    TimeUnit.SECOND,
    TimeUnit.MINUTE,
    TimeUnit.HOUR,
    TimeUnit.DAY,
    TimeUnit.MONTH,
    TimeUnit.YEAR,
]


class TrafficPanel(QWidget):
    """Bidirectional traffic-rate calculator panel.

    Parameters
    ----------
    engine :
        The shared ``CalculationEngine`` instance that owns all state.
    parent :
        Optional parent widget.
    """

    def __init__(self, engine: CalculationEngine, parent=None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._formatter = DisplayFormatter()
        self._fields: dict[TimeUnit, ReactiveNumberField] = {}
        self._display_labels: dict[TimeUnit, QLabel] = {}
        self._is_updating = False

        self._build_ui()
        self._connect_signals()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        group = QGroupBox("Traffic / Throughput  (events per time unit)")
        grid = QGridLayout()
        grid.setSpacing(8)

        # Column headers
        grid.addWidget(self._header_label("Time Unit"), 0, 0)
        grid.addWidget(self._header_label("Rate (editable)"), 0, 1)
        grid.addWidget(self._header_label("Formatted"), 0, 2)

        for row_index, unit in enumerate(_UNIT_ORDER, start=1):
            # Unit label (abbreviated)
            abbreviation = TIME_UNIT_ABBREVIATIONS[unit]
            unit_label = QLabel(f"per {abbreviation}")
            unit_label.setStyleSheet("font-weight: bold;")
            grid.addWidget(unit_label, row_index, 0)

            # Editable numeric field
            field = ReactiveNumberField(placeholder="0")
            self._fields[unit] = field
            grid.addWidget(field, row_index, 1)

            # Read-only formatted display (with scientific notation)
            display_label = QLabel("0")
            display_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            display_label.setMinimumWidth(200)
            display_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._display_labels[unit] = display_label
            grid.addWidget(display_label, row_index, 2)

        group.setLayout(grid)
        outer_layout.addWidget(group)
        outer_layout.addStretch()

    @staticmethod
    def _header_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; color: #555;")
        return label

    # -- signal wiring ------------------------------------------------------

    def _connect_signals(self) -> None:
        # When the user edits any field, push the new rate into the engine
        for unit, field in self._fields.items():
            field.value_changed.connect(partial(self._on_field_edited, unit))

        # When the engine announces a change, refresh all displayed values
        self._engine.rates_changed.connect(self._refresh_all)
        self._engine.mode_changed.connect(self._refresh_all)

    def _on_field_edited(self, unit: TimeUnit, value: Decimal) -> None:
        """User changed a rate field – push into the engine."""
        if self._is_updating:
            return
        self._engine.set_rate(value, unit)

    # -- display refresh ----------------------------------------------------

    def _refresh_all(self) -> None:
        """Recompute every row from engine state.

        Uses the ``_is_updating`` guard so that programmatically setting
        field text does not re-trigger ``_on_field_edited``.
        """
        self._is_updating = True
        try:
            for unit in _UNIT_ORDER:
                display_value = self._engine.get_rate(unit)
                exact_value = self._engine.get_rate_exact(unit)

                # Update the editable field with the exact value (no 10^x)
                self._fields[unit].set_display_value(
                    self._formatter.format_input(exact_value)
                )

                # Update the read-only label with mode-aware formatting
                self._display_labels[unit].setText(
                    self._formatter.format_value(display_value)
                )
        finally:
            self._is_updating = False
