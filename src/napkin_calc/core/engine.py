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

The target throughput is stored as a pending constraint.  It is only
resolved into a payload size or traffic rate once the user provides
the other missing variable.
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
    reset_occurred = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._time_converter = TimeUnitConverter()
        self._display_mode = CalculationMode.EXACT

        self._payload_size_bytes = Decimal("0")

        # Pending target throughput constraint (bytes per second, exact).
        # Non-zero when the user has entered a target but the equation
        # can't be solved yet because rate or payload is still missing.
        self._pending_target_bps = Decimal("0")

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

        If a pending target throughput exists and payload is still zero,
        resolves the constraint by computing payload size.
        """
        self._time_converter.set_rate(value, unit)

        if (
            self._pending_target_bps != Decimal("0")
            and self._payload_size_bytes == Decimal("0")
            and self._time_converter.events_per_second != Decimal("0")
        ):
            self._payload_size_bytes = (
                self._pending_target_bps / self._time_converter.events_per_second
            )
            self._pending_target_bps = Decimal("0")

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
        """The canonical internal rate -- always exact."""
        return self._time_converter.events_per_second

    # -- payload size -------------------------------------------------------

    @property
    def payload_size_bytes(self) -> Decimal:
        """Payload size per event in bytes (always exact)."""
        return self._payload_size_bytes

    def set_payload_size(self, value: Decimal, unit: DataSizeUnit) -> None:
        """Set the per-event payload size from *value* in *unit*.

        If a pending target throughput exists and rate is still zero,
        resolves the constraint by computing the traffic rate.
        """
        self._payload_size_bytes = value * bytes_per_unit(unit, CalculationMode.EXACT)

        if (
            self._pending_target_bps != Decimal("0")
            and self._time_converter.events_per_second == Decimal("0")
            and self._payload_size_bytes != Decimal("0")
        ):
            new_rate = self._pending_target_bps / self._payload_size_bytes
            self._time_converter.set_rate(new_rate, TimeUnit.SECOND)
            self._pending_target_bps = Decimal("0")
            self.rates_changed.emit()

        self.storage_changed.emit()

    def get_payload_size(self, unit: DataSizeUnit) -> Decimal:
        """Return the payload size in *unit* using the active display mode."""
        divisor = bytes_per_unit(unit, self._display_mode)
        if divisor == 0:
            return Decimal("0")
        return self._payload_size_bytes / divisor

    # -- pending target constraint ------------------------------------------

    @property
    def pending_target_bytes_per_second(self) -> Decimal:
        """The unresolved target throughput, or zero if fully resolved."""
        return self._pending_target_bps

    # -- data throughput / storage ------------------------------------------

    @property
    def data_throughput_bytes_per_second(self) -> Decimal:
        """Bytes of data generated per second (rate * payload).

        If a pending target is set but not yet resolved, returns the
        target value so the throughput grid shows something useful.
        """
        computed = self._time_converter.events_per_second * self._payload_size_bytes
        if computed == Decimal("0") and self._pending_target_bps != Decimal("0"):
            return self._pending_target_bps
        return computed

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

    def set_target_throughput(
        self, value: Decimal, size_unit: DataSizeUnit, time_unit: TimeUnit
    ) -> None:
        """Set a target throughput constraint.

        If both rate and payload are known (non-zero), holds rate
        constant and recalculates payload immediately.

        If only rate is known, recalculates payload immediately.

        If only payload is known, recalculates rate immediately.

        If neither is known, stores the target as a pending constraint.
        It will be resolved when the user later provides a rate or
        payload size.
        """
        target_bytes = value * bytes_per_unit(size_unit, CalculationMode.EXACT)
        target_bps = target_bytes / seconds_per_unit(time_unit, CalculationMode.EXACT)

        has_rate = self.events_per_second_exact != Decimal("0")
        has_payload = self._payload_size_bytes != Decimal("0")

        if has_rate:
            # Solve for payload: payload = target_bps / rate
            self._payload_size_bytes = target_bps / self.events_per_second_exact
            self._pending_target_bps = Decimal("0")
            self.storage_changed.emit()
        elif has_payload:
            # Solve for rate: rate = target_bps / payload
            new_rate = target_bps / self._payload_size_bytes
            self._time_converter.set_rate(new_rate, TimeUnit.SECOND)
            self._pending_target_bps = Decimal("0")
            self.rates_changed.emit()
            self.storage_changed.emit()
        else:
            # Can't solve yet -- store as pending constraint
            self._pending_target_bps = target_bps
            self.storage_changed.emit()

    # -- reset --------------------------------------------------------------

    def reset(self) -> None:
        """Clear all state back to zero."""
        self._time_converter.reset()
        self._payload_size_bytes = Decimal("0")
        self._pending_target_bps = Decimal("0")
        self.rates_changed.emit()
        self.storage_changed.emit()
        self.reset_occurred.emit()
