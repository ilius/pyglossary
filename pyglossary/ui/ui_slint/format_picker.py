from __future__ import annotations

from typing import TYPE_CHECKING

import slint

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["FormatPicker"]


class FormatPicker:
	"""
	Non-modal format selection window. `on_select(desc)` is invoked on OK or
	double-click with the chosen format description (plugin.description), or
	not at all on cancel. The owner must keep a reference to the picker for as
	long as the window should stay open (see `UI._ref_dialog`).
	"""

	def __init__(
		self,
		descList: list[str],
		activeDesc: str,
		onSelect: Callable[[str], None],
		onClose: Callable[[FormatPicker], None],
	) -> None:
		self._all = list(descList)
		self._shown: list[str] = list(descList)
		self._active = activeDesc
		self._onSelect = onSelect
		self._onClose = onClose

		comp = load_slint("dialogs.slint").FormatPickerDialog
		self.dialog = comp()
		self._model = slint.ListModel(list(self._shown))
		self.dialog.shown_formats = self._model
		self._applyActiveIndex()

		# Bind weakly so the Slint component does not strongly retain this
		# controller: that would form a cycle through an unsendable Slint object.
		# See utils.weakCallback.
		self.dialog.search_edited = weakCallback(self._onSearch)
		self.dialog.item_clicked = weakCallback(self._onItemClicked)
		self.dialog.item_double_clicked = weakCallback(self._onItemDoubleClicked)
		self.dialog.ok = weakCallback(self._onOk)
		self.dialog.cancel = weakCallback(self._onCancel)

		self.dialog.show()

	# ----------------------------------------------------------
	def _applyActiveIndex(self) -> None:
		idx = self._shown.index(self._active) if self._active in self._shown else -1
		self.dialog.current_index = idx

	def _rebuildShown(self, query: str) -> None:
		query = query.strip().lower()
		if not query:
			self._shown = list(self._all)
		else:
			prefix = [d for d in self._all if d.lower().startswith(query)]
			contains = [d for d in self._all if query in d.lower() and d not in prefix]
			self._shown = prefix + contains
		# rebuild model in place
		self._model = slint.ListModel(list(self._shown))
		self.dialog.shown_formats = self._model
		self._applyActiveIndex()

	# ----------------------------------------------------------
	# callbacks (run on the Slint event-loop thread)
	# ----------------------------------------------------------
	def _onSearch(self, query: str) -> None:
		self._rebuildShown(query)

	def _onItemClicked(self, i: int) -> None:
		# current-index is already updated by the slint side
		pass

	def _onItemDoubleClicked(self, i: int) -> None:
		if 0 <= i < len(self._shown):
			self._accept(self._shown[i])

	def _onOk(self) -> None:
		i = self.dialog.current_index
		if 0 <= i < len(self._shown):
			self._accept(self._shown[i])
		else:
			self._close()

	def _onCancel(self) -> None:
		self._close()

	# ----------------------------------------------------------
	def _accept(self, desc: str) -> None:
		self._onSelect(desc)
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
