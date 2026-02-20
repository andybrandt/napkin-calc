"""Reusable UI widgets for the Napkin Calculator.

The main building block is ``ReactiveNumberField`` – a QLineEdit that:
- Validates numeric input (integers, decimals, scientific notation).
- Emits a ``value_changed`` signal only on *user* edits.
- Provides ``set_display_value`` for programmatic updates that do NOT
  trigger the signal (preventing infinite update loops).
"""

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QLineEdit, QToolButton


class DecimalValidator(QValidator):
    """Accept integers, decimals, and simple scientific notation (e.g. 1e6)."""

    def validate(self, text: str, pos: int) -> tuple:  # type: ignore[override]
        stripped = text.strip()
        if stripped == "" or stripped == "-":
            return (QValidator.State.Intermediate, text, pos)
        try:
            Decimal(stripped)
            return (QValidator.State.Acceptable, text, pos)
        except InvalidOperation:
            # Allow partial input like "1e" or "1." while typing
            if stripped.endswith(("e", "E", ".", "e+", "e-", "E+", "E-")):
                return (QValidator.State.Intermediate, text, pos)
            return (QValidator.State.Invalid, text, pos)


class ReactiveNumberField(QLineEdit):
    """Numeric input field with a guard against programmatic signal loops.

    Parameters
    ----------
    parent :
        Optional parent widget.
    placeholder :
        Greyed-out hint text shown when the field is empty.

    Signals
    -------
    value_changed(Decimal) :
        Fired when the *user* changes the value (not on programmatic
        ``set_display_value`` calls).
    """

    value_changed = Signal(object)  # Decimal passed as object for Signal compat

    def __init__(self, parent=None, placeholder: str = "0") -> None:
        super().__init__(parent)
        self._updating_programmatically = False

        self.setValidator(DecimalValidator(self))
        self.setPlaceholderText(placeholder)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setMinimumWidth(120)
        self.setMaximumWidth(180)

        self.editingFinished.connect(self._on_editing_finished)

    # -- programmatic (silent) update --------------------------------------

    def set_display_value(self, text: str) -> None:
        """Replace the displayed text *without* emitting ``value_changed``."""
        self._updating_programmatically = True
        self.setText(text)
        self._updating_programmatically = False

    # -- internal ----------------------------------------------------------

    def _on_editing_finished(self) -> None:
        """Handle Return / focus-out from user editing."""
        if self._updating_programmatically:
            return
        text = self.text().strip().replace(",", "")
        if not text:
            return
        try:
            value = Decimal(text)
        except InvalidOperation:
            return
        self.value_changed.emit(value)


_LOCKED_TEXT = "\U0001f512"   # closed padlock
_UNLOCKED_TEXT = "\U0001f513"  # open padlock


class LockButton(QToolButton):
    """Toggle button that shows a padlock glyph.

    Emits ``toggled(bool)`` -- True means this variable should be locked.
    Uses emoji padlock characters that render with their own color on
    all platforms and are visible on any background.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setToolTip("Click to hold this value constant")
        self._refresh_text()
        self.toggled.connect(self._refresh_text)

    def _refresh_text(self, *_args) -> None:
        if self.isChecked():
            self.setText(_LOCKED_TEXT)
            self.setToolTip("This value is held constant")
        else:
            self.setText(_UNLOCKED_TEXT)
            self.setToolTip("Click to hold this value constant")
