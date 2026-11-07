"""Widget-style (theme) picker for the Slint UI; applies on next launch."""

from __future__ import annotations

from typing import TYPE_CHECKING

import slint

from .utils import SLINT_STYLES, load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["ThemeDialog"]

_STYLE_IDS = [style for _label, style in SLINT_STYLES]


class ThemeDialog:
	"""Non-modal; calls `onOk(style)` on OK (see `utils.setSlintStyle`)."""

	def __init__(
		self,
		currentStyle: str,
		onOk: Callable[[str], None],
		onClose: Callable[[ThemeDialog], None],
	) -> None:
		self._onOkCb = onOk
		self._onClose = onClose
		self.dialog = load_slint("dialogs.slint").ThemeDialog()
		self.dialog.theme_names = slint.ListModel([label for label, _ in SLINT_STYLES])
		self.dialog.current_index = (
			_STYLE_IDS.index(currentStyle) if currentStyle in _STYLE_IDS else 0
		)
		self.dialog.ok = weakCallback(self._onOk)
		self.dialog.cancel = weakCallback(self._close)
		self.dialog.show()

	def _onOk(self) -> None:
		i = self.dialog.current_index
		if 0 <= i < len(_STYLE_IDS):
			self._onOkCb(_STYLE_IDS[i])
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
