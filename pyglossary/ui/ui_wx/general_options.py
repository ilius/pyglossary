# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from typing import TYPE_CHECKING

import wx

from pyglossary.ui.config import configDefDict

from .sort_helpers import (
	SORT_KEY_DESC_BY_NAME,
	SORT_KEY_DESC_LIST,
	SORT_KEY_NAME_BY_DESC,
)

if TYPE_CHECKING:
	from .ui import UI

__all__ = ["GeneralOptionsWxDialog"]


class GeneralOptionsWxDialog(wx.Dialog):
	def __init__(self, ui: UI, parent: wx.Window | None) -> None:
		super().__init__(parent, title="General Options", size=(480, 420))
		self._ui = ui
		panel = wx.Panel(self)
		lay = wx.BoxSizer(wx.VERTICAL)

		sort_row = wx.BoxSizer(wx.HORIZONTAL)
		self._sort_check = wx.CheckBox(panel, label="Sort entries by")
		self._sort_combo = wx.Choice(panel, choices=SORT_KEY_DESC_LIST)
		sort_row.Add(self._sort_check, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
		sort_row.Add(self._sort_combo, 1, wx.EXPAND)
		lay.Add(sort_row, 0, wx.ALL | wx.EXPAND, 4)
		self._sort_check.Bind(wx.EVT_CHECKBOX, self._on_sort_toggle)

		enc_row = wx.BoxSizer(wx.HORIZONTAL)
		self._enc_check = wx.CheckBox(panel, label="Sort Encoding")
		self._enc_edit = wx.TextCtrl(panel, value="utf-8", size=(120, -1))
		enc_row.Add(self._enc_check, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
		enc_row.Add(self._enc_edit, 0, wx.EXPAND)
		lay.Add(enc_row, 0, wx.ALL | wx.EXPAND, 4)

		locale_row = wx.BoxSizer(wx.HORIZONTAL)
		locale_row.Add(
			wx.StaticText(panel, label="Sort Locale"),
			0,
			wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
			6,
		)
		self._locale_e = wx.TextCtrl(panel)
		locale_row.Add(self._locale_e, 1, wx.EXPAND)
		lay.Add(locale_row, 0, wx.ALL | wx.EXPAND, 4)

		self._sqlite_chk = wx.CheckBox(panel, label="SQLite mode")
		lay.Add(self._sqlite_chk, 0, wx.ALL, 4)

		self._cfg_checks: dict[str, wx.CheckBox] = {}
		self.config_params_defaults = {
			"save_info_json": False,
			"lower": False,
			"skip_resources": False,
			"rtl": False,
			"enable_alts": True,
			"cleanup": True,
			"remove_html_all": True,
		}
		for param in self.config_params_defaults:
			txt = configDefDict[param].comment.split("\n")[0]
			cb = wx.CheckBox(panel, label=txt)
			self._cfg_checks[param] = cb
			lay.Add(cb, 0, wx.ALL, 4)

		btns = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(panel, wx.ID_OK)
		cancel_btn = wx.Button(panel, wx.ID_CANCEL)
		btns.AddButton(ok_btn)
		btns.AddButton(cancel_btn)
		btns.Realize()
		lay.Add(btns, 0, wx.ALL | wx.EXPAND, 8)
		panel.SetSizer(lay)
		self.Bind(wx.EVT_BUTTON, self._on_ok, ok_btn)
		self._load_from_ui()

	def _get_sqlite_allowed(self) -> bool:
		co = self._ui.convertOptions
		sqlite = co.get("sqlite")
		if sqlite is not None:
			return bool(sqlite)
		return bool(self._ui.config.get("auto_sqlite", True))

	def _on_sort_toggle(self, _evt: wx.CommandEvent) -> None:
		self._update_sort_controls(self._sort_check.GetValue())

	def _update_sort_controls(self, on: bool) -> None:
		self._sort_combo.Enable(on)

	def _load_from_ui(self) -> None:
		co = self._ui.convertOptions
		sort = bool(co.get("sort", False))
		self._sort_check.SetValue(sort)
		self._sort_combo.Enable(sort)
		sort_key_name = co.get("sortKeyName", "")
		locale_txt = ""
		if sort_key_name and isinstance(sort_key_name, str):
			name_part, sep, locale_part = sort_key_name.partition(":")
			if sep:
				sort_key_name = name_part
				locale_txt = locale_part
		if sort_key_name and sort_key_name in SORT_KEY_DESC_BY_NAME:
			desc = SORT_KEY_DESC_BY_NAME[sort_key_name]
			idx = self._sort_combo.FindString(desc)
			if idx != wx.NOT_FOUND:
				self._sort_combo.SetSelection(idx)
		self._locale_e.SetValue(locale_txt)
		self._sqlite_chk.Enable(self._get_sqlite_allowed())
		if "sortEncoding" in co:
			self._enc_check.SetValue(True)
			self._enc_edit.SetValue(co["sortEncoding"])
		else:
			self._enc_check.SetValue(False)
			self._enc_edit.SetValue("utf-8")
		cfg = self._ui.config
		for param, cb in self._cfg_checks.items():
			cb.SetValue(bool(cfg.get(param, self.config_params_defaults[param])))

	def _on_ok(self, _evt: wx.CommandEvent) -> None:
		co = self._ui.convertOptions
		cfg = self._ui.config
		co["sqlite"] = bool(self._sqlite_chk.GetValue())
		if self._sort_check.GetValue():
			desc = self._sort_combo.GetStringSelection()
			name = SORT_KEY_NAME_BY_DESC[desc]
			loc = self._locale_e.GetValue().strip()
			if loc:
				name = f"{name}:{loc}"
			co["sort"] = True
			co["sortKeyName"] = name
			if self._enc_check.GetValue():
				co["sortEncoding"] = self._enc_edit.GetValue().strip()
			elif "sortEncoding" in co:
				del co["sortEncoding"]
		else:
			for k in ("sort", "sortKeyName", "sortEncoding"):
				if k in co:
					del co[k]
		for param, cb in self._cfg_checks.items():
			cfg[param] = cb.GetValue()
		self.EndModal(wx.ID_OK)
