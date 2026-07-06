from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.sort_keys import namedSortKeyList
from pyglossary.ui.config import configDefDict

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

	from .ui import UI

__all__ = ["GeneralOptionsDialog"]

log = logging.getLogger("pyglossary")

sortKeyDescList = [sk.desc for sk in namedSortKeyList]
sortKeyNameByDesc = {sk.desc: sk.name for sk in namedSortKeyList}
sortKeyDescByName = {sk.name: sk.desc for sk in namedSortKeyList}

# Same set as ui_tk/general_options.py GeneralOptionsDialog.configParams
_CONFIG_PARAMS: dict[str, bool] = {
	"save_info_json": False,
	"lower": False,
	"skip_resources": False,
	"rtl": False,
	"enable_alts": True,
	"cleanup": True,
	"remove_html_all": True,
}


class GeneralOptionsDialog:
	"""
	Non-modal general-options editor. On OK it mutates `ui.convertOptions`
	(sort / sortKeyName / sortEncoding / sqlite) and `ui.config` (the bool
	toggles) in place, then calls `onOk()`. The owner must keep a reference.
	"""

	def __init__(
		self,
		ui: UI,
		onOk: Callable[[], None],
		onClose: Callable[[GeneralOptionsDialog], None],
	) -> None:
		self.ui = ui
		self._onOk = onOk
		self._onClose = onClose
		self._configParams = list(_CONFIG_PARAMS.keys())
		self._configValues: dict[str, bool] = {}

		convertOptions = ui.convertOptions
		config = ui.config

		# sort box state
		sortEnabled = bool(convertOptions.get("sort", False))
		sortKeyName = convertOptions.get("sortKeyName") or ""
		sortLocale = ""
		if sortKeyName:
			base, _, locale = sortKeyName.partition(":")
			sortKeyName = base
			sortLocale = locale
		currentSortKeyDesc = sortKeyDescByName.get(sortKeyName, sortKeyDescList[0])
		sortEncodingEnabled = "sortEncoding" in convertOptions
		sortEncoding = convertOptions.get("sortEncoding", "utf-8") or "utf-8"

		# config checks
		checkRows: list[dict[str, Any]] = []
		for param in self._configParams:
			default = _CONFIG_PARAMS[param]
			value = bool(config.get(param, default))
			self._configValues[param] = value
			comment = (configDefDict[param].comment or "").split("\n")[0]
			checkRows.append({"comment": comment, "value": value})

		comp = load_slint("dialogs.slint").GeneralOptionsDialog
		self.dialog = comp()
		self.dialog.sort_enabled = sortEnabled
		self.dialog.sort_key_descs = slint.ListModel(list(sortKeyDescList))
		self.dialog.current_sort_key = currentSortKeyDesc
		self.dialog.sort_encoding_enabled = sortEncodingEnabled
		self.dialog.sort_encoding = sortEncoding
		self.dialog.sort_locale = sortLocale
		self.dialog.sqlite_enabled = self._getSQLite()
		self.dialog.config_checks = slint.ListModel(checkRows)

		# Bind weakly (see utils.weakCallback) so the Slint component is never
		# part of a reference cycle with this controller.
		self.dialog.set_config = weakCallback(self._setConfig)
		self.dialog.ok = weakCallback(self._onOkCb)
		self.dialog.cancel = weakCallback(self._onCancel)

		self.dialog.show()

	def _getSQLite(self) -> bool:
		convertOptions = self.ui.convertOptions
		sqlite = convertOptions.get("sqlite")
		if sqlite is not None:
			return bool(sqlite)
		return bool(self.ui.config.get("auto_sqlite", True))

	# ----------------------------------------------------------
	# callbacks (Slint event-loop thread)
	# ----------------------------------------------------------
	def _setConfig(self, i: int, v: bool) -> None:
		self._configValues[self._configParams[i]] = bool(v)

	def _onOkCb(self) -> None:
		convertOptions = self.ui.convertOptions
		config = self.ui.config

		sort = self.dialog.sort_enabled
		if not sort:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				convertOptions.pop(param, None)
		else:
			sortKeyDesc = self.dialog.current_sort_key
			sortKeyName = sortKeyNameByDesc.get(sortKeyDesc, "")
			sortLocale = (self.dialog.sort_locale or "").strip()
			if sortLocale:
				sortKeyName = f"{sortKeyName}:{sortLocale}"
			convertOptions["sort"] = True
			convertOptions["sortKeyName"] = sortKeyName
			if self.dialog.sort_encoding_enabled:
				convertOptions["sortEncoding"] = self.dialog.sort_encoding or "utf-8"
			else:
				convertOptions.pop("sortEncoding", None)

		convertOptions["sqlite"] = bool(self.dialog.sqlite_enabled)

		for param, value in self._configValues.items():
			config[param] = bool(value)

		self._onOk()
		self._close()

	def _onCancel(self) -> None:
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
