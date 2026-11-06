"""Single-button informational alert for the Slint UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["AlertDialog"]


class AlertDialog:
	"""Non-modal message box (slint `Dialog` + `StandardButton`)."""

	def __init__(
		self,
		message: str,
		onClose: Callable[[AlertDialog], None],
	) -> None:
		self._onClose = onClose
		self.dialog = load_slint("dialogs.slint").AlertDialog()
		self.dialog.message = message
		self.dialog.ok_clicked = weakCallback(self._close)
		self.dialog.show()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
