"""Confirmation dialog for the Slint UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["ConfirmDialog"]


class ConfirmDialog:
	"""Modal confirmation (slint `Dialog` + `StandardButton`)."""

	def __init__(
		self,
		message: str,
		onConfirm: Callable[[], None],
		onClose: Callable[[ConfirmDialog], None],
	) -> None:
		self._onConfirm = onConfirm
		self._onClose = onClose
		self.dialog = load_slint("dialogs.slint").ConfirmDialog()
		self.dialog.message = message
		self.dialog.ok_clicked = weakCallback(self._ok)
		self.dialog.cancel_clicked = weakCallback(self._cancel)
		self.dialog.show()

	def _ok(self) -> None:
		self.dialog.hide()
		onConfirm = self._onConfirm
		self._onClose(self)
		onConfirm()

	def _cancel(self) -> None:
		self.dialog.hide()
		self._onClose(self)
