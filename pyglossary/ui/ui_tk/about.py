# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from pyglossary.core import homePage
from pyglossary.ui.base import (
	aboutText,
	authors,
	licenseText,
	logo,
)
from pyglossary.ui.version import getVersion

from .utils import (
	newLabelWithImage,
	newReadOnlyText,
)

if TYPE_CHECKING:
	from tkinter.font import Font

__all__ = ["createAboutFrame"]


class VerticalNotebook(ttk.Frame):
	def __init__(
		self,
		parent: tk.Widget,
		font: Font,
		**kwargs: Any,
	) -> None:
		ttk.Frame.__init__(self, parent, **kwargs)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(2, weight=1)
		# scrollable tabs
		self._listbox = tk.Listbox(
			self,
			width=1,
			highlightthickness=0,
			relief="raised",
			justify="center",
			font=font,
		)
		self._listbox.configure()

		# list of widgets associated with the tabs
		self._tabs = []
		self._current_tab = None  # currently displayed tab

		self._listbox.grid(row=0, column=1, sticky="ns")
		# binding to display the selected tab
		self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
		self._maxWidth = 0

	# add tab
	def add(self, widget: tk.Widget, text: str) -> None:
		self._listbox.insert("end", text)
		# resize listbox to be large enough to show all tab labels
		self._maxWidth = max(self._maxWidth, len(text))
		self._listbox.configure(
			width=self._maxWidth + 2,
		)
		index = len(self._tabs)
		self._tabs.append(widget)
		if self._current_tab is None:
			self.switch_tab(index)

	def switch_tab(self, index: int) -> None:
		self._show_tab_index(index)
		self._listbox.selection_clear(0, "end")
		self._listbox.selection_set(index)
		self._listbox.see(index)

	def _show_tab_index(self, index: int) -> None:
		widget = self._tabs[index]
		if self._current_tab is not None:
			self._current_tab.grid_remove()
		self._current_tab = widget
		widget.grid(in_=self, column=2, row=0, sticky="ewns")

	def _on_listbox_select(self, _event: tk.Event | None = None) -> None:
		selection = self._listbox.curselection()
		if not selection:
			return
		index = selection[0]
		if index >= len(self._tabs):
			print(f"{index=}")
			return
		self._show_tab_index(index)


def createAboutFrame(parent: ttk.Widget, bigFont: Font) -> ttk.Frame:
	aboutFrame = ttk.Frame(parent)

	versionFrame = ttk.Frame(aboutFrame, borderwidth=5)
	newLabelWithImage(versionFrame, file=logo).pack(
		side="left",
		fill="both",
		expand=False,
	)
	ttk.Label(versionFrame, text=f"PyGlossary\nVersion {getVersion()}").pack(
		side="left",
		fill="both",
		expand=False,
	)
	versionFrame.pack(side="top", fill="x")
	##

	aboutNotebook = VerticalNotebook(aboutFrame, font=bigFont)

	aboutAboutFrame = ttk.Frame()
	newReadOnlyText(
		aboutAboutFrame,
		text=f"{aboutText}\nHome page: {homePage}",
		font=("DejaVu Sans", 11, ""),
	).pack(fill="both", expand=True)
	aboutAboutFrame.pack(side="top", fill="x")
	aboutNotebook.add(aboutAboutFrame, "About")

	authorsFrame = ttk.Frame()
	authorsText = "\n".join(authors).replace("\t", "    ")
	newReadOnlyText(
		authorsFrame,
		text=authorsText,
		font=("DejaVu Sans", 11, ""),
	).pack(fill="both", expand=True)
	aboutNotebook.add(authorsFrame, "Authors")

	licenseFrame = ttk.Frame()
	newReadOnlyText(
		licenseFrame,
		text=licenseText,
		font=("DejaVu Sans", 11, ""),
	).pack(fill="both", expand=True)
	aboutNotebook.add(licenseFrame, "License")

	aboutNotebook.pack(fill="both", expand=True)
	# aboutNotebook.show_tab_index(0)

	return aboutFrame
