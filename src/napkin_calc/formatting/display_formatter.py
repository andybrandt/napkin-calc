"""Format numbers for display in exact or estimate mode.

Responsibilities:
- Thousands-separated formatting for readability.
- Scientific-notation annotation (10^x) for large values.
- Rounding controls for estimate mode.
"""

import math
from decimal import Decimal, ROUND_HALF_UP


# Threshold above which we append scientific notation
_SCIENTIFIC_NOTATION_THRESHOLD = Decimal("1000")

# Values at or above this magnitude are rounded to whole numbers;
# smaller values keep up to _SMALL_VALUE_DECIMALS fractional digits.
_WHOLE_NUMBER_THRESHOLD = Decimal("100")
_SMALL_VALUE_DECIMALS = 2


class DisplayFormatter:
    """Stateless formatter – call ``format_value`` on any Decimal."""

    @staticmethod
    def format_value(value: Decimal) -> str:
        """Return a human-readable string with optional 10^x annotation.

        Rounding rule: values >= 100 are shown as whole numbers;
        smaller values keep up to 2 decimal places.

        Returns
        -------
        str
            e.g. ``"1,000,000  (10^6)"`` or ``"0.12"``.
        """
        if value == 0:
            return "0"

        rounded = _smart_round(value)
        formatted = _add_thousands_separator(rounded)
        notation = _scientific_notation_suffix(value)

        if notation:
            return f"{formatted}  ({notation})"
        return formatted

    @staticmethod
    def format_input(value: Decimal) -> str:
        """Format a value for placing back into an input field (no 10^x)."""
        if value == 0:
            return "0"
        rounded = _smart_round(value)
        return _add_thousands_separator(rounded)

    @staticmethod
    def scientific_notation(value: Decimal) -> str:
        """Return e.g. ``'10^6'`` for large values, or empty string."""
        return _scientific_notation_suffix(value)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _smart_round(value: Decimal) -> Decimal:
    """Round *value* based on its magnitude.

    - Values >= 100 are rounded to the nearest whole number.
    - Smaller values keep up to 2 decimal places.
    Trailing fractional zeros are stripped.
    """
    if value == value.to_integral_value():
        return value.to_integral_value()

    if abs(value) >= _WHOLE_NUMBER_THRESHOLD:
        return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return rounded.normalize()


def _add_thousands_separator(value: Decimal) -> str:
    """Insert commas as thousands separators.

    Works for both integer-like Decimals and those with fractional parts.
    """
    if value == value.to_integral_value():
        return f"{int(value):,}"

    sign, digits, exponent = value.as_tuple()
    # Convert to string via float formatting to get commas
    # (Decimal.__format__ supports commas from Python 3.1+)
    return f"{value:,.{-exponent}f}"


def _scientific_notation_suffix(value: Decimal) -> str:
    """Return e.g. ``'10^6'`` when *value* >= 1000, else empty string."""
    abs_value = abs(value)
    if abs_value < _SCIENTIFIC_NOTATION_THRESHOLD:
        return ""

    exponent = int(math.log10(float(abs_value)))
    return f"10^{exponent}"
