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

from typing import TYPE_CHECKING

from gi.repository import Gtk as gtk

from .browse import BrowseButton
from .utils import pack

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["InputFileBox", "OutputFileBox"]

_ = str  # later replace with translator function


class InputFileBox(gtk.Box):
	def __init__(
		self,
		entryChanged: Callable[[gtk.Entry], None],
		labelSizeGroup: gtk.SizeGroup = None,
		buttonSizeGroup: gtk.SizeGroup = None,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL, spacing=3)
		label = gtk.Label(label=_("Input File:"))
		pack(self, label)
		label.set_property("xalign", 0)
		self.entry = gtk.Entry()
		pack(self, self.entry, 1, 1)
		button = BrowseButton(
			self.entry.set_text,
			label="Browse",
			actionSave=False,
			title="Select Input File",
		)
		pack(self, button)
		if labelSizeGroup:
			labelSizeGroup.add_widget(label)
		if buttonSizeGroup:
			buttonSizeGroup.add_widget(button)
		self.entry.connect("changed", entryChanged)

	def get_text(self) -> str:
		return self.entry.get_text()

	def set_text(self, text: str) -> None:
		return self.entry.set_text(text)


class OutputFileBox(gtk.Box):
	def __init__(
		self,
		entryChanged: Callable[[gtk.Entry], None],
		labelSizeGroup: gtk.SizeGroup = None,
		buttonSizeGroup: gtk.SizeGroup = None,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL, spacing=3)
		label = gtk.Label(label=_("Ouput File:"))
		pack(self, label)
		label.set_property("xalign", 0)
		self.entry = gtk.Entry()
		pack(self, self.entry, 1, 1)
		button = BrowseButton(
			self.entry.set_text,
			label="Browse",
			actionSave=True,
			title="Select Output File",
		)
		pack(self, button)
		if labelSizeGroup:
			labelSizeGroup.add_widget(label)
		if buttonSizeGroup:
			buttonSizeGroup.add_widget(button)
		self.entry.connect("changed", entryChanged)

	def get_text(self) -> str:
		return self.entry.get_text()

	def set_text(self, text: str) -> None:
		return self.entry.set_text(text)
