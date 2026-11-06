"""Searchable input/output format picker for the Slint UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import slint

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["FormatPicker"]


class FormatPicker:
	"""Non-modal; calls `onSelect(description)` on OK / double-click."""

	def __init__(
		self,
		descList: list[str],
		activeDesc: str,
		onSelect: Callable[[str], None],
		onClose: Callable[[FormatPicker], None],
	) -> None:
		self._all = [(d, d.lower()) for d in descList]
		self._active = activeDesc
		self._onSelect = onSelect
		self._onClose = onClose

		self.dialog = load_slint("dialogs.slint").FormatPickerDialog()
		self._setShown(descList)
		self.dialog.search_edited = weakCallback(self._onSearch)
		self.dialog.ok = weakCallback(self._onOk)
		self.dialog.cancel = weakCallback(self._close)
		self.dialog.show()

	def _setShown(self, shown: list[str]) -> None:
		self._shown = shown
		self.dialog.shown_formats = slint.ListModel(shown)
		self.dialog.current_index = (
			shown.index(self._active) if self._active in shown else -1
		)

	def _onSearch(self, query: str) -> None:
		query = query.strip().lower()
		prefix: list[str] = []
		contains: list[str] = []
		for desc, lower in self._all:
			if lower.startswith(query):
				prefix.append(desc)
			elif query in lower:
				contains.append(desc)
		self._setShown(prefix + contains)

	def _onOk(self) -> None:
		i = self.dialog.current_index
		if 0 <= i < len(self._shown):
			self._onSelect(self._shown[i])
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
