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

from pyglossary.ui.config import configDefDict

from .sort_options import SortOptionsBox
from .utils import (
	newButton,
	set_window_icon,
)

__all__ = ["GeneralOptionsDialog"]


class UIType(Protocol):
	pass  # TODO


class GeneralOptionsDialog(tk.Toplevel):
	def __init__(
		self,
		ui: UIType,
		master: tk.Widget | None = None,
	) -> None:
		self.ui = ui
		tk.Toplevel.__init__(self, master=master)
		self.resizable(width=True, height=True)
		self.title("General Options")
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())
		####
		padx = 0
		pady = 0
		##
		self.sortOptionsBox = SortOptionsBox(ui, master=self)
		self.sortOptionsBox.pack(side="top", pady=pady, expand=True, fill="both")
		##
		hbox = ttk.Frame(self)
		self.sqliteCheckVar = tk.IntVar()
		self.sqliteCheck = ttk.Checkbutton(
			hbox,
			text="SQLite mode",
			variable=self.sqliteCheckVar,
		)
		self.sqliteCheck.pack(side="left", padx=padx, expand=True, fill="x")
		hbox.pack(side="top", pady=pady, expand=True, fill="both")
		##
		self.configParams = {
			"save_info_json": False,
			"lower": False,
			"skip_resources": False,
			"rtl": False,
			"enable_alts": True,
			"cleanup": True,
			"remove_html_all": True,
		}
		self.configCheckVars: dict[str, tk.IntVar] = {}
		for param in self.configParams:
			# hbox = ttk.Frame(self)
			comment = configDefDict[param].comment
			comment = comment.split("\n")[0]
			checkVar = tk.IntVar()
			checkButton = ttk.Checkbutton(
				self,
				text=comment,
				variable=checkVar,
			)
			self.configCheckVars[param] = checkVar
			checkButton.pack(side="top", padx=padx, expand=True, fill="both")
			# hbox.pack(side="top", pady=pady)

		###
		buttonBox = ttk.Frame(self)
		okButton = newButton(
			buttonBox,
			text="  OK  ",
			command=self.okClicked,
		)
		okButton.pack(side="right")
		buttonBox.pack(fill="x")
		##
		self.updateWidgets()

	def getSQLite(self) -> bool:
		convertOptions = self.ui.convertOptions
		sqlite = convertOptions.get("sqlite")
		if sqlite is not None:
			return sqlite
		return self.ui.config.get("auto_sqlite", True)

	def updateWidgets(self) -> None:
		config = self.ui.config
		self.sortOptionsBox.updateWidgets()
		self.sqliteCheck.configure(state=tk.NORMAL if self.getSQLite() else tk.DISABLED)
		for param, checkVar in self.configCheckVars.items():
			default = self.configParams[param]
			checkVar.set(config.get(param, default))

	def applyChanges(self) -> None:
		# print("applyChanges")
		self.sortOptionsBox.applyChanges()

		convertOptions = self.ui.convertOptions
		config = self.ui.config

		convertOptions["sqlite"] = bool(self.sqliteCheckVar.get())

		for param, checkVar in self.configCheckVars.items():
			config[param] = bool(checkVar.get())

	def okClicked(self) -> None:
		self.applyChanges()
		self.destroy()
