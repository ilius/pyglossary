from __future__ import annotations

from typing import TYPE_CHECKING

import slint

from .utils import SLINT_STYLES, load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["ThemeDialog"]


class ThemeDialog:
	"""
	Non-modal picker for the built-in Slint widget style (see
	`utils.SLINT_STYLES`). Slint bakes a style into the compiled
	`ComponentDefinition` of each `.slint` file at load time (see
	`utils.load_slint`), so a newly picked style cannot be hot-applied to the
	already-running window -- it is persisted to config.json (by the caller,
	via `onOk`) and takes effect on the next launch (see `utils.setSlintStyle`,
	called once at startup in `UI.__init__`).
	"""

	def __init__(
		self,
		currentStyle: str,
		onOk: Callable[[str], None],
		onClose: Callable[[ThemeDialog], None],
	) -> None:
		self._onOk = onOk
		self._onClose = onClose

		comp = load_slint("dialogs.slint").ThemeDialog
		self.dialog = comp()
		self.dialog.theme_names = slint.ListModel(
			[label for label, _style in SLINT_STYLES],
		)
		styles = [style for _label, style in SLINT_STYLES]
		self.dialog.current_index = (
			styles.index(currentStyle) if currentStyle in styles else 0
		)
		# Bind weakly (see utils.weakCallback) so the Slint component is never
		# part of a reference cycle with this controller.
		self.dialog.ok = weakCallback(self._onOkCb)
		self.dialog.cancel = weakCallback(self._onCancel)
		self.dialog.show()

	def _onOkCb(self) -> None:
		i = self.dialog.current_index
		styles = [style for _label, style in SLINT_STYLES]
		if 0 <= i < len(styles):
			self._onOk(styles[i])
		self._close()

	def _onCancel(self) -> None:
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
