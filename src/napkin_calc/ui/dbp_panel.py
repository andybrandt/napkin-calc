"""Delay-Bandwidth Product (DBP) panel.

Displays a simple utility for sizing network buffers based on
bandwidth and round-trip time.
"""

from decimal import Decimal, InvalidOperation

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

from napkin_calc.core.constants import BandwidthUnit, DataSizeUnit
from napkin_calc.core.data_converter import DataSizeConverter
from napkin_calc.core.dbp_calculator import DBPCalculator
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.formatting.display_formatter import DisplayFormatter
from napkin_calc.formatting.talking_points import TalkingPointGenerator
from napkin_calc.ui.widgets import ReactiveNumberField

_BANDWIDTH_UNITS = [
    BandwidthUnit.MBPS,
    BandwidthUnit.GBPS,
    BandwidthUnit.TBPS,
]


class DBPPanel(QWidget):
    """Delay-Bandwidth Product calculator panel."""

    def __init__(self, engine: CalculationEngine, parent=None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._calculator = DBPCalculator()
        self._formatter = DisplayFormatter()
        self._talker = TalkingPointGenerator()
        self._is_updating = False

        self._build_ui()
        self._connect_signals()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)

        group = QGroupBox("Network / Buffers (Delay-Bandwidth Product)")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Labels
        layout.addWidget(QLabel("Bandwidth:"), 0, 0)
        layout.addWidget(QLabel("Round-Trip Time:"), 1, 0)
        
        # Make the first column narrow
        layout.setColumnStretch(0, 0)

        # Bandwidth input
        bw_layout = QHBoxLayout()
        self._bw_field = ReactiveNumberField(placeholder="e.g. 1")
        bw_layout.addWidget(self._bw_field)

        self._bw_unit_combo = QComboBox()
        for unit in _BANDWIDTH_UNITS:
            self._bw_unit_combo.addItem(unit.value, unit)
        self._bw_unit_combo.setCurrentIndex(1)  # Default to Gbps
        bw_layout.addWidget(self._bw_unit_combo)
        bw_layout.addStretch()

        layout.addLayout(bw_layout, 0, 1)

        # RTT input
        rtt_layout = QHBoxLayout()
        self._rtt_field = ReactiveNumberField(placeholder="e.g. 100")
        rtt_layout.addWidget(self._rtt_field)
        rtt_layout.addWidget(QLabel("ms"))
        rtt_layout.addStretch()

        layout.addLayout(rtt_layout, 1, 1)

        # Output row
        layout.addWidget(self._header_label("Data in Flight:"), 2, 0)

        self._output_label = QLabel("0")
        self._output_label.setStyleSheet("font-weight: bold; color: #408cd2;")
        self._output_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self._output_talking_label = QLabel("")
        font = self._output_talking_label.font()
        font.setItalic(True)
        self._output_talking_label.setFont(font)

        out_layout = QHBoxLayout()
        out_layout.addWidget(self._output_label)
        out_layout.addWidget(self._output_talking_label)
        out_layout.addStretch()

        layout.addLayout(out_layout, 2, 1)

        group.setLayout(layout)
        outer_layout.addWidget(group)

    @staticmethod
    def _header_label(text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    # -- signal wiring ------------------------------------------------------

    def _connect_signals(self) -> None:
        self._bw_field.value_changed.connect(self._on_input_changed)
        self._bw_unit_combo.currentIndexChanged.connect(self._on_input_changed)
        self._rtt_field.value_changed.connect(self._on_input_changed)

        self._engine.mode_changed.connect(self._refresh_output)
        self._engine.reset_occurred.connect(self._on_reset)

    def _on_input_changed(self, *args) -> None:
        if self._is_updating:
            return
        self._refresh_output()

    def _on_reset(self) -> None:
        self._is_updating = True
        self._bw_field.set_display_value("")
        self._rtt_field.set_display_value("")
        self._bw_unit_combo.setCurrentIndex(1)
        self._is_updating = False
        self._refresh_output()

    # -- display refresh ----------------------------------------------------

    def _refresh_output(self) -> None:
        bw_text = self._bw_field.text().strip().replace(",", "")
        rtt_text = self._rtt_field.text().strip().replace(",", "")

        if not bw_text or not rtt_text:
            self._output_label.setText("0")
            self._output_talking_label.setText("")
            return

        try:
            bw_val = Decimal(bw_text)
            rtt_val = Decimal(rtt_text)
        except InvalidOperation:
            return

        unit = self._bw_unit_combo.currentData()
        mode = self._engine.display_mode

        self._calculator.set_bandwidth(bw_val, unit, mode)
        self._calculator.set_rtt(rtt_val)

        total_bytes = self._calculator.data_in_flight_bytes

        if total_bytes == 0:
            self._output_label.setText("0")
            self._output_talking_label.setText("")
            return

        # Auto-select the best unit to display
        converter = DataSizeConverter()
        converter.size_in_bytes = total_bytes
        best_unit = converter.best_unit(mode)
        display_val = converter.get_size(best_unit, mode)

        # Format output
        text = f"{self._formatter.format_value(display_val)} {best_unit.value}"
        talking = self._talker.generate_data_size(display_val, best_unit)

        self._output_label.setText(text)
        self._output_talking_label.setText(talking)
