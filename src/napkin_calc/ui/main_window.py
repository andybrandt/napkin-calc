"""Application main window – toolbar, tabs, and global controls."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QToolBar,
    QWidget,
)

from napkin_calc.core.constants import CalculationMode
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.ui.traffic_panel import TrafficPanel


class MainWindow(QMainWindow):
    """Top-level window for the Napkin Calculator application."""

    _WINDOW_TITLE = "Napkin Calculator – System Design Estimator"
    _DEFAULT_SIZE = (900, 600)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self._WINDOW_TITLE)
        self.resize(*self._DEFAULT_SIZE)

        # Shared engine used by all panels
        self._engine = CalculationEngine(parent=self)

        self._build_toolbar()
        self._build_tabs()
        self._update_mode_indicator()

    # -- toolbar ------------------------------------------------------------

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Controls")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Exact / Estimate toggle button
        self._mode_button = QPushButton()
        self._mode_button.setCheckable(True)
        self._mode_button.setMinimumWidth(160)
        self._mode_button.clicked.connect(self._on_mode_toggled)
        toolbar.addWidget(self._mode_button)

        toolbar.addSeparator()

        # Mode description label
        self._mode_label = QLabel()
        self._mode_label.setStyleSheet("padding-left: 8px; color: #666;")
        toolbar.addWidget(self._mode_label)

        # Spacer to push the reset button to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Reset button
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

    # -- tabs ---------------------------------------------------------------

    def _build_tabs(self) -> None:
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        # Phase 1: Traffic panel only
        traffic_panel = TrafficPanel(self._engine)
        self._tabs.addTab(traffic_panel, "Traffic && Throughput")
