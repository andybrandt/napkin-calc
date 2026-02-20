"""Application main window – single scrollable layout with all panels."""

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from napkin_calc.core.constants import CalculationMode
from napkin_calc.core.engine import CalculationEngine
from napkin_calc.persistence.scenario_manager import ScenarioManager
from napkin_calc.ui.data_volume_panel import DataVolumePanel
from napkin_calc.ui.theme import apply_dark, apply_light, is_dark
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

        # Exact / Estimate toggle (text button – always visible)
        self._mode_button = QPushButton()
        self._mode_button.setCheckable(True)
        self._mode_button.setMinimumWidth(160)
        self._mode_button.clicked.connect(self._on_mode_toggled)
        toolbar.addWidget(self._mode_button)

        toolbar.addSeparator()

        # Mode description – visible at normal widths
        self._mode_label = QLabel()
        self._mode_label.setContentsMargins(8, 0, 0, 0)
        toolbar.addWidget(self._mode_label)

        # Spacer pushes action buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer)

        # Theme toggle (sun / moon)
        self._theme_button = QToolButton()
        self._theme_button.setToolTip("Toggle light / dark theme")
        self._theme_button.clicked.connect(self._on_theme_toggled)
        self._update_theme_icon()
        toolbar.addWidget(self._theme_button)

        toolbar.addSeparator()

        # Icon buttons for Save / Load / Reset (refs kept for icon refresh)
        self._save_button = QToolButton()
        self._save_button.setToolTip("Save scenario (.npkn)")
        self._save_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._save_button.clicked.connect(self._on_save)
        toolbar.addWidget(self._save_button)

        self._load_button = QToolButton()
        self._load_button.setToolTip("Load scenario (.npkn)")
        self._load_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._load_button.clicked.connect(self._on_load)
        toolbar.addWidget(self._load_button)

        toolbar.addSeparator()

        self._reset_button = QToolButton()
        self._reset_button.setToolTip("Reset all fields to zero")
        self._reset_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._reset_button.clicked.connect(self._on_reset)
        toolbar.addWidget(self._reset_button)

        self._refresh_toolbar_icons()

    @staticmethod
    def _inverted_icon(icon: QIcon, size: int = 24) -> QIcon:
        """Return a color-inverted copy of *icon* (dark glyphs become light)."""
        pixmap = icon.pixmap(QSize(size, size))
        image = pixmap.toImage()
        image.invertPixels(QImage.InvertMode.InvertRgb)
        return QIcon(QPixmap.fromImage(image))

    def _refresh_toolbar_icons(self) -> None:
        """Re-set toolbar icons for the current theme.

        Save and Load work in both themes.  The Reset icon is
        color-inverted in dark mode so it stays visible.
        """
        style = self.style()
        self._save_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DriveFDIcon))
        self._load_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        reset_icon = style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        if is_dark():
            reset_icon = self._inverted_icon(reset_icon)
        self._reset_button.setIcon(reset_icon)

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
                "1 KB = 1,024 B  \u00b7  1 month = 30.44 days  \u00b7  1 year = 365.25 days"
            )
        else:
            self._mode_button.setText("Mode: ESTIMATE")
            self._mode_label.setText(
                "1 KB = 1,000 B  \u00b7  1 month = 30 days  \u00b7  1 year = 365 days"
            )

    # -- theme toggle -------------------------------------------------------

    def _on_theme_toggled(self) -> None:
        if is_dark():
            apply_light()
        else:
            apply_dark()
        self._refresh_toolbar_icons()
        self._update_theme_icon()

    def _update_theme_icon(self) -> None:
        if is_dark():
            self._theme_button.setText("\u2600")   # sun – click to go light
            self._theme_button.setToolTip("Switch to light theme")
        else:
            self._theme_button.setText("\u263d")   # crescent moon – click to go dark
            self._theme_button.setToolTip("Switch to dark theme")

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
                    f"{self._WINDOW_TITLE}  \u2014  {scenario_name}"
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
