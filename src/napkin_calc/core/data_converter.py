"""Convert data sizes between byte-based units.

Works the same way as ``TimeUnitConverter``: stores a canonical value
in bytes and converts to any ``DataSizeUnit`` on demand, respecting
the exact/estimate mode.
"""

from decimal import Decimal
from typing import Dict

from napkin_calc.core.constants import (
    CalculationMode,
    DataSizeUnit,
    bytes_per_unit,
)


class DataSizeConverter:
    """Bidirectional converter across all supported data-size units.

    Internally stores the canonical size as **bytes** using exact
    conversion factors.
    """

    def __init__(self) -> None:
        self._bytes: Decimal = Decimal("0")

    # -- mutators -----------------------------------------------------------

    def set_size(self, value: Decimal, unit: DataSizeUnit) -> None:
        """Set the size from a value expressed in *unit* (always exact)."""
        self._bytes = value * bytes_per_unit(unit, CalculationMode.EXACT)

    @property
    def size_in_bytes(self) -> Decimal:
        """Canonical size stored internally (always exact)."""
        return self._bytes

    @size_in_bytes.setter
    def size_in_bytes(self, value: Decimal) -> None:
        self._bytes = value

    # -- accessors ----------------------------------------------------------

    def get_size(self, unit: DataSizeUnit, mode: CalculationMode) -> Decimal:
        """Return the size expressed in *unit* for the given display mode."""
        return self._bytes / bytes_per_unit(unit, mode)

    def get_all_sizes(
        self, mode: CalculationMode
    ) -> Dict[DataSizeUnit, Decimal]:
        """Return sizes for every data-size unit in the given display mode."""
        return {unit: self.get_size(unit, mode) for unit in DataSizeUnit}

    def best_unit(self, mode: CalculationMode) -> DataSizeUnit:
        """Return the largest unit where the value is still >= 1.

        Useful for picking a human-friendly display unit automatically.
        Falls back to BYTE if the value is very small.
        """
        # Walk from largest to smallest
        for unit in reversed(list(DataSizeUnit)):
            if self.get_size(unit, mode) >= 1:
                return unit
        return DataSizeUnit.BYTE

    def reset(self) -> None:
        """Clear the stored size to zero."""
        self._bytes = Decimal("0")
