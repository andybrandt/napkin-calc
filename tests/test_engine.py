"""Tests for CalculationEngine – signal-based reactive model.

These tests require a QApplication instance because the engine is a QObject.
"""

from decimal import Decimal

import pytest

from napkin_calc.core.constants import CalculationMode, DataSizeUnit, LockedVariable, TimeUnit
from napkin_calc.core.engine import CalculationEngine


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication for the entire test module.

    PySide6 requires exactly one QApplication per process.
    """
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture()
def engine(qapp) -> CalculationEngine:
    """Fresh engine for each test."""
    return CalculationEngine()


class TestDisplayMode:
    def test_default_mode_is_exact(self, engine: CalculationEngine) -> None:
        assert engine.display_mode == CalculationMode.EXACT

    def test_toggle_switches_to_estimate(self, engine: CalculationEngine) -> None:
        engine.toggle_display_mode()
        assert engine.display_mode == CalculationMode.ESTIMATE

    def test_toggle_back_to_exact(self, engine: CalculationEngine) -> None:
        engine.toggle_display_mode()  # -> ESTIMATE
        engine.toggle_display_mode()  # -> EXACT
        assert engine.display_mode == CalculationMode.EXACT

    def test_mode_changed_signal_fires(self, engine: CalculationEngine) -> None:
        signal_received = []
        engine.mode_changed.connect(lambda: signal_received.append(True))
        engine.toggle_display_mode()
        assert len(signal_received) == 1


class TestRateOperations:
    def test_set_and_get_rate(self, engine: CalculationEngine) -> None:
        engine.set_rate(Decimal("86400"), TimeUnit.DAY)
        result = engine.get_rate(TimeUnit.SECOND)
        # In estimate mode, second->day = 86400 (same as exact)
        # so 86400/86400 * 1 = 1
        # Actually get_rate uses display_mode which defaults to ESTIMATE
        # For SECOND, exact and estimate are the same
        assert abs(result - Decimal("1")) < Decimal("0.001")

    def test_rates_changed_signal_fires(self, engine: CalculationEngine) -> None:
        signal_received = []
        engine.rates_changed.connect(lambda: signal_received.append(True))
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        assert len(signal_received) == 1

    def test_reset_zeros_and_signals(self, engine: CalculationEngine) -> None:
        engine.set_rate(Decimal("1000"), TimeUnit.SECOND)
        signal_received = []
        engine.rates_changed.connect(lambda: signal_received.append(True))
        engine.reset()
        assert engine.events_per_second_exact == Decimal("0")
        assert len(signal_received) == 1

    def test_get_rate_exact_always_uses_exact_factors(
        self, engine: CalculationEngine
    ) -> None:
        engine.set_rate(Decimal("1"), TimeUnit.SECOND)
        exact_month = engine.get_rate_exact(TimeUnit.MONTH)
        assert exact_month == Decimal("2629800")

    def test_set_rate_also_fires_storage_changed(
        self, engine: CalculationEngine
    ) -> None:
        signal_received = []
        engine.storage_changed.connect(lambda: signal_received.append(True))
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        assert len(signal_received) == 1


class TestPayloadAndStorage:
    """Payload size and data throughput calculations."""

    def test_set_payload_size_in_kb(self, engine: CalculationEngine) -> None:
        engine.set_payload_size(Decimal("1"), DataSizeUnit.KILOBYTE)
        assert engine.payload_size_bytes == Decimal("1024")

    def test_storage_changed_signal_on_payload(
        self, engine: CalculationEngine
    ) -> None:
        signal_received = []
        engine.storage_changed.connect(lambda: signal_received.append(True))
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        assert len(signal_received) == 1

    def test_data_throughput_bytes_per_second(
        self, engine: CalculationEngine
    ) -> None:
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        # 100 events/sec * 500 bytes = 50,000 bytes/sec
        assert engine.data_throughput_bytes_per_second == Decimal("50000")

    def test_data_throughput_per_day(self, engine: CalculationEngine) -> None:
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        # 50,000 B/sec * 86,400 sec/day (estimate) = 4,320,000,000 B/day
        bytes_per_day = engine.get_data_throughput_bytes(TimeUnit.DAY)
        assert bytes_per_day == Decimal("4320000000")

    def test_data_throughput_in_gb(self, engine: CalculationEngine) -> None:
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        gb_per_day = engine.get_data_throughput(TimeUnit.DAY, DataSizeUnit.GIGABYTE)
        # 4,320,000,000 / 1,073,741,824 ≈ 4.02 GB (exact mode)
        assert abs(gb_per_day - Decimal("4.02")) < Decimal("0.01")

    def test_best_unit_selection(self, engine: CalculationEngine) -> None:
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        value, unit = engine.get_data_throughput_best_unit(TimeUnit.DAY)
        # ~4.02 GB/day (exact) → best unit should be GB
        assert unit == DataSizeUnit.GIGABYTE
        assert abs(value - Decimal("4.02")) < Decimal("0.01")

    def test_reset_clears_payload(self, engine: CalculationEngine) -> None:
        engine.set_payload_size(Decimal("1"), DataSizeUnit.MEGABYTE)
        engine.reset()
        assert engine.payload_size_bytes == Decimal("0")
        assert engine.data_throughput_bytes_per_second == Decimal("0")

    def test_target_with_rate_locked_solves_payload(self, engine: CalculationEngine) -> None:
        """Lock Rate, set rate, enter target -> Payload is back-calculated."""
        engine.set_locked_variable(LockedVariable.RATE)
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        engine.set_target_throughput(Decimal("50"), DataSizeUnit.KILOBYTE, TimeUnit.SECOND)
        assert engine.payload_size_bytes == Decimal("512")
        assert engine.events_per_second_exact == Decimal("100")

    def test_target_with_payload_locked_solves_rate(self, engine: CalculationEngine) -> None:
        """Lock Payload, set payload, enter target -> Rate is back-calculated."""
        engine.set_locked_variable(LockedVariable.PAYLOAD)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        engine.set_target_throughput(Decimal("50"), DataSizeUnit.KILOBYTE, TimeUnit.SECOND)
        assert engine.events_per_second_exact == Decimal("102.4")
        assert engine.payload_size_bytes == Decimal("500")

    def test_target_stored_when_both_zero(self, engine: CalculationEngine) -> None:
        """Neither rate nor payload known -- target stored for later."""
        engine.set_target_throughput(Decimal("1"), DataSizeUnit.KILOBYTE, TimeUnit.SECOND)
        assert engine.events_per_second_exact == Decimal("0")
        assert engine.payload_size_bytes == Decimal("0")
        assert engine.pending_target_bytes_per_second == Decimal("1024")

    def test_stored_target_resolves_when_rate_provided(self, engine: CalculationEngine) -> None:
        """Stored target + user enters rate -> payload is calculated (default lock=VOLUME)."""
        engine.set_target_throughput(Decimal("50"), DataSizeUnit.KILOBYTE, TimeUnit.SECOND)
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        # Volume locked (default), rate just set, so payload = 51200 / 100 = 512
        assert engine.payload_size_bytes == Decimal("512")

    def test_stored_target_resolves_when_payload_provided(self, engine: CalculationEngine) -> None:
        """Stored target + lock Payload + user enters payload -> rate calculated."""
        engine.set_locked_variable(LockedVariable.PAYLOAD)
        engine.set_target_throughput(Decimal("50"), DataSizeUnit.KILOBYTE, TimeUnit.SECOND)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        # Payload locked, so rate = 51200 / 500 = 102.4
        assert engine.events_per_second_exact == Decimal("102.4")

    def test_throughput_grid_shows_target_while_unresolved(self, engine: CalculationEngine) -> None:
        """Data throughput should reflect the target even before resolution."""
        engine.set_target_throughput(Decimal("1"), DataSizeUnit.TERABYTE, TimeUnit.DAY)
        bytes_per_day = engine.get_data_throughput_bytes(TimeUnit.DAY)
        assert bytes_per_day == Decimal("1099511627776")

    def test_volume_locked_edit_rate_recalculates_payload(self, engine: CalculationEngine) -> None:
        """Lock=Volume, set all three, then change rate -> payload adjusts."""
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        engine.set_payload_size(Decimal("500"), DataSizeUnit.BYTE)
        # Store the volume: 100 * 500 = 50000 bps
        engine.set_target_throughput(Decimal("50000"), DataSizeUnit.BYTE, TimeUnit.SECOND)
        # Now change rate to 200 with Volume locked
        engine.set_rate(Decimal("200"), TimeUnit.SECOND)
        # Payload should adjust: 50000 / 200 = 250
        assert engine.payload_size_bytes == Decimal("250")
        assert engine.events_per_second_exact == Decimal("200")
