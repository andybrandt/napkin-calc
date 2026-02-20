"""Traffic & Throughput panel – the first and primary calculator view.

Displays a grid of time-unit rows (Second ... Year).  Each row has:
- A label for the time unit.
- A ``ReactiveNumberField`` where the user can type a rate.
- A read-only talking-point label (e.g. "~3.7 billion").

Editing any field recalculates all others via the ``CalculationEngine``.
"""

from decimal import Decimal
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import TIME_UNIT_ABBREVIATIONS, LockedVariable, TimeUnit
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.formatting.display_formatter import DisplayFormatter
from napkin_calc.formatting.talking_points import TalkingPointGenerator
from napkin_calc.ui.widgets import LockButton, ReactiveNumberField

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
        self._talker = TalkingPointGenerator()
        self._fields: dict[TimeUnit, ReactiveNumberField] = {}
        self._notation_labels: dict[TimeUnit, QLabel] = {}
        self._talking_labels: dict[TimeUnit, QLabel] = {}
        self._is_updating = False

        self._build_ui()
        self._connect_signals()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        group = QGroupBox("Traffic / Throughput  (events per time unit)")

        # Lock button for the Rate variable
        self._lock_button = LockButton()
        self._lock_button.setChecked(
            self._engine.locked_variable == LockedVariable.RATE
        )

        group_layout = QVBoxLayout()

        lock_row = QHBoxLayout()
        lock_row.addWidget(self._lock_button)
        lock_row.addWidget(QLabel("Hold Rate constant"))
        lock_row.addStretch()
        group_layout.addLayout(lock_row)

        grid = QGridLayout()
        grid.setSpacing(8)

        # Column headers
        grid.addWidget(self._header_label("Time Unit"), 0, 0)
        grid.addWidget(self._header_label("Rate - events # / unit of time"), 0, 1)
        grid.addWidget(self._header_label("Scale"), 0, 2)
        grid.addWidget(self._header_label("Talking Point"), 0, 3)

        # Keep first three columns compact; talking-point column stretches
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 1)

        for row_index, unit in enumerate(_UNIT_ORDER, start=1):
            # Unit label (abbreviated)
            abbreviation = TIME_UNIT_ABBREVIATIONS[unit]
            unit_label = QLabel(f"per {abbreviation}")
            font = unit_label.font()
            font.setBold(True)
            unit_label.setFont(font)
            grid.addWidget(unit_label, row_index, 0)

            # Editable numeric field
            field = ReactiveNumberField(placeholder="0")
            self._fields[unit] = field
            grid.addWidget(field, row_index, 1)

            # Scientific notation label (e.g. "10^6")
            notation_label = QLabel("")
            notation_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            font = notation_label.font()
            font.setBold(True)
            notation_label.setFont(font)
            self._notation_labels[unit] = notation_label
            grid.addWidget(notation_label, row_index, 2)

            # Read-only talking-point label
            talking_label = QLabel("")
            talking_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            font = talking_label.font()
            font.setItalic(True)
            talking_label.setFont(font)
            talking_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._talking_labels[unit] = talking_label
            grid.addWidget(talking_label, row_index, 3)

        group_layout.addLayout(grid)
        group.setLayout(group_layout)
        outer_layout.addWidget(group)
        outer_layout.addStretch()

    @staticmethod
    def _header_label(text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    # -- signal wiring ------------------------------------------------------

    def _connect_signals(self) -> None:
        for unit, field in self._fields.items():
            field.value_changed.connect(partial(self._on_field_edited, unit))

        self._lock_button.clicked.connect(self._on_lock_clicked)
        self._engine.lock_changed.connect(self._sync_lock_button)

        self._engine.rates_changed.connect(self._refresh_all)
        self._engine.mode_changed.connect(self._refresh_all)

    def _on_lock_clicked(self) -> None:
        self._engine.set_locked_variable(LockedVariable.RATE)

    def _sync_lock_button(self) -> None:
        """Keep this lock button in sync when another panel changes the lock."""
        self._lock_button.setChecked(
            self._engine.locked_variable == LockedVariable.RATE
        )

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

                self._fields[unit].set_display_value(
                    self._formatter.format_input(exact_value)
                )
                self._notation_labels[unit].setText(
                    self._formatter.scientific_notation(display_value)
                )
                self._talking_labels[unit].setText(
                    self._talker.generate(display_value)
                )
        finally:
            self._is_updating = False
