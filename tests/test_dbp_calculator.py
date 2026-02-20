"""Tests for DBPCalculator – Delay-Bandwidth Product logic."""

from decimal import Decimal

from napkin_calc.core.constants import BandwidthUnit, CalculationMode
from napkin_calc.core.dbp_calculator import DBPCalculator


class TestDBPCalculator:
    def test_bandwidth_and_rtt(self) -> None:
        calc = DBPCalculator()
        # 1 Gbps (estimate mode = 1,000,000,000 bps)
        calc.set_bandwidth(Decimal("1"), BandwidthUnit.GBPS, CalculationMode.ESTIMATE)
        calc.set_rtt(Decimal("100"))  # 100 ms

        # Data in flight = 1 Gbps * 0.1 sec = 100,000,000 bits = 12,500,000 bytes
        assert calc.data_in_flight_bytes == Decimal("12500000")

    def test_zero_rtt(self) -> None:
        calc = DBPCalculator()
        calc.set_bandwidth(Decimal("1"), BandwidthUnit.GBPS, CalculationMode.ESTIMATE)
        calc.set_rtt(Decimal("0"))
        assert calc.data_in_flight_bytes == Decimal("0")
