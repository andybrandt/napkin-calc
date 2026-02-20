"""Tests for TimeUnitConverter – the core rate conversion logic."""

from decimal import Decimal

import pytest

from napkin_calc.core.constants import CalculationMode, TimeUnit
from napkin_calc.core.time_converter import TimeUnitConverter


class TestSetAndGetRate:
    """Setting a rate in one unit and reading it back in others."""

    def test_set_per_day_read_per_second(self) -> None:
        converter = TimeUnitConverter()
        # 86,400 events per day  =  1 event per second (exact)
        converter.set_rate(Decimal("86400"), TimeUnit.DAY)
        result = converter.get_rate(TimeUnit.SECOND, CalculationMode.EXACT)
        assert result == Decimal("1")

    def test_set_per_second_read_per_minute(self) -> None:
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("100"), TimeUnit.SECOND)
        result = converter.get_rate(TimeUnit.MINUTE, CalculationMode.EXACT)
        assert result == Decimal("6000")

    def test_set_per_hour_read_per_day(self) -> None:
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("1000"), TimeUnit.HOUR)
        result = converter.get_rate(TimeUnit.DAY, CalculationMode.EXACT)
        assert result == Decimal("24000")

    def test_ten_million_per_day_requirements_example(self) -> None:
        """FR2 example: 10 million requests/day -> various units."""
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("10000000"), TimeUnit.DAY)

        per_second = converter.get_rate(TimeUnit.SECOND, CalculationMode.EXACT)
        # 10_000_000 / 86400 ≈ 115.7407…
        assert abs(per_second - Decimal("115.7407")) < Decimal("0.001")

        per_hour = converter.get_rate(TimeUnit.HOUR, CalculationMode.EXACT)
        # 10_000_000 / 24 ≈ 416666.67
        assert abs(per_hour - Decimal("416666.67")) < Decimal("0.01")


class TestExactVsEstimate:
    """Verify that estimate mode uses rounded conversion factors."""

    def test_per_month_exact_vs_estimate(self) -> None:
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("1"), TimeUnit.SECOND)

        exact_month = converter.get_rate(TimeUnit.MONTH, CalculationMode.EXACT)
        estimate_month = converter.get_rate(TimeUnit.MONTH, CalculationMode.ESTIMATE)

        # Exact: 1 month = 2,629,800 seconds (30.4375 days)
        assert exact_month == Decimal("2629800")
        # Estimate: 1 month = 2,592,000 seconds (30 days)
        assert estimate_month == Decimal("2592000")

    def test_per_year_exact_vs_estimate(self) -> None:
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("1"), TimeUnit.SECOND)

        exact_year = converter.get_rate(TimeUnit.YEAR, CalculationMode.EXACT)
        estimate_year = converter.get_rate(TimeUnit.YEAR, CalculationMode.ESTIMATE)

        assert exact_year == Decimal("31557600")    # 365.25 days
        assert estimate_year == Decimal("31536000")  # 365 days


class TestGetAllRates:
    """get_all_rates should return a dict covering every TimeUnit."""

    def test_returns_all_units(self) -> None:
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("1"), TimeUnit.SECOND)
        rates = converter.get_all_rates(CalculationMode.EXACT)
        assert set(rates.keys()) == set(TimeUnit)


class TestReset:
    """reset() should zero out the internal state."""

    def test_reset_zeroes_rate(self) -> None:
        converter = TimeUnitConverter()
        converter.set_rate(Decimal("1000"), TimeUnit.SECOND)
        converter.reset()
        assert converter.events_per_second == Decimal("0")
