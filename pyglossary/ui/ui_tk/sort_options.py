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
from typing import Protocol

from pyglossary.sort_keys import namedSortKeyList

__all__ = ["SortOptionsBox"]

sortKeyNames = [sk.name for sk in namedSortKeyList]
sortKeyNameByDesc = {sk.desc: sk.name for sk in namedSortKeyList}
sortKeyDescByName = {sk.name: sk.desc for sk in namedSortKeyList}


class UIType(Protocol):
	pass  # TODO


class SortOptionsBox(ttk.Frame):
	def __init__(
		self,
		ui: UIType,
		master: tk.Widget | None = None,
	) -> None:
		self.ui = ui
		ttk.Frame.__init__(self, master=master)
		hbox = ttk.Frame(master=self)
		sortCheckVar = tk.IntVar()
		sortCheck = ttk.Checkbutton(
			master=hbox,
			text="Sort entries by",
			variable=sortCheckVar,
			command=self.onSortCheckClicked,
		)
		sortKeyVar = tk.StringVar()
		sortKeyDescList = [sk.desc for sk in namedSortKeyList]
		sortKeyCombo = ttk.OptionMenu(
			hbox,
			sortKeyVar,
			sortKeyDescList[0],
			*sortKeyDescList,
		)
		self.sortCheckVar = sortCheckVar
		self.sortKeyVar = sortKeyVar
		self.sortKeyCombo = sortKeyCombo
		sortCheck.pack(side="left")
		sortKeyCombo.pack(side="left")
		hbox.pack(side="top", expand=True, fill="both")
		###
		hbox = self.encodingHBox = ttk.Frame(master=self)
		encodingCheckVar = self.encodingCheckVar = tk.IntVar()
		encodingCheck = ttk.Checkbutton(
			master=hbox,
			text="Sort Encoding",
			variable=encodingCheckVar,
		)
		encodingEntry = self.encodingEntry = ttk.Entry(hbox, width=15)
		encodingEntry.delete(0, "end")
		encodingEntry.insert(0, "utf-8")
		ttk.Label(hbox, text="    ").pack(side="left")
		encodingCheck.pack(side="left")
		encodingEntry.pack(side="left")
		hbox.pack(side="top", expand=True, fill="both")
		###
		hbox = self.localeHBox = ttk.Frame(master=self)
		localeEntry = self.localeEntry = ttk.Entry(hbox, width=15)
		ttk.Label(master=hbox, text="    ").pack(side="left")
		ttk.Label(master=hbox, text="Sort Locale").pack(side="left")
		localeEntry.pack(side="left", expand=True, fill="x")
		hbox.pack(side="top", expand=True, fill="both")
		###

	def updateSortStates(self, sort: bool) -> None:
		state = tk.NORMAL if sort else tk.DISABLED
		self.sortKeyCombo.configure(state=state)
		# self.encodingHBox.configure(state=state) # unknown option "-state"
		# self.localeHBox.configure(state=state) # unknown option "-state"

	def onSortCheckClicked(self) -> None:
		sort = bool(self.sortCheckVar.get())
		self.updateSortStates(sort)

	def updateWidgets(self) -> None:
		convertOptions = self.ui.convertOptions
		sort = bool(convertOptions.get("sort", False))
		self.sortCheckVar.set(int(sort))
		self.updateSortStates(sort)

		sortKeyName = convertOptions.get("sortKeyName")
		if sortKeyName:
			sortKeyName, _, localeName = sortKeyName.partition(":")
			if sortKeyName:
				self.sortKeyVar.set(sortKeyDescByName[sortKeyName])
			self.localeEntry.delete(0, "end")
			self.localeEntry.insert(0, localeName)

		if "sortEncoding" in convertOptions:
			self.encodingCheckVar.set(1)
			self.encodingEntry.delete(0, "end")
			self.encodingEntry.insert(0, convertOptions["sortEncoding"])

	def applyChanges(self) -> None:
		convertOptions = self.ui.convertOptions
		sort = int(self.sortCheckVar.get())
		if not sort:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				if param in convertOptions:
					del convertOptions[param]
			return

		sortKeyDesc = self.sortKeyVar.get()
		sortKeyName = sortKeyNameByDesc[sortKeyDesc]
		sortLocale = self.localeEntry.get()
		if sortLocale:
			sortKeyName = f"{sortKeyName}:{sortLocale}"

		convertOptions["sort"] = True
		convertOptions["sortKeyName"] = sortKeyName
		if self.encodingCheckVar.get():
			convertOptions["sortEncoding"] = self.encodingEntry.get()
