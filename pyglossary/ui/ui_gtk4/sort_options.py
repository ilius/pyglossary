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

from gi.repository import Gtk as gtk

from pyglossary.sort_keys import defaultSortKeyName, namedSortKeyList

from .utils import HBox, pack

__all__ = ["SortOptionsBox"]


# log = logging.getLogger("pyglossary")


sortKeyNameByDesc = {_sk.desc: _sk.name for _sk in namedSortKeyList}
sortKeyNames = [_sk.name for _sk in namedSortKeyList]


# Gtk.CheckButton is not a subclass of Gtk.Button! LOL


class SortOptionsBox(gtk.Box):
	def __init__(self, mainWin: gtk.Window) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.mainWin = mainWin
		###
		self.set_spacing(5)
		###
		hbox = HBox(spacing=5)
		sortCheck = gtk.CheckButton(label="Sort entries by")
		sortKeyCombo = gtk.ComboBoxText()
		for _sk in namedSortKeyList:
			sortKeyCombo.append_text(_sk.desc)
		sortKeyCombo.set_active(sortKeyNames.index(defaultSortKeyName))
		sortKeyCombo.set_sensitive(False)
		# sortKeyCombo.connect("changed", self.sortKeyComboChanged)
		self.sortCheck = sortCheck
		self.sortKeyCombo = sortKeyCombo
		sortCheck.connect("toggled", self.onSortCheckToggled)
		pack(hbox, sortCheck)
		pack(hbox, sortKeyCombo)
		pack(self, hbox)
		###
		hbox = self.encodingHBox = HBox(spacing=5)
		encodingRadio = self.encodingRadio = gtk.CheckButton(label="Sort Encoding")
		encodingEntry = self.encodingEntry = gtk.Entry()
		encodingEntry.set_text("utf-8")
		encodingEntry.set_width_chars(15)
		pack(hbox, gtk.Label(label="    "))
		pack(hbox, encodingRadio)
		pack(hbox, encodingEntry)
		pack(self, hbox)
		encodingRadio.set_active(True)
		###
		sortRadioSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sortRadioSizeGroup.add_widget(encodingRadio)
		###
		self.show()

	def onSortCheckToggled(self, *_args: object) -> None:
		sort = self.sortCheck.get_active()
		self.sortKeyCombo.set_sensitive(sort)
		self.encodingHBox.set_sensitive(sort)

	def updateWidgets(self) -> None:
		convertOptions = self.mainWin.convertOptions
		sort = convertOptions.get("sort")
		self.sortCheck.set_active(sort)
		self.sortKeyCombo.set_sensitive(sort)
		self.encodingHBox.set_sensitive(sort)

		sortKeyName = convertOptions.get("sortKeyName")
		if sortKeyName:
			self.sortKeyCombo.set_active(sortKeyNames.index(sortKeyName))

		sortEncoding = convertOptions.get("sortEncoding", "utf-8")
		self.encodingEntry.set_text(sortEncoding)

	def applyChanges(self) -> None:
		convertOptions = self.mainWin.convertOptions
		sort = self.sortCheck.get_active()
		if not sort:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				if param in convertOptions:
					del convertOptions[param]
			return

		sortKeyDesc = self.sortKeyCombo.get_active_text()
		convertOptions["sort"] = sort
		convertOptions["sortKeyName"] = sortKeyNameByDesc[sortKeyDesc]
		if self.encodingRadio.get_active():
			convertOptions["sortEncoding"] = self.encodingEntry.get_text()
