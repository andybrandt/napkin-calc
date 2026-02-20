"""Convert event rates between different time units.

The converter always works in exact precision internally. The caller
specifies which CalculationMode to use only when *reading* values for
display so that switching between modes never loses precision.
"""

from decimal import Decimal
from typing import Dict

from napkin_calc.core.constants import (
    CalculationMode,
    TimeUnit,
    seconds_per_unit,
)


class TimeUnitConverter:
    """Bidirectional rate converter across all supported time units.

    Internally stores the canonical rate as **events per second** using
    the exact conversion factors.  Conversion to other units can be
    requested in either exact or estimate mode.
    """

    def __init__(self) -> None:
        self._events_per_second: Decimal = Decimal("0")

    # -- mutators -----------------------------------------------------------

    def set_rate(self, value: Decimal, unit: TimeUnit) -> None:
        """Set the rate from a value expressed in *unit*.

        The value is normalised to events-per-second using **exact**
        factors so no precision is lost.
        """
        seconds = seconds_per_unit(unit, CalculationMode.EXACT)
        self._events_per_second = value / seconds

    # -- accessors ----------------------------------------------------------

    @property
    def events_per_second(self) -> Decimal:
        """Canonical rate stored internally (always exact)."""
        return self._events_per_second

    def get_rate(self, unit: TimeUnit, mode: CalculationMode) -> Decimal:
        """Return the rate expressed in *unit* for the given display mode."""
        seconds = seconds_per_unit(unit, mode)
        return self._events_per_second * seconds

    def get_all_rates(
        self, mode: CalculationMode
    ) -> Dict[TimeUnit, Decimal]:
        """Return rates for every time unit in the given display mode."""
        return {unit: self.get_rate(unit, mode) for unit in TimeUnit}

    def reset(self) -> None:
        """Clear the stored rate to zero."""
        self._events_per_second = Decimal("0")
