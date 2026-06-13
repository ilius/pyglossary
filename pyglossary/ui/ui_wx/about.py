# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from html import escape
from os.path import isabs, join

import wx.html

from pyglossary.core import appResDir, homePage
from pyglossary.ui.base import aboutText, authors, licenseText, logo
from pyglossary.ui.version import getAboutHeader

from .wx_imports import wx

__all__ = ["exec_about_dialog"]


def _res_path(path: str) -> str:
	if not isabs(path):
		return join(appResDir, path)
	return path


def _new_readonly_text(parent: wx.Window, text: str) -> wx.TextCtrl:
	edit = wx.TextCtrl(
		parent,
		value=text,
		style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
	)
	font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
	edit.SetFont(font)
	return edit


def _new_about_browser(parent: wx.Window, text: str) -> wx.Panel:
	panel = wx.Panel(parent)
	sizer = wx.BoxSizer(wx.VERTICAL)
	html = escape(text).replace("\n", "<br>\n")
	html += f'<br><a href="{escape(homePage, quote=True)}">{escape(homePage)}</a>'
	browser = wx.html.HtmlWindow(panel)
	browser.SetPage(f"<body>{html}</body>")
	sizer.Add(browser, 1, wx.EXPAND)
	panel.SetSizer(sizer)
	return panel


class AboutWxDialog(wx.Dialog):
	def __init__(self, parent: wx.Window | None = None) -> None:
		super().__init__(parent, title="About PyGlossary", size=(600, 550))
		panel = wx.Panel(self)
		layout = wx.BoxSizer(wx.VERTICAL)

		header = wx.BoxSizer(wx.HORIZONTAL)
		logo_bmp = wx.Bitmap(_res_path(logo), wx.BITMAP_TYPE_ANY)
		header.Add(wx.StaticBitmap(panel, bitmap=logo_bmp), 0, wx.RIGHT, 20)
		header_label = wx.StaticText(
			panel,
			label=getAboutHeader("wxPython", wx.version()),
		)
		header.Add(header_label, 1, wx.ALIGN_CENTER_VERTICAL)
		layout.Add(header, 0, wx.ALL | wx.EXPAND, 15)

		tabs = wx.Notebook(panel)
		tabs.AddPage(_new_about_browser(tabs, aboutText), "About")
		tabs.AddPage(_new_readonly_text(tabs, "\n".join(authors)), "Authors")
		tabs.AddPage(_new_readonly_text(tabs, licenseText), "License")
		layout.Add(tabs, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

		btns = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(panel, wx.ID_OK)
		btns.AddButton(ok_btn)
		btns.Realize()
		layout.Add(btns, 0, wx.ALL | wx.ALIGN_RIGHT, 15)
		panel.SetSizer(layout)


def exec_about_dialog(parent: wx.Window | None) -> None:
	dlg = AboutWxDialog(parent)
	dlg.ShowModal()
	dlg.Destroy()
