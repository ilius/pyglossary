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

from .utils import (
	decodeGeometry,
	encodeLocation,
	newButton,
	set_window_icon,
)

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["PreConvertInfoDialog"]


class PreConvertInfoDialog(tk.Toplevel):
	def __init__(
		self,
		info: dict[str, Any],
		okFunc: Callable[[dict[str, Any]]],
		master: tk.Widget,
	) -> None:
		tk.Toplevel.__init__(self, master=master)
		self.resizable(width=True, height=True)
		self.title("Set Info / Metedata")
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())

		self.info = info
		self.okFunc = okFunc

		mainFrame = self.frame = ttk.Frame(master=self)

		frame = ttk.Frame(master=mainFrame)
		ttk.Label(
			text="Glossary Name",
			master=frame,
		).pack(side="left", expand=False)
		nameEntry = ttk.Entry(master=frame, width=50)
		nameEntry.pack(side="left", fill="x", expand=True)
		nameEntry.insert(0, info.get("name", ""))
		self.nameEntry = nameEntry
		frame.pack(side="top", expand=True, fill="both")

		frame = ttk.Frame(master=mainFrame)
		ttk.Label(
			text="Source Language",
			master=frame,
		).pack(side="left", expand=False)
		sourceLangEntry = ttk.Entry(master=frame)
		sourceLangEntry.pack(side="right", fill="x", expand=True)
		sourceLangEntry.insert(0, info.get("sourceLang", ""))
		self.sourceLangEntry = sourceLangEntry
		frame.pack(side="top", expand=True, fill="both")

		frame = ttk.Frame(master=mainFrame)
		ttk.Label(
			text="Target Language",
			master=frame,
		).pack(side="left", expand=False)
		targetLangEntry = ttk.Entry(master=frame)
		targetLangEntry.pack(side="right", fill="x", expand=True)
		targetLangEntry.insert(0, info.get("targetLang", ""))
		self.targetLangEntry = targetLangEntry
		frame.pack(side="top", expand=True, fill="both")

		mainFrame.pack(fill="both", expand=True)

		buttonBox = ttk.Frame(self)
		okButton = newButton(
			buttonBox,
			text="  OK  ",
			command=self.okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		okButton.pack(side="right")
		buttonBox.pack(fill="x")

		px, py, pw, ph = decodeGeometry(master.winfo_toplevel().geometry())
		self.geometry(
			encodeLocation(
				px + pw // 2 - 200,
				py + ph // 2 - 100,
			)
		)

	def okClicked(self) -> None:
		name = self.nameEntry.get()
		if name:
			self.info["name"] = name
		sourceLang = self.sourceLangEntry.get()
		if sourceLang:
			self.info["sourceLang"] = sourceLang
		targetLang = self.targetLangEntry.get()
		if targetLang:
			self.info["targetLang"] = targetLang
		self.okFunc(self.info)
		self.destroy()
