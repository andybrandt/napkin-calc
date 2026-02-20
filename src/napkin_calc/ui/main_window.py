"""Application main window – single scrollable layout with all panels."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import CalculationMode
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.persistence.scenario_manager import ScenarioManager
from napkin_calc.ui.data_volume_panel import DataVolumePanel
from napkin_calc.ui.traffic_panel import TrafficPanel

_FILE_FILTER = "Napkin Scenarios (*.npkn)"


class MainWindow(QMainWindow):
    """Top-level window for the Napkin Calculator application.

    All calculator sections are stacked vertically in a single
    scrollable view so that every value is visible at once during an
    interview -- no tabs, no hidden panels.
    """

    _WINDOW_TITLE = "Napkin Calculator – System Design Estimator"
    _DEFAULT_SIZE = (960, 700)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self._WINDOW_TITLE)
        self.resize(*self._DEFAULT_SIZE)

        self._engine = CalculationEngine(parent=self)
        self._scenario_manager = ScenarioManager(self._engine)
        self._last_save_dir = str(Path.home())

        self._build_toolbar()
        self._build_central_area()
        self._update_mode_indicator()

    # -- toolbar ------------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Controls")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Exact / Estimate toggle
        self._mode_button = QPushButton()
        self._mode_button.setCheckable(True)
        self._mode_button.setMinimumWidth(160)
        self._mode_button.clicked.connect(self._on_mode_toggled)
        toolbar.addWidget(self._mode_button)

        toolbar.addSeparator()

        self._mode_label = QLabel()
        self._mode_label.setStyleSheet("padding-left: 8px;")
        toolbar.addWidget(self._mode_label)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Save / Load / Reset
        save_button = QPushButton("Save Scenario")
        save_button.clicked.connect(self._on_save)
        toolbar.addWidget(save_button)

        load_button = QPushButton("Load Scenario")
        load_button.clicked.connect(self._on_load)
        toolbar.addWidget(load_button)

        toolbar.addSeparator()

        reset_button = QPushButton("Reset All")
        reset_button.clicked.connect(self._on_reset)
        toolbar.addWidget(reset_button)

    # -- mode toggle --------------------------------------------------------

    def _on_mode_toggled(self) -> None:
        self._engine.toggle_display_mode()
        self._update_mode_indicator()

    def _update_mode_indicator(self) -> None:
        is_exact = self._engine.display_mode == CalculationMode.EXACT
        self._mode_button.setChecked(is_exact)
        if is_exact:
            self._mode_button.setText("Mode: EXACT")
            self._mode_label.setText(
                "1 KB = 1,024 B  ·  1 month = 30.44 days  ·  1 year = 365.25 days"
            )
        else:
            self._mode_button.setText("Mode: ESTIMATE")
            self._mode_label.setText(
                "1 KB = 1,000 B  ·  1 month = 30 days  ·  1 year = 365 days"
            )

    # -- save / load --------------------------------------------------------

    def _on_save(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Scenario",
            self._last_save_dir,
            _FILE_FILTER,
        )
        if not file_path:
            return

        path = Path(file_path)
        if path.suffix != ".npkn":
            path = path.with_suffix(".npkn")

        self._last_save_dir = str(path.parent)

        try:
            self._scenario_manager.save(path, scenario_name=path.stem)
        except OSError as exc:
            QMessageBox.warning(self, "Save Failed", str(exc))

    def _on_load(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Scenario",
            self._last_save_dir,
            _FILE_FILTER,
        )
        if not file_path:
            return

        path = Path(file_path)
        self._last_save_dir = str(path.parent)

        try:
            scenario_name = self._scenario_manager.load(path)
            if scenario_name:
                self.setWindowTitle(
                    f"{self._WINDOW_TITLE}  —  {scenario_name}"
                )
            self._update_mode_indicator()
        except (OSError, KeyError, ValueError) as exc:
            QMessageBox.warning(self, "Load Failed", str(exc))

    # -- reset --------------------------------------------------------------

    def _on_reset(self) -> None:
        self._engine.reset()
        self.setWindowTitle(self._WINDOW_TITLE)

    # -- central area -------------------------------------------------------

    def _build_central_area(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        layout.addWidget(TrafficPanel(self._engine))
        layout.addWidget(DataVolumePanel(self._engine))

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.setCentralWidget(scroll)
