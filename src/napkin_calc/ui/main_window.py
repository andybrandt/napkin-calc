"""Application main window – single scrollable layout with all panels."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import CalculationMode
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.ui.data_volume_panel import DataVolumePanel
from napkin_calc.ui.traffic_panel import TrafficPanel


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

        self._build_toolbar()
        self._build_central_area()
        self._update_mode_indicator()

    # -- toolbar ------------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Controls")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self._mode_button = QPushButton()
        self._mode_button.setCheckable(True)
        self._mode_button.setMinimumWidth(160)
        self._mode_button.clicked.connect(self._on_mode_toggled)
        toolbar.addWidget(self._mode_button)

        toolbar.addSeparator()

        self._mode_label = QLabel()
        self._mode_label.setStyleSheet("padding-left: 8px;")
        toolbar.addWidget(self._mode_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        reset_button = QPushButton("Reset All")
        reset_button.clicked.connect(self._on_reset)
        toolbar.addWidget(reset_button)

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

    def _on_reset(self) -> None:
        self._engine.reset()

    # -- central area (scrollable stack of all panels) ----------------------

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
