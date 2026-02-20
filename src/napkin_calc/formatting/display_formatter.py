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

# Maximum decimal places shown for fractional results
_MAX_DECIMAL_PLACES = 4


class DisplayFormatter:
    """Stateless formatter – call ``format_value`` on any Decimal."""

    @staticmethod
    def format_value(value: Decimal, max_decimals: int = _MAX_DECIMAL_PLACES) -> str:
        """Return a human-readable string with optional 10^x annotation.

        Parameters
        ----------
        value:
            The number to format.
        max_decimals:
            Maximum fractional digits to show (trailing zeros stripped).

        Returns
        -------
        str
            e.g. ``"1,000,000  (10^6)"`` or ``"0.1157"``.
        """
        if value == 0:
            return "0"

        rounded = _smart_round(value, max_decimals)
        formatted = _add_thousands_separator(rounded)
        notation = _scientific_notation_suffix(value)

        if notation:
            return f"{formatted}  ({notation})"
        return formatted

    @staticmethod
    def format_input(value: Decimal, max_decimals: int = _MAX_DECIMAL_PLACES) -> str:
        """Format a value for placing back into an input field (no 10^x)."""
        if value == 0:
            return "0"
        rounded = _smart_round(value, max_decimals)
        return _add_thousands_separator(rounded)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _smart_round(value: Decimal, max_decimals: int) -> Decimal:
    """Round *value* to at most *max_decimals* fractional digits.

    Whole numbers are left untouched.  Trailing fractional zeros are
    stripped so we don't display ``"100.0000"``.
    """
    if value == value.to_integral_value():
        return value.to_integral_value()

    quantize_str = "1." + "0" * max_decimals
    rounded = value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
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
