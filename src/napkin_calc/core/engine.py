"""Central calculation engine that owns all reactive state.

The engine is a QObject so it can emit Qt signals whenever the
underlying model changes.  UI panels connect to these signals to
refresh their display fields.

Design invariant: the engine always stores *exact* values.  The
``CalculationMode`` passed to accessor helpers only affects how the
result is converted for display.
"""

from decimal import Decimal

from PySide6.QtCore import QObject, Signal

from napkin_calc.core.constants import CalculationMode, TimeUnit
from napkin_calc.core.time_converter import TimeUnitConverter


class CalculationEngine(QObject):
    """Reactive calculation model for the Napkin Calculator.

    Signals
    -------
    rates_changed :
        Emitted whenever the traffic rate is updated from any source.
    mode_changed :
        Emitted when the display mode (exact / estimate) is toggled.
    """

    rates_changed = Signal()
    mode_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._time_converter = TimeUnitConverter()
        self._display_mode = CalculationMode.ESTIMATE

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
        """
        self._time_converter.set_rate(value, unit)
        self.rates_changed.emit()

    def get_rate(self, unit: TimeUnit) -> Decimal:
        """Return the current rate in *unit*, using the active display mode."""
        return self._time_converter.get_rate(unit, self._display_mode)

    def get_rate_exact(self, unit: TimeUnit) -> Decimal:
        """Return the current rate in *unit* using exact factors (for input fields)."""
        return self._time_converter.get_rate(unit, CalculationMode.EXACT)

    @property
    def events_per_second_exact(self) -> Decimal:
        """The canonical internal value – always exact."""
        return self._time_converter.events_per_second

    def reset(self) -> None:
        """Clear all state back to zero."""
        self._time_converter.reset()
        self.rates_changed.emit()
