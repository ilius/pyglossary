# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from typing import Any

from .wx_imports import wx

__all__ = ["PreConvertInfoWxDialog"]


class PreConvertInfoWxDialog(wx.Dialog):
	def __init__(
		self,
		info: dict[str, Any],
		parent: wx.Window | None,
	) -> None:
		super().__init__(parent, title="Set Info / Metadata", size=(420, 200))
		self._info = info
		panel = wx.Panel(self)
		grid = wx.FlexGridSizer(cols=2, hgap=8, vgap=8)
		grid.AddGrowableCol(1, 1)
		grid.Add(wx.StaticText(panel, label="Glossary Name"), 0, wx.ALIGN_CENTER_VERTICAL)
		self._name_e = wx.TextCtrl(panel, value=info.get("name", ""))
		grid.Add(self._name_e, 1, wx.EXPAND)
		grid.Add(
			wx.StaticText(panel, label="Source Language"), 0, wx.ALIGN_CENTER_VERTICAL
		)
		self._src_e = wx.TextCtrl(panel, value=info.get("sourceLang", ""))
		grid.Add(self._src_e, 1, wx.EXPAND)
		grid.Add(
			wx.StaticText(panel, label="Target Language"), 0, wx.ALIGN_CENTER_VERTICAL
		)
		self._tgt_e = wx.TextCtrl(panel, value=info.get("targetLang", ""))
		grid.Add(self._tgt_e, 1, wx.EXPAND)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 10)
		btns = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(panel, wx.ID_OK)
		cancel_btn = wx.Button(panel, wx.ID_CANCEL)
		btns.AddButton(ok_btn)
		btns.AddButton(cancel_btn)
		btns.Realize()
		sizer.Add(btns, 0, wx.ALL | wx.EXPAND, 10)
		panel.SetSizer(sizer)
		self.Bind(wx.EVT_BUTTON, self._on_ok, ok_btn)

	def _on_ok(self, _evt: wx.CommandEvent) -> None:
		if self._name_e.GetValue().strip():
			self._info["name"] = self._name_e.GetValue().strip()
		if self._src_e.GetValue().strip():
			self._info["sourceLang"] = self._src_e.GetValue().strip()
		if self._tgt_e.GetValue().strip():
			self._info["targetLang"] = self._tgt_e.GetValue().strip()
		self.EndModal(wx.ID_OK)
