"""Tests for ScenarioManager – JSON save/load round-trip."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from napkin_calc.core.constants import CalculationMode, DataSizeUnit, TimeUnit
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.persistence.scenario_manager import ScenarioManager


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture()
def engine(qapp) -> CalculationEngine:
    return CalculationEngine()


@pytest.fixture()
def manager(engine) -> ScenarioManager:
    return ScenarioManager(engine)


class TestSaveLoad:
    """Save state to a file, load it back, verify everything matches."""

    def test_round_trip_preserves_rate(
        self, engine: CalculationEngine, manager: ScenarioManager, tmp_path: Path
    ) -> None:
        engine.set_rate(Decimal("10000000"), TimeUnit.DAY)
        file = tmp_path / "test.npkn"
        manager.save(file)

        # Create a fresh engine and load into it
        fresh_engine = CalculationEngine()
        fresh_manager = ScenarioManager(fresh_engine)
        fresh_manager.load(file)

        assert abs(
            fresh_engine.events_per_second_exact - engine.events_per_second_exact
        ) < Decimal("0.0001")

    def test_round_trip_preserves_payload(
        self, engine: CalculationEngine, manager: ScenarioManager, tmp_path: Path
    ) -> None:
        engine.set_payload_size(Decimal("400"), DataSizeUnit.BYTE)
        file = tmp_path / "test.npkn"
        manager.save(file)

        fresh_engine = CalculationEngine()
        ScenarioManager(fresh_engine).load(file)

        assert fresh_engine.payload_size_bytes == Decimal("400")

    def test_round_trip_preserves_display_mode(
        self, engine: CalculationEngine, manager: ScenarioManager, tmp_path: Path
    ) -> None:
        engine.set_display_mode(CalculationMode.EXACT)
        file = tmp_path / "test.npkn"
        manager.save(file)

        fresh_engine = CalculationEngine()
        ScenarioManager(fresh_engine).load(file)

        assert fresh_engine.display_mode == CalculationMode.EXACT

    def test_round_trip_full_scenario(
        self, engine: CalculationEngine, manager: ScenarioManager, tmp_path: Path
    ) -> None:
        """End-to-end: set rate + payload + mode, save, load, verify all."""
        engine.set_rate(Decimal("5000000"), TimeUnit.DAY)
        engine.set_payload_size(Decimal("2"), DataSizeUnit.KILOBYTE)
        engine.set_display_mode(CalculationMode.EXACT)

        file = tmp_path / "full_scenario.npkn"
        manager.save(file, scenario_name="Chat App")

        fresh_engine = CalculationEngine()
        fresh_manager = ScenarioManager(fresh_engine)
        name = fresh_manager.load(file)

        assert name == "Chat App"
        assert fresh_engine.display_mode == CalculationMode.EXACT
        assert fresh_engine.payload_size_bytes == Decimal("2048")
        assert abs(
            fresh_engine.events_per_second_exact - engine.events_per_second_exact
        ) < Decimal("0.0001")


class TestFileFormat:
    """Verify the JSON file structure."""

    def test_saved_file_is_valid_json(
        self, engine: CalculationEngine, manager: ScenarioManager, tmp_path: Path
    ) -> None:
        engine.set_rate(Decimal("1000"), TimeUnit.SECOND)
        file = tmp_path / "test.npkn"
        manager.save(file)

        data = json.loads(file.read_text())
        assert "napkin_calc_version" in data
        assert "events_per_second" in data
        assert "payload_size_bytes" in data
        assert "display_mode" in data

    def test_scenario_name_stored(
        self, engine: CalculationEngine, manager: ScenarioManager, tmp_path: Path
    ) -> None:
        file = tmp_path / "named.npkn"
        manager.save(file, scenario_name="Video Streaming")

        data = json.loads(file.read_text())
        assert data["scenario_name"] == "Video Streaming"


class TestToDict:
    """to_dict helper for programmatic access."""

    def test_returns_expected_keys(self, engine: CalculationEngine) -> None:
        result = ScenarioManager.to_dict(engine)
        assert set(result.keys()) == {
            "napkin_calc_version",
            "scenario_name",
            "events_per_second",
            "payload_size_bytes",
            "display_mode",
        }

    def test_values_are_strings(self, engine: CalculationEngine) -> None:
        engine.set_rate(Decimal("100"), TimeUnit.SECOND)
        result = ScenarioManager.to_dict(engine, scenario_name="Test")
        assert result["scenario_name"] == "Test"
        assert result["events_per_second"] == "100"
