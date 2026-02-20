"""Conversion factors and reference data used throughout the calculator.

Two sets of factors are maintained:
- **Exact**: precise values (binary KB = 1024, month = 365.25/12 days).
- **Estimate**: rounded values used in napkin math (KB = 1000, month = 30 days).
"""

from decimal import Decimal
from enum import Enum


class TimeUnit(Enum):
    """Supported time windows for rate conversion."""
    SECOND = "Second"
    MINUTE = "Minute"
    HOUR = "Hour"
    DAY = "Day"
    MONTH = "Month"
    YEAR = "Year"


# Short labels for use in the UI (column headers, row labels, etc.)
TIME_UNIT_ABBREVIATIONS: dict[TimeUnit, str] = {
    TimeUnit.SECOND: "sec",
    TimeUnit.MINUTE: "min",
    TimeUnit.HOUR: "hr",
    TimeUnit.DAY: "d",
    TimeUnit.MONTH: "mo",
    TimeUnit.YEAR: "y",
}


class DataSizeUnit(Enum):
    """Supported data-size magnitudes."""
    BYTE = "B"
    KILOBYTE = "KB"
    MEGABYTE = "MB"
    GIGABYTE = "GB"
    TERABYTE = "TB"
    PETABYTE = "PB"
    EXABYTE = "EB"


class CalculationMode(Enum):
    """Controls how values are *displayed* (engine always stores exact)."""
    EXACT = "exact"
    ESTIMATE = "estimate"


# ---------------------------------------------------------------------------
# Time – seconds per unit
# ---------------------------------------------------------------------------

SECONDS_PER_MINUTE = Decimal("60")
SECONDS_PER_HOUR = Decimal("3600")
SECONDS_PER_DAY = Decimal("86400")

# Exact: average Gregorian month = 365.25 / 12 = 30.4375 days
SECONDS_PER_MONTH_EXACT = Decimal("2629800")   # 30.4375 * 86400
SECONDS_PER_YEAR_EXACT = Decimal("31557600")    # 365.25  * 86400

# Estimate: 30-day month, 365-day year
SECONDS_PER_MONTH_ESTIMATE = Decimal("2592000")  # 30 * 86400
SECONDS_PER_YEAR_ESTIMATE = Decimal("31536000")   # 365 * 86400


def seconds_per_unit(unit: TimeUnit, mode: CalculationMode) -> Decimal:
    """Return the number of seconds in one *unit* for the given mode."""
    exact_map = {
        TimeUnit.SECOND: Decimal("1"),
        TimeUnit.MINUTE: SECONDS_PER_MINUTE,
        TimeUnit.HOUR: SECONDS_PER_HOUR,
        TimeUnit.DAY: SECONDS_PER_DAY,
        TimeUnit.MONTH: SECONDS_PER_MONTH_EXACT,
        TimeUnit.YEAR: SECONDS_PER_YEAR_EXACT,
    }
    estimate_map = {
        TimeUnit.SECOND: Decimal("1"),
        TimeUnit.MINUTE: SECONDS_PER_MINUTE,
        TimeUnit.HOUR: SECONDS_PER_HOUR,
        TimeUnit.DAY: SECONDS_PER_DAY,
        TimeUnit.MONTH: SECONDS_PER_MONTH_ESTIMATE,
        TimeUnit.YEAR: SECONDS_PER_YEAR_ESTIMATE,
    }
    mapping = exact_map if mode == CalculationMode.EXACT else estimate_map
    return mapping[unit]


# ---------------------------------------------------------------------------
# Data sizes – bytes per unit
# ---------------------------------------------------------------------------

BYTES_PER_KB_EXACT = Decimal("1024")
BYTES_PER_MB_EXACT = Decimal("1048576")       # 1024^2
BYTES_PER_GB_EXACT = Decimal("1073741824")    # 1024^3
BYTES_PER_TB_EXACT = Decimal("1099511627776")  # 1024^4
BYTES_PER_PB_EXACT = Decimal("1125899906842624")       # 1024^5
BYTES_PER_EB_EXACT = Decimal("1152921504606846976")    # 1024^6

BYTES_PER_KB_ESTIMATE = Decimal("1000")
BYTES_PER_MB_ESTIMATE = Decimal("1000000")
BYTES_PER_GB_ESTIMATE = Decimal("1000000000")
BYTES_PER_TB_ESTIMATE = Decimal("1000000000000")
BYTES_PER_PB_ESTIMATE = Decimal("1000000000000000")
BYTES_PER_EB_ESTIMATE = Decimal("1000000000000000000")


def bytes_per_unit(unit: DataSizeUnit, mode: CalculationMode) -> Decimal:
    """Return the number of bytes in one *unit* for the given mode."""
    exact_map = {
        DataSizeUnit.BYTE: Decimal("1"),
        DataSizeUnit.KILOBYTE: BYTES_PER_KB_EXACT,
        DataSizeUnit.MEGABYTE: BYTES_PER_MB_EXACT,
        DataSizeUnit.GIGABYTE: BYTES_PER_GB_EXACT,
        DataSizeUnit.TERABYTE: BYTES_PER_TB_EXACT,
        DataSizeUnit.PETABYTE: BYTES_PER_PB_EXACT,
        DataSizeUnit.EXABYTE: BYTES_PER_EB_EXACT,
    }
    estimate_map = {
        DataSizeUnit.BYTE: Decimal("1"),
        DataSizeUnit.KILOBYTE: BYTES_PER_KB_ESTIMATE,
        DataSizeUnit.MEGABYTE: BYTES_PER_MB_ESTIMATE,
        DataSizeUnit.GIGABYTE: BYTES_PER_GB_ESTIMATE,
        DataSizeUnit.TERABYTE: BYTES_PER_TB_ESTIMATE,
        DataSizeUnit.PETABYTE: BYTES_PER_PB_ESTIMATE,
        DataSizeUnit.EXABYTE: BYTES_PER_EB_ESTIMATE,
    }
    mapping = exact_map if mode == CalculationMode.EXACT else estimate_map
    return mapping[unit]
