from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["AlertDialog"]


class AlertDialog:
	"""
	Non-modal, single-button informational alert.

	Backed by Slint's built-in `Dialog` element + `StandardButton { kind: ok; }`
	(see `dialogs.slint`), which places the button per the host platform's
	convention rather than a hand-laid-out `Button`.
	"""

	def __init__(
		self,
		message: str,
		onClose: Callable[[AlertDialog], None],
	) -> None:
		self._onClose = onClose

		comp = load_slint("dialogs.slint").AlertDialog
		self.dialog = comp()
		self.dialog.message = message
		# Bind weakly (see utils.weakCallback) so the Slint component is never
		# part of a reference cycle with this controller.
		self.dialog.ok_clicked = weakCallback(self._close)
		self.dialog.show()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
