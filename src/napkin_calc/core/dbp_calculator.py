"""Delay-Bandwidth Product (DBP) calculator."""

from decimal import Decimal

from napkin_calc.core.constants import BandwidthUnit, CalculationMode, bits_per_bandwidth_unit


class DBPCalculator:
    """Calculate the Delay-Bandwidth Product (data in flight)."""

    def __init__(self) -> None:
        self._bandwidth_bits_per_sec = Decimal("0")
        self._rtt_ms = Decimal("0")

    def set_bandwidth(self, value: Decimal, unit: BandwidthUnit, mode: CalculationMode) -> None:
        """Set the bandwidth in the given unit (mode dictates base 10 or base 2)."""
        self._bandwidth_bits_per_sec = value * bits_per_bandwidth_unit(unit, mode)

    def set_rtt(self, rtt_ms: Decimal) -> None:
        """Set the Round-Trip Time (RTT) in milliseconds."""
        self._rtt_ms = rtt_ms

    @property
    def data_in_flight_bytes(self) -> Decimal:
        """Data in flight (DBP) in bytes."""
        # DBP bits = bandwidth (bits/sec) * rtt (sec)
        rtt_sec = self._rtt_ms / Decimal("1000")
        dbp_bits = self._bandwidth_bits_per_sec * rtt_sec
        return dbp_bits / Decimal("8")
