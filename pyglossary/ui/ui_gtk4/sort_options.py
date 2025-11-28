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


sortKeyNameByDesc = {sk.desc: sk.name for sk in namedSortKeyList}
sortKeyNames = [sk.name for sk in namedSortKeyList]


# Note: RadioButton does not exist in Gtk 4.0,
# you have to use CheckButton with group= arg or set_group() method

# Note: Gtk.CheckButton is not a subclass of Gtk.Button!


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
		for sk in namedSortKeyList:
			sortKeyCombo.append_text(sk.desc)
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
		encodingCheck = self.encodingCheck = gtk.CheckButton(label="Sort Encoding")
		encodingEntry = self.encodingEntry = gtk.Entry()
		encodingEntry.set_text("utf-8")
		encodingEntry.set_width_chars(15)
		pack(hbox, gtk.Label(label="    "))
		pack(hbox, encodingCheck)
		pack(hbox, encodingEntry)
		pack(self, hbox)
		encodingCheck.set_active(True)
		###
		hbox = self.localeHBox = HBox(spacing=5)
		localeEntry = self.localeEntry = gtk.Entry()
		localeEntry.set_width_chars(15)
		localeEntry.set_text("latin")
		pack(hbox, gtk.Label(label="    "))
		self.localeCheck = gtk.CheckButton(
			label="Sort Locale",
			group=self.encodingCheck,
		)
		pack(hbox, self.localeCheck)
		pack(hbox, localeEntry)
		pack(self, hbox)
		###
		checkBoxSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		checkBoxSizeGroup.add_widget(encodingCheck)
		###
		self.show()

	def onSortCheckToggled(self, *_args: object) -> None:
		sort = self.sortCheck.get_active()
		self.sortKeyCombo.set_sensitive(sort)
		self.encodingHBox.set_sensitive(sort)

	def updateWidgets(self) -> None:
		convertOptions = self.mainWin.convertOptions
		sort = bool(convertOptions.get("sort", False))
		self.sortCheck.set_active(sort)
		self.sortKeyCombo.set_sensitive(sort)
		self.encodingHBox.set_sensitive(sort)
		self.localeHBox.set_sensitive(sort)

		if "sortEncoding" in convertOptions:
			self.encodingCheck.set_active(True)
			self.encodingEntry.set_text(convertOptions["sortEncoding"])

		sortKeyName = convertOptions.get("sortKeyName")
		if sortKeyName:
			sortKeyName, _, localeName = sortKeyName.partition(":")
			if sortKeyName:
				self.sortKeyCombo.set_active(sortKeyNames.index(sortKeyName))
			self.localeEntry.set_text(localeName)
			if localeName:
				self.localeCheck.set_active(True)

	def applyChanges(self) -> None:
		convertOptions = self.mainWin.convertOptions
		sort = self.sortCheck.get_active()
		if not sort:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				if param in convertOptions:
					del convertOptions[param]
			return

		convertOptions["sort"] = True

		sortKeyDesc = self.sortKeyCombo.get_active_text()
		sortKeyName = sortKeyNameByDesc[sortKeyDesc]
		if self.localeCheck.get_active():
			sortLocale = self.localeEntry.get_text()
			if sortLocale:
				sortKeyName = f"{sortKeyName}:{sortLocale}"
				if "sortEncoding" in convertOptions:
					del convertOptions["sortEncoding"]
		elif self.encodingCheck.get_active():
			convertOptions["sortEncoding"] = self.encodingEntry.get_text()

		convertOptions["sortKeyName"] = sortKeyName
