# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from typing import TYPE_CHECKING, Any

from gi.repository import Gtk as gtk

from pyglossary.ui.config import configDefDict

from .sort_options import SortOptionsBox
from .utils import (
	HBox,
	dialog_add_button,
	pack,
)

if TYPE_CHECKING:
	from gi.repository import Gdk as gdk

__all__ = ["GeneralOptionsButton"]


class GeneralOptionsDialog(gtk.Dialog):
	def onCloseRequest(self, _widget: gtk.Widget) -> bool:
		self.hide()
		return True

	def onResponse(self, _widget: gtk.Widget, _event: gdk.Event) -> bool:
		self.applyChanges()
		self.hide()
		return True

	def __init__(self, mainWin: gtk.Window, **kwargs: Any) -> None:
		gtk.Dialog.__init__(
			self,
			transient_for=mainWin,
			**kwargs,
		)
		self.set_title("General Options")
		self.mainWin = mainWin
		##
		self.vbox = self.get_content_area()
		self.vbox.set_spacing(5)
		##
		self.set_default_size(600, 500)
		self.connect("close-request", self.onCloseRequest)
		##
		self.connect("response", self.onResponse)
		dialog_add_button(
			self,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		##
		hpad = 10
		##
		self.sortOptionsBox = SortOptionsBox(mainWin)
		pack(self.vbox, self.sortOptionsBox)
		##
		hbox = HBox(spacing=hpad)
		self.sqliteCheck = gtk.CheckButton(label="SQLite mode")
		pack(hbox, self.sqliteCheck)
		pack(self.vbox, hbox)
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
		self.configCheckButtons = {}
		for param in self.configParams:
			hbox = HBox(spacing=hpad)
			comment = configDefDict[param].comment
			checkButton = gtk.CheckButton(
				label=comment.split("\n")[0],
			)
			self.configCheckButtons[param] = checkButton
			pack(hbox, checkButton)
			pack(self.vbox, hbox)
		##
		self.updateWidgets()
		self.vbox.show()

	def getSQLite(self) -> bool:
		convertOptions = self.mainWin.convertOptions
		sqlite = convertOptions.get("sqlite")
		if sqlite is not None:
			return sqlite
		return self.mainWin.config.get("auto_sqlite", True)

	def updateWidgets(self) -> None:
		config = self.mainWin.config
		self.sortOptionsBox.updateWidgets()
		self.sqliteCheck.set_active(self.getSQLite())
		for param, check in self.configCheckButtons.items():
			default = self.configParams[param]
			check.set_active(config.get(param, default))

	def applyChanges(self) -> None:
		# print("applyChanges")
		self.sortOptionsBox.applyChanges()

		convertOptions = self.mainWin.convertOptions
		config = self.mainWin.config

		convertOptions["sqlite"] = self.sqliteCheck.get_active()

		for param, check in self.configCheckButtons.items():
			config[param] = check.get_active()


class GeneralOptionsButton(gtk.Button):
	def __init__(self, mainWin: gtk.Window) -> None:
		gtk.Button.__init__(self, label="General Options")
		self.mainWin = mainWin
		self.connect("clicked", self.onClick)
		self.dialog = None

	def onClick(self, _widget: gtk.Widget) -> None:
		if self.dialog is None:
			self.dialog = GeneralOptionsDialog(self.mainWin)
		self.dialog.present()
