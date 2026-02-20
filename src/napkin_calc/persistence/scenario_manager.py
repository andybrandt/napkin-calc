"""Save and load calculator state to/from .npkn files (JSON internally).

A scenario captures the full engine state so it can be restored later.
This lets users build a library of standard interview scenarios
(e.g. "Chat App", "Video Streaming") and switch between them.

File format (``.npkn``, JSON content)::

    {
        "napkin_calc_version": "0.1.0",
        "scenario_name": "My Chat App",
        "events_per_second": "115.7407407407407407407407407",
        "payload_size_bytes": "400",
        "display_mode": "estimate"
    }
"""

import json
from decimal import Decimal
from pathlib import Path

from napkin_calc.core.constants import CalculationMode, DataSizeUnit, TimeUnit
from napkin_calc.core.engine import CalculationEngine

_FORMAT_VERSION = "0.1.0"


class ScenarioManager:
    """Serialize / deserialize ``CalculationEngine`` state to JSON."""

    def __init__(self, engine: CalculationEngine) -> None:
        self._engine = engine

    # -- save ---------------------------------------------------------------

    def save(self, path: Path, scenario_name: str = "") -> None:
        """Write the current engine state to *path* as JSON."""
        data = {
            "napkin_calc_version": _FORMAT_VERSION,
            "scenario_name": scenario_name,
            "events_per_second": str(self._engine.events_per_second_exact),
            "payload_size_bytes": str(self._engine.payload_size_bytes),
            "display_mode": self._engine.display_mode.value,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -- load ---------------------------------------------------------------

    def load(self, path: Path) -> str:
        """Restore engine state from *path*.

        Returns the scenario name stored in the file (may be empty).
        """
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)

        events_per_second = Decimal(data["events_per_second"])
        payload_size_bytes = Decimal(data["payload_size_bytes"])
        display_mode = CalculationMode(data.get("display_mode", "estimate"))

        # Restore rate by setting events/sec directly via the SECOND unit
        self._engine.set_rate(events_per_second, TimeUnit.SECOND)

        # Restore payload as raw bytes
        self._engine.set_payload_size(payload_size_bytes, DataSizeUnit.BYTE)

        # Restore display mode
        self._engine.set_display_mode(display_mode)

        return data.get("scenario_name", "")

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def to_dict(engine: CalculationEngine, scenario_name: str = "") -> dict:
        """Return the engine state as a plain dict (useful for testing)."""
        return {
            "napkin_calc_version": _FORMAT_VERSION,
            "scenario_name": scenario_name,
            "events_per_second": str(engine.events_per_second_exact),
            "payload_size_bytes": str(engine.payload_size_bytes),
            "display_mode": engine.display_mode.value,
        }
