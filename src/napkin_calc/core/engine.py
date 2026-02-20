"""Central calculation engine that owns all reactive state.

The engine is a QObject so it can emit Qt signals whenever the
underlying model changes.  UI sections connect to these signals to
refresh their display fields.

Design invariant: the engine always stores *exact* values.  The
``CalculationMode`` passed to accessor helpers only affects how the
result is converted for display.

Relationships
-------------
``data_throughput_per_second = events_per_second * payload_size_bytes``

Storage accumulation for a given time window is simply
``data_throughput_per_second * seconds_in_window``.
"""

from decimal import Decimal

from PySide6.QtCore import QObject, Signal

from napkin_calc.core.constants import (
    CalculationMode,
    DataSizeUnit,
    TimeUnit,
    bytes_per_unit,
    seconds_per_unit,
)
from napkin_calc.core.data_converter import DataSizeConverter
from napkin_calc.core.time_converter import TimeUnitConverter


class CalculationEngine(QObject):
    """Reactive calculation model for the Napkin Calculator.

    Signals
    -------
    rates_changed :
        Emitted whenever the traffic rate is updated.
    storage_changed :
        Emitted whenever payload size or a derived storage value changes.
    mode_changed :
        Emitted when the display mode (exact / estimate) is toggled.
    """

    rates_changed = Signal()
    storage_changed = Signal()
    mode_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._time_converter = TimeUnitConverter()
        self._display_mode = CalculationMode.ESTIMATE

        # Payload size per event (canonical: bytes, exact)
        self._payload_size_bytes = Decimal("0")

    # -- display mode -------------------------------------------------------

    @property
    def display_mode(self) -> CalculationMode:
        return self._display_mode

    def set_display_mode(self, mode: CalculationMode) -> None:
        if mode != self._display_mode:
            self._display_mode = mode
            self.mode_changed.emit()

    def toggle_display_mode(self) -> None:
        new_mode = (
            CalculationMode.EXACT
            if self._display_mode == CalculationMode.ESTIMATE
            else CalculationMode.ESTIMATE
        )
        self.set_display_mode(new_mode)

    # -- traffic rate -------------------------------------------------------

    def set_rate(self, value: Decimal, unit: TimeUnit) -> None:
        """Set the traffic rate from a user-edited field.

        Normalises to events/sec internally then notifies listeners.
        Also triggers storage recalculation since storage depends on rate.
        """
        self._time_converter.set_rate(value, unit)
        self.rates_changed.emit()
        self.storage_changed.emit()

    def get_rate(self, unit: TimeUnit) -> Decimal:
        """Return the current rate in *unit*, using the active display mode."""
        return self._time_converter.get_rate(unit, self._display_mode)

    def get_rate_exact(self, unit: TimeUnit) -> Decimal:
        """Return the current rate in *unit* using exact factors."""
        return self._time_converter.get_rate(unit, CalculationMode.EXACT)

    @property
    def events_per_second_exact(self) -> Decimal:
        """The canonical internal rate – always exact."""
        return self._time_converter.events_per_second

    # -- payload size -------------------------------------------------------

    @property
    def payload_size_bytes(self) -> Decimal:
        """Payload size per event in bytes (always exact)."""
        return self._payload_size_bytes

    def set_payload_size(self, value: Decimal, unit: DataSizeUnit) -> None:
        """Set the per-event payload size from *value* in *unit*."""
        self._payload_size_bytes = value * bytes_per_unit(unit, CalculationMode.EXACT)
        self.storage_changed.emit()

    def get_payload_size(self, unit: DataSizeUnit) -> Decimal:
        """Return the payload size in *unit* using the active display mode."""
        divisor = bytes_per_unit(unit, self._display_mode)
        if divisor == 0:
            return Decimal("0")
        return self._payload_size_bytes / divisor

    # -- data throughput / storage ------------------------------------------

    @property
    def data_throughput_bytes_per_second(self) -> Decimal:
        """Bytes of data generated per second (rate * payload)."""
        return self._time_converter.events_per_second * self._payload_size_bytes

    def get_data_throughput_bytes(self, time_unit: TimeUnit) -> Decimal:
        """Total bytes generated in one *time_unit* (display-mode aware)."""
        seconds = seconds_per_unit(time_unit, self._display_mode)
        return self.data_throughput_bytes_per_second * seconds

    def get_data_throughput(
        self, time_unit: TimeUnit, size_unit: DataSizeUnit
    ) -> Decimal:
        """Data generated in one *time_unit*, expressed in *size_unit*."""
        total_bytes = self.get_data_throughput_bytes(time_unit)
        divisor = bytes_per_unit(size_unit, self._display_mode)
        if divisor == 0:
            return Decimal("0")
        return total_bytes / divisor

    def get_data_throughput_best_unit(
        self, time_unit: TimeUnit
    ) -> tuple[Decimal, DataSizeUnit]:
        """Data generated per *time_unit*, auto-selecting the best size unit.

        Returns (value, unit) where the value is >= 1 in the chosen unit.
        """
        total_bytes = self.get_data_throughput_bytes(time_unit)
        converter = DataSizeConverter()
        converter.size_in_bytes = total_bytes
        best = converter.best_unit(self._display_mode)
        return converter.get_size(best, self._display_mode), best

    # -- reset --------------------------------------------------------------

    def reset(self) -> None:
        """Clear all state back to zero."""
        self._time_converter.reset()
        self._payload_size_bytes = Decimal("0")
        self.rates_changed.emit()
        self.storage_changed.emit()
