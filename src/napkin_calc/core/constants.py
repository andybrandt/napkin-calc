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


class BandwidthUnit(Enum):
    """Supported network bandwidth magnitudes (bits/sec)."""
    BPS = "bps"
    KBPS = "Kbps"
    MBPS = "Mbps"
    GBPS = "Gbps"
    TBPS = "Tbps"


class LockedVariable(Enum):
    """Which variable is held constant when the other two change."""
    RATE = "rate"
    PAYLOAD = "payload"
    VOLUME = "volume"


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


def bits_per_bandwidth_unit(unit: BandwidthUnit, mode: CalculationMode) -> Decimal:
    """Return the number of bits in one *unit* for the given mode."""
    # Bandwidth is usually base-10 even in exact mode, but some people use base-2.
    # For napkin math, base-10 (1000) is standard for bits/sec (e.g. 1 Gbps = 10^9 bps).
    exact_map = {
        BandwidthUnit.BPS: Decimal("1"),
        BandwidthUnit.KBPS: BYTES_PER_KB_EXACT,
        BandwidthUnit.MBPS: BYTES_PER_MB_EXACT,
        BandwidthUnit.GBPS: BYTES_PER_GB_EXACT,
        BandwidthUnit.TBPS: BYTES_PER_TB_EXACT,
    }
    estimate_map = {
        BandwidthUnit.BPS: Decimal("1"),
        BandwidthUnit.KBPS: BYTES_PER_KB_ESTIMATE,
        BandwidthUnit.MBPS: BYTES_PER_MB_ESTIMATE,
        BandwidthUnit.GBPS: BYTES_PER_GB_ESTIMATE,
        BandwidthUnit.TBPS: BYTES_PER_TB_ESTIMATE,
    }
    # Often telecom uses estimate map (base 10) for both, but we'll follow mode to be consistent.
    mapping = exact_map if mode == CalculationMode.EXACT else estimate_map
    return mapping[unit]


# ---------------------------------------------------------------------------
# Reference Tables
# ---------------------------------------------------------------------------

REFERENCE_NINES = [
    {"availability": "99% (Two 9s)", "year": "3.65 days", "month": "7.31 hours", "day": "14.4 mins"},
    {"availability": "99.9% (Three 9s)", "year": "8.77 hours", "month": "43.8 mins", "day": "1.44 mins"},
    {"availability": "99.99% (Four 9s)", "year": "52.6 mins", "month": "4.38 mins", "day": "8.64 secs"},
    {"availability": "99.999% (Five 9s)", "year": "5.26 mins", "month": "26.3 secs", "day": "864 ms"},
]

REFERENCE_LATENCY = [
    {"operation": "L1 cache reference", "latency": "0.5 ns", "cost": "Base"},
    {"operation": "L2 cache reference", "latency": "7 ns", "cost": "14x"},
    {"operation": "Main memory reference (RAM)", "latency": "100 ns", "cost": "20x L2, 200x L1"},
    {"operation": "Solid State Drive (SSD)", "latency": "150,000 ns (150 \u03bcs)", "cost": "1,500x RAM"},
    {"operation": "Disk Drive (HDD)", "latency": "10,000,000 ns (10 ms)", "cost": "66x SSD"},
    {"operation": "Round trip within datacenter", "latency": "500,000 ns (0.5 ms)", "cost": ""},
    {"operation": "Network round trip (cross country)", "latency": "150,000,000 ns (150 ms)", "cost": ""},
]
