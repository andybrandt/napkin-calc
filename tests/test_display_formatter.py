"""Tests for DisplayFormatter – number formatting and scientific notation."""

from decimal import Decimal

import pytest

from napkin_calc.formatting.display_formatter import DisplayFormatter


class TestFormatValue:
    """format_value produces comma-separated numbers with 10^x annotations."""

    def test_zero(self) -> None:
        assert DisplayFormatter.format_value(Decimal("0")) == "0"

    def test_small_integer(self) -> None:
        result = DisplayFormatter.format_value(Decimal("42"))
        assert result == "42"

    def test_thousands_separator(self) -> None:
        result = DisplayFormatter.format_value(Decimal("1000000"))
        assert "1,000,000" in result

    def test_scientific_notation_for_million(self) -> None:
        result = DisplayFormatter.format_value(Decimal("1000000"))
        assert "10^6" in result

    def test_no_scientific_notation_below_threshold(self) -> None:
        result = DisplayFormatter.format_value(Decimal("999"))
        assert "10^" not in result

    def test_scientific_notation_at_threshold(self) -> None:
        result = DisplayFormatter.format_value(Decimal("1000"))
        assert "10^3" in result

    def test_decimal_fraction(self) -> None:
        result = DisplayFormatter.format_value(Decimal("115.7407"))
        # Should show a reasonable number of decimals, no 10^x
        assert "115" in result
        assert "10^" not in result

    def test_billion_annotation(self) -> None:
        result = DisplayFormatter.format_value(Decimal("1000000000"))
        assert "10^9" in result


class TestFormatInput:
    """format_input should NOT include scientific notation annotations."""

    def test_large_number_no_annotation(self) -> None:
        result = DisplayFormatter.format_input(Decimal("1000000"))
        assert "10^" not in result
        assert "1,000,000" in result

    def test_zero(self) -> None:
        assert DisplayFormatter.format_input(Decimal("0")) == "0"
