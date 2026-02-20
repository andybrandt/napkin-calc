"""Light / dark theme support.

Uses the Qt "Fusion" style which fully respects QPalette overrides.
At startup the system palette is preserved; the user can then toggle
between an explicit light and dark palette.

Every color role is set for every color group (All + Disabled) so that
no colors are inherited from the previous palette or from Qt's
automatic derivation.
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


_is_dark = False


def init_theme() -> None:
    """Call once at startup, before creating any widgets."""
    global _is_dark
    QApplication.setStyle("Fusion")
    window_color = QApplication.palette().color(QPalette.ColorRole.Window)
    _is_dark = window_color.lightness() < 128


def _set_all(palette: QPalette, role: QPalette.ColorRole, color: QColor) -> None:
    """Set *color* for *role* across Active, Inactive, and Disabled groups."""
    palette.setColor(QPalette.ColorGroup.Active, role, color)
    palette.setColor(QPalette.ColorGroup.Inactive, role, color)
    palette.setColor(QPalette.ColorGroup.Disabled, role, color)


# ---------------------------------------------------------------------------
# Light palette
# ---------------------------------------------------------------------------

def _build_light_palette() -> QPalette:
    palette = QPalette()

    black = QColor(0, 0, 0)
    white = QColor(255, 255, 255)
    light_grey = QColor(240, 240, 240)
    disabled = QColor(150, 150, 150)

    _set_all(palette, QPalette.ColorRole.Window, light_grey)
    _set_all(palette, QPalette.ColorRole.WindowText, black)
    _set_all(palette, QPalette.ColorRole.Base, white)
    _set_all(palette, QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    _set_all(palette, QPalette.ColorRole.Text, black)
    _set_all(palette, QPalette.ColorRole.Button, light_grey)
    _set_all(palette, QPalette.ColorRole.ButtonText, black)
    _set_all(palette, QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    _set_all(palette, QPalette.ColorRole.ToolTipText, black)
    _set_all(palette, QPalette.ColorRole.BrightText, QColor(200, 0, 0))
    _set_all(palette, QPalette.ColorRole.Link, QColor(40, 100, 180))
    _set_all(palette, QPalette.ColorRole.Highlight, QColor(50, 120, 200))
    _set_all(palette, QPalette.ColorRole.HighlightedText, white)
    _set_all(palette, QPalette.ColorRole.PlaceholderText, QColor(160, 160, 160))
    _set_all(palette, QPalette.ColorRole.Light, white)
    _set_all(palette, QPalette.ColorRole.Midlight, QColor(220, 220, 220))
    _set_all(palette, QPalette.ColorRole.Mid, QColor(180, 180, 180))
    _set_all(palette, QPalette.ColorRole.Dark, QColor(160, 160, 160))
    _set_all(palette, QPalette.ColorRole.Shadow, QColor(100, 100, 100))

    # Disabled overrides
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)

    return palette


# ---------------------------------------------------------------------------
# Dark palette
# ---------------------------------------------------------------------------

def _build_dark_palette() -> QPalette:
    palette = QPalette()

    white_text = QColor(230, 230, 230)
    disabled_text = QColor(120, 120, 120)

    _set_all(palette, QPalette.ColorRole.Window, QColor(45, 45, 45))
    _set_all(palette, QPalette.ColorRole.WindowText, white_text)
    _set_all(palette, QPalette.ColorRole.Base, QColor(35, 35, 35))
    _set_all(palette, QPalette.ColorRole.AlternateBase, QColor(55, 55, 55))
    _set_all(palette, QPalette.ColorRole.Text, white_text)
    _set_all(palette, QPalette.ColorRole.Button, QColor(55, 55, 55))
    _set_all(palette, QPalette.ColorRole.ButtonText, white_text)
    _set_all(palette, QPalette.ColorRole.ToolTipBase, QColor(70, 70, 70))
    _set_all(palette, QPalette.ColorRole.ToolTipText, white_text)
    _set_all(palette, QPalette.ColorRole.BrightText, QColor(255, 80, 80))
    _set_all(palette, QPalette.ColorRole.Link, QColor(100, 170, 240))
    _set_all(palette, QPalette.ColorRole.Highlight, QColor(80, 140, 210))
    _set_all(palette, QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    _set_all(palette, QPalette.ColorRole.PlaceholderText, disabled_text)
    _set_all(palette, QPalette.ColorRole.Light, QColor(90, 90, 90))
    _set_all(palette, QPalette.ColorRole.Midlight, QColor(70, 70, 70))
    _set_all(palette, QPalette.ColorRole.Mid, QColor(80, 80, 80))
    _set_all(palette, QPalette.ColorRole.Dark, QColor(30, 30, 30))
    _set_all(palette, QPalette.ColorRole.Shadow, QColor(20, 20, 20))

    # Disabled overrides
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_text)

    return palette


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_light() -> None:
    """Switch the application to the light palette."""
    global _is_dark
    QApplication.setPalette(_build_light_palette())
    _is_dark = False
    # Force a full repaint of all widgets
    for widget in QApplication.topLevelWidgets():
        widget.repaint()


def apply_dark() -> None:
    """Switch the application to the dark palette."""
    global _is_dark
    QApplication.setPalette(_build_dark_palette())
    _is_dark = True
    for widget in QApplication.topLevelWidgets():
        widget.repaint()


def is_dark() -> bool:
    """Return True if the dark theme is currently active."""
    return _is_dark
