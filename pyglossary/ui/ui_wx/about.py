# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)

from __future__ import annotations

from html import escape
from os.path import isabs, join

import wx
import wx.html

from pyglossary.core import appResDir, homePage
from pyglossary.ui.base import aboutText, authors, licenseText, logo
from pyglossary.ui.version import getAboutHeader

# Prefix of contributor lines in dataDir AUTHORS (BLACK CIRCLE + VS15).
_AUTHORS_BULLET = "⚫︎"

__all__ = ["exec_about_dialog"]


def _wx_colour_hex(colour: wx.Colour) -> str:
	return f"#{colour.Red():02x}{colour.Green():02x}{colour.Blue():02x}"


def _sys_window_colours() -> tuple[wx.Colour, wx.Colour, wx.Colour]:
	"""Background, foreground, and link colours from the active theme."""
	bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
	fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
	hot = getattr(wx, "SYS_COLOUR_HOTLIGHT", None)
	if hot is not None:
		link = wx.SystemSettings.GetColour(hot)
	else:
		link = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
	if not link.IsOk() or link == bg:
		link = wx.Colour(10, 130, 255)
	return bg, fg, link


def _res_path(path: str) -> str:
	if not isabs(path):
		return join(appResDir, path)
	return path


def _authors_line_is_bullet(line: str) -> bool:
	return line.lstrip().startswith(_AUTHORS_BULLET)


def _authors_bullet_body(line: str) -> str:
	t = line.lstrip()
	if t.startswith(_AUTHORS_BULLET):
		return t[len(_AUTHORS_BULLET) :].lstrip()
	return t.lstrip()


def _authors_tab_inner_html(lines: list[str]) -> str:
	"""Build AUTHORS tab markup: <ul> for bullet blocks, <p> for other paragraphs."""
	chunks: list[str] = [f"<p><b>{escape('Authors:')}</b></p>\n"]
	ul_items: list[str] = []
	current_li: list[str] = []

	def flush_li() -> None:
		if not current_li:
			return
		inner = "<br>\n".join(escape(part) for part in current_li)
		ul_items.append(f"<li>{inner}</li>")
		current_li.clear()

	def close_ul() -> None:
		if not ul_items:
			return
		chunks.append("<ul>\n" + "\n".join(ul_items) + "\n</ul>\n")
		ul_items.clear()

	for raw in lines:
		line = raw.rstrip()
		if not line.strip():
			flush_li()
			continue
		if _authors_line_is_bullet(line):
			flush_li()
			current_li.append(_authors_bullet_body(line))
			continue
		if current_li and line.startswith("\t") and not _authors_line_is_bullet(line):
			current_li.append(line.strip())
			continue
		flush_li()
		close_ul()
		para = line.strip()
		if para == "Thanks to:":
			chunks.append(f"<p><b>{escape(para)}</b></p>\n")
		else:
			chunks.append(f"<p>{escape(para)}</p>\n")

	flush_li()
	close_ul()
	return "".join(chunks)


def _new_html_panel(
	parent: wx.Window,
	text: str | None = None,
	*,
	inner_html: str | None = None,
	append_home_link: bool = False,
) -> wx.Panel:
	"""
	Plain-text or pre-escaped HTML body in wx.html.HtmlWindow
	(same widget as About tab).
	"""
	if (text is None) == (inner_html is None):
		raise TypeError("pass exactly one of text or inner_html")
	panel = wx.Panel(parent)
	bg, fg, link = _sys_window_colours()
	panel.SetBackgroundColour(bg)
	sizer = wx.BoxSizer(wx.VERTICAL)
	if inner_html is not None:
		html = inner_html
	else:
		html = escape(text or "").replace("\n", "<br>\n")
	if append_home_link:
		html += f'<br><a href="{escape(homePage, quote=True)}">{escape(homePage)}</a>'
	bg_h, fg_h, link_h = (_wx_colour_hex(bg), _wx_colour_hex(fg), _wx_colour_hex(link))
	# wx.html.HtmlWindow defaults to a light page; match SYS_COLOUR_WINDOW / text / links.
	page = (
		f'<html><body bgcolor="{bg_h}" text="{fg_h}" link="{link_h}" '
		f'vlink="{link_h}" alink="{link_h}">{html}</body></html>'
	)
	browser = wx.html.HtmlWindow(panel)
	browser.SetBackgroundColour(bg)
	browser.SetPage(page)
	sizer.Add(browser, 1, wx.EXPAND)
	panel.SetSizer(sizer)
	return panel


class AboutWxDialog(wx.Dialog):
	def __init__(self, parent: wx.Window | None = None) -> None:
		super().__init__(parent, title="About PyGlossary", size=(600, 550))
		bg, _, _ = _sys_window_colours()
		self.SetBackgroundColour(bg)
		panel = wx.Panel(self)
		panel.SetBackgroundColour(bg)
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
		tabs.SetBackgroundColour(bg)
		tabs.AddPage(_new_html_panel(tabs, aboutText, append_home_link=True), "About")
		tabs.AddPage(
			_new_html_panel(tabs, inner_html=_authors_tab_inner_html(authors)), "Authors"
		)
		tabs.AddPage(_new_html_panel(tabs, licenseText), "License")
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
