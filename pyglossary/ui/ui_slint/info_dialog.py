"""Glossary metadata (name / languages) dialog for the Slint UI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["InfoDialog"]

# (info key, dialog property)
_FIELDS = (
	("name", "name_value"),
	("sourceLang", "source_lang"),
	("targetLang", "target_lang"),
)


class InfoDialog:
	"""Non-modal; on OK stores the non-empty fields into `info` in place."""

	def __init__(
		self,
		info: dict[str, Any],
		onClose: Callable[[InfoDialog], None],
	) -> None:
		self.info = info
		self._onClose = onClose
		self.dialog = load_slint("dialogs.slint").InfoDialog()
		for key, prop in _FIELDS:
			setattr(self.dialog, prop, info.get(key, ""))
		self.dialog.ok = weakCallback(self._onOk)
		self.dialog.cancel = weakCallback(self._close)
		self.dialog.show()

	def _onOk(self) -> None:
		for key, prop in _FIELDS:
			value = getattr(self.dialog, prop)
			if value:
				self.info[key] = value
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
