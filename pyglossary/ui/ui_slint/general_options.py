"""General conversion options dialog (sort, sqlite, config toggles) for the Slint UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import slint

from pyglossary.sort_keys import namedSortKeyList
from pyglossary.ui.config import configDefDict

from .utils import load_slint, weakCallback

if TYPE_CHECKING:
	from collections.abc import Callable

	from .ui import UI

__all__ = ["GeneralOptionsDialog"]

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
_PARAM_NAMES = tuple(_CONFIG_PARAMS)


class GeneralOptionsDialog:
	"""Non-modal; on OK updates `ui.convertOptions` and `ui.config` in place."""

	def __init__(
		self,
		ui: UI,
		onClose: Callable[[GeneralOptionsDialog], None],
	) -> None:
		self.ui = ui
		self._onClose = onClose
		convertOptions = ui.convertOptions
		self._configValues = {
			param: bool(ui.config.get(param, default))
			for param, default in _CONFIG_PARAMS.items()
		}

		sortKeyName, _, sortLocale = (convertOptions.get("sortKeyName") or "").partition(
			":"
		)
		sqlite = convertOptions.get("sqlite")

		d = self.dialog = load_slint("dialogs.slint").GeneralOptionsDialog()
		d.sort_enabled = bool(convertOptions.get("sort", False))
		d.sort_key_descs = slint.ListModel(sortKeyDescList)
		d.current_sort_key = sortKeyDescByName.get(sortKeyName, sortKeyDescList[0])
		d.sort_encoding_enabled = "sortEncoding" in convertOptions
		d.sort_encoding = convertOptions.get("sortEncoding") or "utf-8"
		d.sort_locale = sortLocale
		d.sqlite_enabled = (
			bool(ui.config.get("auto_sqlite", True)) if sqlite is None else bool(sqlite)
		)
		d.config_checks = slint.ListModel(
			[
				{
					"comment": (configDefDict[param].comment or "").split("\n")[0],
					"value": value,
				}
				for param, value in self._configValues.items()
			],
		)
		d.set_config = weakCallback(self._setConfig)
		d.ok = weakCallback(self._onOk)
		d.cancel = weakCallback(self._close)
		d.show()

	def _setConfig(self, i: int, value: bool) -> None:
		self._configValues[_PARAM_NAMES[i]] = value

	def _onOk(self) -> None:
		d = self.dialog
		convertOptions = self.ui.convertOptions
		if d.sort_enabled:
			sortKeyName = sortKeyNameByDesc.get(d.current_sort_key, "")
			sortLocale = d.sort_locale.strip()
			if sortLocale:
				sortKeyName = f"{sortKeyName}:{sortLocale}"
			convertOptions["sort"] = True
			convertOptions["sortKeyName"] = sortKeyName
			if d.sort_encoding_enabled:
				convertOptions["sortEncoding"] = d.sort_encoding or "utf-8"
			else:
				convertOptions.pop("sortEncoding", None)
		else:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				convertOptions.pop(param, None)
		convertOptions["sqlite"] = d.sqlite_enabled
		self.ui.config.update(self._configValues)
		self._close()

	def _close(self) -> None:
		self.dialog.hide()
		self._onClose(self)
