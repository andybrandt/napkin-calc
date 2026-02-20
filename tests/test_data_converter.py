"""Tests for DataSizeConverter – data-size unit conversions."""

from decimal import Decimal

from napkin_calc.core.constants import CalculationMode, DataSizeUnit
from napkin_calc.core.data_converter import DataSizeConverter


class TestSetAndGetSize:
    """Setting a size in one unit and reading it back in others."""

    def test_set_kb_get_bytes_exact(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("1"), DataSizeUnit.KILOBYTE)
        assert converter.get_size(DataSizeUnit.BYTE, CalculationMode.EXACT) == Decimal("1024")

    def test_set_kb_get_bytes_estimate(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("1"), DataSizeUnit.KILOBYTE)
        # Stored as 1024 bytes (exact); displayed as 1024/1000 = 1.024 KB in estimate
        result = converter.get_size(DataSizeUnit.KILOBYTE, CalculationMode.ESTIMATE)
        assert result == Decimal("1.024")

    def test_set_gb_get_mb_exact(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("1"), DataSizeUnit.GIGABYTE)
        result = converter.get_size(DataSizeUnit.MEGABYTE, CalculationMode.EXACT)
        assert result == Decimal("1024")

    def test_set_gb_get_mb_estimate(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("1"), DataSizeUnit.GIGABYTE)
        # 1 GB exact = 1,073,741,824 B; in estimate MB = 1,000,000
        result = converter.get_size(DataSizeUnit.MEGABYTE, CalculationMode.ESTIMATE)
        assert abs(result - Decimal("1073.741824")) < Decimal("0.001")


class TestBestUnit:
    """best_unit should pick the largest unit where value >= 1."""

    def test_bytes_stay_bytes(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("500"), DataSizeUnit.BYTE)
        assert converter.best_unit(CalculationMode.ESTIMATE) == DataSizeUnit.BYTE

    def test_one_kb(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("1"), DataSizeUnit.KILOBYTE)
        assert converter.best_unit(CalculationMode.EXACT) == DataSizeUnit.KILOBYTE

    def test_large_value_picks_tb(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("5"), DataSizeUnit.TERABYTE)
        assert converter.best_unit(CalculationMode.ESTIMATE) == DataSizeUnit.TERABYTE

    def test_zero_falls_back_to_byte(self) -> None:
        converter = DataSizeConverter()
        assert converter.best_unit(CalculationMode.EXACT) == DataSizeUnit.BYTE


class TestGetAllSizes:
    """get_all_sizes should return a dict covering every DataSizeUnit."""

    def test_returns_all_units(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("1"), DataSizeUnit.GIGABYTE)
        sizes = converter.get_all_sizes(CalculationMode.EXACT)
        assert set(sizes.keys()) == set(DataSizeUnit)


class TestReset:
    def test_reset_zeroes_size(self) -> None:
        converter = DataSizeConverter()
        converter.set_size(Decimal("100"), DataSizeUnit.MEGABYTE)
        converter.reset()
        assert converter.size_in_bytes == Decimal("0")
