"""Central calculation engine that owns all reactive state.

The engine is a QObject so it can emit Qt signals whenever the
underlying model changes.  UI sections connect to these signals to
refresh their display fields.

Design invariant: the engine always stores *exact* values.  The
``CalculationMode`` passed to accessor helpers only affects how the
result is converted for display.

Lock behaviour
--------------
``Volume = Rate * Payload``

On startup no variable is locked (LockedVariable.NONE).  The first
variable the user types into auto-locks -- this is reflected in the
UI padlock buttons.  After that, the locked variable is held constant
and the third is recalculated whenever either of the other two change.
The user can override the lock at any time by clicking a different padlock.
Reset clears the lock back to NONE.
"""

from decimal import Decimal

from PySide6.QtCore import QObject, Signal

from napkin_calc.core.constants import (
    CalculationMode,
    DataSizeUnit,
    LockedVariable,
    TimeUnit,
    bytes_per_unit,
    seconds_per_unit,
)
from napkin_calc.core.data_converter import DataSizeConverter
from napkin_calc.core.time_converter import TimeUnitConverter


class CalculationEngine(QObject):
    """Reactive calculation model for the Napkin Calculator."""

    rates_changed = Signal()
    storage_changed = Signal()
    mode_changed = Signal()
    lock_changed = Signal()
    reset_occurred = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._time_converter = TimeUnitConverter()
        self._display_mode = CalculationMode.EXACT
        self._payload_size_bytes = Decimal("0")
        self._locked = LockedVariable.NONE

        # Stored target throughput in bytes/sec (exact).
        # Used when Volume is an independent input rather than derived.
        self._target_volume_bps = Decimal("0")

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

    # -- lock ---------------------------------------------------------------

    @property
    def locked_variable(self) -> LockedVariable:
        return self._locked

    def set_locked_variable(self, var: LockedVariable) -> None:
        """Set the locked variable explicitly (user clicked a padlock)."""
        if var != self._locked:
            self._locked = var
            self.lock_changed.emit()

    def _auto_lock(self, var: LockedVariable) -> None:
        """Auto-lock *var* if nothing is locked yet."""
        if self._locked == LockedVariable.NONE:
            self._locked = var
            self.lock_changed.emit()

    # -- traffic rate -------------------------------------------------------

    def set_rate(self, value: Decimal, unit: TimeUnit) -> None:
        """User edited the traffic rate.

        Auto-locks Rate on first non-zero input if nothing is locked yet.
        Resolves payload from the stored target when appropriate:
        - Volume is locked and target is set, OR
        - Payload is still zero and a stored target can now be resolved.
        """
        self._time_converter.set_rate(value, unit)
        if value != Decimal("0"):
            self._auto_lock(LockedVariable.RATE)

        should_solve_payload = (
            self._target_volume_bps != Decimal("0")
            and self._time_converter.events_per_second != Decimal("0")
            and (
                self._locked == LockedVariable.VOLUME
                or self._payload_size_bytes == Decimal("0")
            )
        )
        if should_solve_payload:
            self._payload_size_bytes = (
                self._target_volume_bps / self._time_converter.events_per_second
            )

        self.rates_changed.emit()
        self.storage_changed.emit()

    def get_rate(self, unit: TimeUnit) -> Decimal:
        return self._time_converter.get_rate(unit, self._display_mode)

    def get_rate_exact(self, unit: TimeUnit) -> Decimal:
        return self._time_converter.get_rate(unit, CalculationMode.EXACT)

    @property
    def events_per_second_exact(self) -> Decimal:
        return self._time_converter.events_per_second

    # -- payload size -------------------------------------------------------

    @property
    def payload_size_bytes(self) -> Decimal:
        return self._payload_size_bytes

    def set_payload_size(self, value: Decimal, unit: DataSizeUnit) -> None:
        """User edited the payload size.

        Auto-locks Payload on first non-zero input if nothing is locked yet.
        Resolves rate from the stored target when appropriate:
        - Volume is locked and target is set, OR
        - Rate is still zero and a stored target can now be resolved.
        """
        self._payload_size_bytes = value * bytes_per_unit(unit, CalculationMode.EXACT)
        if self._payload_size_bytes != Decimal("0"):
            self._auto_lock(LockedVariable.PAYLOAD)

        should_solve_rate = (
            self._target_volume_bps != Decimal("0")
            and self._payload_size_bytes != Decimal("0")
            and (
                self._locked == LockedVariable.VOLUME
                or self._time_converter.events_per_second == Decimal("0")
            )
        )
        if should_solve_rate:
            new_rate = self._target_volume_bps / self._payload_size_bytes
            self._time_converter.set_rate(new_rate, TimeUnit.SECOND)
            self.rates_changed.emit()

        self.storage_changed.emit()

    def get_payload_size(self, unit: DataSizeUnit) -> Decimal:
        divisor = bytes_per_unit(unit, self._display_mode)
        if divisor == 0:
            return Decimal("0")
        return self._payload_size_bytes / divisor

    # -- data throughput / storage ------------------------------------------

    @property
    def data_throughput_bytes_per_second(self) -> Decimal:
        """Bytes of data generated per second.

        If a target volume is set and the computed value is still zero
        (because rate or payload is missing), returns the target so the
        throughput grid shows useful data.
        """
        computed = self._time_converter.events_per_second * self._payload_size_bytes
        if computed == Decimal("0") and self._target_volume_bps != Decimal("0"):
            return self._target_volume_bps
        return computed

    def get_data_throughput_bytes(self, time_unit: TimeUnit) -> Decimal:
        seconds = seconds_per_unit(time_unit, self._display_mode)
        return self.data_throughput_bytes_per_second * seconds

    def get_data_throughput(
        self, time_unit: TimeUnit, size_unit: DataSizeUnit
    ) -> Decimal:
        total_bytes = self.get_data_throughput_bytes(time_unit)
        divisor = bytes_per_unit(size_unit, self._display_mode)
        if divisor == 0:
            return Decimal("0")
        return total_bytes / divisor

    def get_data_throughput_best_unit(
        self, time_unit: TimeUnit
    ) -> tuple[Decimal, DataSizeUnit]:
        total_bytes = self.get_data_throughput_bytes(time_unit)
        converter = DataSizeConverter()
        converter.size_in_bytes = total_bytes
        best = converter.best_unit(self._display_mode)
        return converter.get_size(best, self._display_mode), best

    def set_target_throughput(
        self, value: Decimal, size_unit: DataSizeUnit, time_unit: TimeUnit
    ) -> None:
        """User edited the target total volume.

        If Rate is locked, recalculate Payload.
        If Payload is locked, recalculate Rate.
        If Volume is locked (user overrides), just store and update naturally.

        If neither Rate nor Payload is available yet, the target is stored
        as a pending constraint for later resolution.
        """
        target_bytes = value * bytes_per_unit(size_unit, CalculationMode.EXACT)
        target_bps = target_bytes / seconds_per_unit(time_unit, CalculationMode.EXACT)
        self._target_volume_bps = target_bps
        if target_bps != Decimal("0"):
            self._auto_lock(LockedVariable.VOLUME)

        has_rate = self.events_per_second_exact != Decimal("0")
        has_payload = self._payload_size_bytes != Decimal("0")

        if self._locked == LockedVariable.RATE and has_rate:
            self._payload_size_bytes = target_bps / self.events_per_second_exact
            self.storage_changed.emit()
        elif self._locked == LockedVariable.PAYLOAD and has_payload:
            new_rate = target_bps / self._payload_size_bytes
            self._time_converter.set_rate(new_rate, TimeUnit.SECOND)
            self.rates_changed.emit()
            self.storage_changed.emit()
        elif self._locked == LockedVariable.VOLUME:
            # User is overriding the locked volume -- just store and recompute
            self.storage_changed.emit()
        elif has_rate:
            # Default: hold rate, solve payload
            self._payload_size_bytes = target_bps / self.events_per_second_exact
            self.storage_changed.emit()
        elif has_payload:
            # Hold payload, solve rate
            new_rate = target_bps / self._payload_size_bytes
            self._time_converter.set_rate(new_rate, TimeUnit.SECOND)
            self.rates_changed.emit()
            self.storage_changed.emit()
        else:
            # Neither known -- store as pending, throughput grid will show it
            self.storage_changed.emit()

    # -- pending target (for backward compat with existing tests) -----------

    @property
    def pending_target_bytes_per_second(self) -> Decimal:
        """The stored target throughput (may or may not be fully resolved)."""
        return self._target_volume_bps

    # -- reset --------------------------------------------------------------

    def reset(self) -> None:
        """Clear all state back to zero and remove any lock."""
        self._time_converter.reset()
        self._payload_size_bytes = Decimal("0")
        self._target_volume_bps = Decimal("0")
        self._locked = LockedVariable.NONE
        self.rates_changed.emit()
        self.storage_changed.emit()
        self.lock_changed.emit()
        self.reset_occurred.emit()
