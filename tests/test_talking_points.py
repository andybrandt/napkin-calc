"""Tests for TalkingPointGenerator – human-friendly magnitude phrases."""

from decimal import Decimal

from napkin_calc.formatting.talking_points import TalkingPointGenerator


class TestTalkingPointGenerator:
    """Generate speakable phrases at various magnitudes."""

    def test_zero(self) -> None:
        assert TalkingPointGenerator.generate(Decimal("0")) == "0"

    def test_small_value(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("42"))
        assert result == "~42"

    def test_small_fractional(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("3.7"))
        assert result == "~3.7"

    def test_thousands(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("6944"))
        assert "thousand" in result
        assert "6.9" in result

    def test_exact_thousand(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("1000"))
        assert result == "1 thousand"

    def test_millions(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("10000000"))
        assert result == "10 million"

    def test_millions_approximate(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("4500000"))
        assert "million" in result
        assert "4.5" in result

    def test_billions(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("3650000000"))
        assert "billion" in result
        assert "3.7" in result or "3.6" in result

    def test_exact_billion(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("1000000000"))
        assert result == "1 billion"

    def test_trillions(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("2500000000000"))
        assert "trillion" in result
        assert "2.5" in result

    def test_sub_ten_keeps_decimal(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("0.12"))
        assert result == "~0.1"

    def test_hundred_rounds_to_whole(self) -> None:
        result = TalkingPointGenerator.generate(Decimal("116"))
        assert result == "~116"
