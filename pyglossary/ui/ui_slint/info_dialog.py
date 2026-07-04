from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	pass

__all__ = ["InfoDialog"]


class InfoDialog:
	"""
	Non-modal editor for glossary name / sourceLang / targetLang. On OK it
	updates the `info` dict (only non-empty fields) and calls `onOk(info)`.
	"""

	def __init__(
		self,
		info: dict[str, Any],
		onOk: Callable[[dict[str, Any]], None],
		onClose: Callable[["InfoDialog"], None],
	) -> None:
		self.info = info
		self._onOk = onOk
		self._onClose = onClose

		comp = load_slint("dialogs.slint").InfoDialog
		self.dialog = comp()
		self.dialog.name_value = info.get("name", "")
		self.dialog.source_lang = info.get("sourceLang", "")
		self.dialog.target_lang = info.get("targetLang", "")
		# Bind weakly (see utils.weakCallback) so the Slint component is never
		# part of a reference cycle with this controller.
		self.dialog.ok = weakCallback(self._onOkCb)
		self.dialog.cancel = weakCallback(self._onCancel)
		self.dialog.show()

	def _onOkCb(self) -> None:
		name = self.dialog.name_value
		if name:
			self.info["name"] = name
		sourceLang = self.dialog.source_lang
		if sourceLang:
			self.info["sourceLang"] = sourceLang
		targetLang = self.dialog.target_lang
		if targetLang:
			self.info["targetLang"] = targetLang
		self._onOk(self.info)
		self._close()

	def _onCancel(self) -> None:
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
