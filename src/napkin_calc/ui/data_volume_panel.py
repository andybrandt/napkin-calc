"""Data Volume panel – payload size input and storage throughput display.

Sits below the Traffic panel in the single-window layout.  Shows:
- An editable payload-size field with a unit selector (B / KB / MB / GB).
- A grid of data throughput per time unit, auto-selecting the best
  data-size unit for each row, with talking points.
"""

from decimal import Decimal, InvalidOperation
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import (
    TIME_UNIT_ABBREVIATIONS,
    DataSizeUnit,
    LockedVariable,
    TimeUnit,
)
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.formatting.display_formatter import DisplayFormatter
from napkin_calc.formatting.talking_points import TalkingPointGenerator
from napkin_calc.ui.widgets import LockButton, ReactiveNumberField

# Time units displayed in the throughput grid
_TIME_UNIT_ORDER = [
    TimeUnit.SECOND,
    TimeUnit.MINUTE,
    TimeUnit.HOUR,
    TimeUnit.DAY,
    TimeUnit.MONTH,
    TimeUnit.YEAR,
]

# Data-size units offered in the payload-size dropdown
_PAYLOAD_UNITS = [
    DataSizeUnit.BYTE,
    DataSizeUnit.KILOBYTE,
    DataSizeUnit.MEGABYTE,
    DataSizeUnit.GIGABYTE,
]


class DataVolumePanel(QWidget):
    """Payload-size input + data-throughput display.

    Parameters
    ----------
    engine :
        The shared ``CalculationEngine`` instance.
    parent :
        Optional parent widget.
    """

    def __init__(self, engine: CalculationEngine, parent=None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._formatter = DisplayFormatter()
        self._talker = TalkingPointGenerator()

        self._throughput_value_labels: dict[TimeUnit, QLabel] = {}
        self._throughput_notation_labels: dict[TimeUnit, QLabel] = {}
        self._throughput_talking_labels: dict[TimeUnit, QLabel] = {}
        self._is_updating = False

        self._build_ui()
        self._connect_signals()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        # --- Payload + Target input section --------------------------------
        payload_group = QGroupBox("Data Volume")
        payload_layout = QGridLayout()

        # Payload row: lock | label | field | unit
        self._payload_lock = LockButton()
        self._payload_lock.setChecked(
            self._engine.locked_variable == LockedVariable.PAYLOAD
        )
        payload_layout.addWidget(self._payload_lock, 0, 0)
        payload_layout.addWidget(QLabel("Payload size per event:"), 0, 1)

        self._payload_field = ReactiveNumberField(placeholder="e.g. 400")
        payload_layout.addWidget(self._payload_field, 0, 2)

        self._payload_unit_combo = QComboBox()
        for unit in _PAYLOAD_UNITS:
            self._payload_unit_combo.addItem(unit.value, unit)
        self._payload_unit_combo.setCurrentIndex(1)  # Default to KB
        payload_layout.addWidget(self._payload_unit_combo, 0, 3)

        # Target Total Volume row: lock | label | field | size unit | time unit
        self._volume_lock = LockButton()
        self._volume_lock.setChecked(
            self._engine.locked_variable == LockedVariable.VOLUME
        )
        payload_layout.addWidget(self._volume_lock, 1, 0)
        payload_layout.addWidget(QLabel("Target Total Volume:"), 1, 1)

        self._target_field = ReactiveNumberField(placeholder="e.g. 1")
        payload_layout.addWidget(self._target_field, 1, 2)

        self._target_size_unit_combo = QComboBox()
        for unit in DataSizeUnit:
            self._target_size_unit_combo.addItem(unit.value, unit)
        self._target_size_unit_combo.setCurrentIndex(4)  # TB
        payload_layout.addWidget(self._target_size_unit_combo, 1, 3)

        self._target_time_unit_combo = QComboBox()
        for time_unit in _TIME_UNIT_ORDER:
            self._target_time_unit_combo.addItem(f"per {time_unit.value}", time_unit)
        self._target_time_unit_combo.setCurrentIndex(3)  # Day
        payload_layout.addWidget(self._target_time_unit_combo, 1, 4)

        payload_layout.setColumnStretch(5, 1)

        payload_group.setLayout(payload_layout)
        outer_layout.addWidget(payload_group)

        # --- Data throughput grid ------------------------------------------
        throughput_group = QGroupBox(
            "Data Throughput  (rate x payload = data per time unit)"
        )
        grid = QGridLayout()
        grid.setSpacing(8)

        # Column headers
        grid.addWidget(self._header_label("Time Unit"), 0, 0)
        grid.addWidget(self._header_label("Data Volume"), 0, 1)
        grid.addWidget(self._header_label("Scale"), 0, 2)
        grid.addWidget(self._header_label("Talking Point"), 0, 3)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 1)

        for row_index, time_unit in enumerate(_TIME_UNIT_ORDER, start=1):
            abbreviation = TIME_UNIT_ABBREVIATIONS[time_unit]
            unit_label = QLabel(f"per {abbreviation}")
            font = unit_label.font()
            font.setBold(True)
            unit_label.setFont(font)
            grid.addWidget(unit_label, row_index, 0)

            # Data volume value (read-only)
            value_label = QLabel("")
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            value_label.setMinimumWidth(140)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._throughput_value_labels[time_unit] = value_label
            grid.addWidget(value_label, row_index, 1)

            # Scientific notation
            notation_label = QLabel("")
            notation_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            font = notation_label.font()
            font.setBold(True)
            notation_label.setFont(font)
            self._throughput_notation_labels[time_unit] = notation_label
            grid.addWidget(notation_label, row_index, 2)

            # Talking point
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
            self._throughput_talking_labels[time_unit] = talking_label
            grid.addWidget(talking_label, row_index, 3)

        throughput_group.setLayout(grid)
        outer_layout.addWidget(throughput_group)

    @staticmethod
    def _header_label(text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    # -- signal wiring ------------------------------------------------------

    def _connect_signals(self) -> None:
        self._payload_field.value_changed.connect(self._on_payload_edited)
        self._payload_unit_combo.currentIndexChanged.connect(
            self._on_payload_unit_changed
        )
        self._target_field.value_changed.connect(self._on_target_edited)
        self._target_size_unit_combo.currentIndexChanged.connect(
            self._on_target_unit_changed
        )
        self._target_time_unit_combo.currentIndexChanged.connect(
            self._on_target_unit_changed
        )

        self._payload_lock.clicked.connect(self._on_payload_lock_clicked)
        self._volume_lock.clicked.connect(self._on_volume_lock_clicked)
        self._engine.lock_changed.connect(self._sync_lock_buttons)

        self._engine.storage_changed.connect(self._refresh_all)
        self._engine.mode_changed.connect(self._refresh_all)

    def _on_payload_lock_clicked(self) -> None:
        self._engine.set_locked_variable(LockedVariable.PAYLOAD)

    def _on_volume_lock_clicked(self) -> None:
        self._engine.set_locked_variable(LockedVariable.VOLUME)

    def _sync_lock_buttons(self) -> None:
        """Keep lock buttons in sync when another panel changes the lock."""
        locked = self._engine.locked_variable
        self._payload_lock.setChecked(locked == LockedVariable.PAYLOAD)
        self._volume_lock.setChecked(locked == LockedVariable.VOLUME)

    def _on_payload_edited(self, value: Decimal) -> None:
        """User typed a new payload size."""
        if self._is_updating:
            return
        unit = self._payload_unit_combo.currentData()
        self._engine.set_payload_size(value, unit)

    def _on_payload_unit_changed(self) -> None:
        """User changed the payload-size unit dropdown."""
        text = self._payload_field.text().strip().replace(",", "")
        if not text:
            return
        try:
            value = Decimal(text)
        except InvalidOperation:
            return
        unit = self._payload_unit_combo.currentData()
        self._engine.set_payload_size(value, unit)

    def _on_target_edited(self, value: Decimal) -> None:
        """User typed a new target throughput."""
        if self._is_updating:
            return
        size_unit = self._target_size_unit_combo.currentData()
        time_unit = self._target_time_unit_combo.currentData()
        self._engine.set_target_throughput(value, size_unit, time_unit)

    def _on_target_unit_changed(self) -> None:
        """User changed one of the target dropdowns."""
        text = self._target_field.text().strip().replace(",", "")
        if not text:
            return
        try:
            value = Decimal(text)
        except InvalidOperation:
            return
        size_unit = self._target_size_unit_combo.currentData()
        time_unit = self._target_time_unit_combo.currentData()
        self._engine.set_target_throughput(value, size_unit, time_unit)

    # -- display refresh ----------------------------------------------------

    def _refresh_all(self) -> None:
        """Refresh the payload field and all throughput rows from engine state."""
        self._is_updating = True
        try:
            # Update payload input field
            if self._engine.payload_size_bytes == 0:
                self._payload_field.set_display_value("")
                self._payload_unit_combo.setCurrentIndex(1)  # default to KB
            else:
                unit = self._payload_unit_combo.currentData()
                exact_value = self._engine.get_payload_size(unit)
                self._payload_field.set_display_value(
                    self._formatter.format_input(exact_value)
                )

            # Update target total volume input field
            target_time_unit = self._target_time_unit_combo.currentData()
            target_size_unit = self._target_size_unit_combo.currentData()
            target_value = self._engine.get_data_throughput(target_time_unit, target_size_unit)
            if target_value == 0:
                self._target_field.set_display_value("")
            else:
                self._target_field.set_display_value(
                    self._formatter.format_input(target_value)
                )

            for time_unit in _TIME_UNIT_ORDER:
                value, best_unit = self._engine.get_data_throughput_best_unit(
                    time_unit
                )
                total_bytes = self._engine.get_data_throughput_bytes(time_unit)

                # Value with auto-selected unit
                display_text = (
                    f"{self._formatter.format_input(value)} {best_unit.value}"
                    if total_bytes > 0
                    else ""
                )
                self._throughput_value_labels[time_unit].setText(display_text)

                # Scientific notation on the raw byte count
                self._throughput_notation_labels[time_unit].setText(
                    self._formatter.scientific_notation(total_bytes)
                )

                # Talking point
                talking = (
                    self._talker.generate_data_size(value, best_unit)
                    if total_bytes > 0
                    else ""
                )
                self._throughput_talking_labels[time_unit].setText(talking)
        finally:
            self._is_updating = False
