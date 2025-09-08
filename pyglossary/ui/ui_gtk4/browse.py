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

from gi.repository import GLib as glib
from gi.repository import Gtk as gtk

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository import Gio as gio

__all__ = ["BrowseButton"]


class BrowseButton(gtk.Button):
	def __init__(
		self,
		setFilePathFunc: Callable[[str], None],
		label: str = "Browse",
		actionSave: bool = False,
		title: str = "Select File",
	) -> None:
		gtk.Button.__init__(self)

		self.set_label(label)
		# TODO: self.set_icon_name
		# self.set_image(gtk.Image.new_from_icon_name(
		# 	"document-save" if actionSave else "document-open",
		# 	gtk.IconSize.BUTTON,
		# ))

		self.actionSave = actionSave
		self.setFilePathFunc = setFilePathFunc
		self.title = title

		self.connect("clicked", self.onClick)

	def onFiledialogOpen(
		self,
		filedialog: gtk.FileDialog,
		task: gio.Task,
	) -> None:
		try:
			file = filedialog.open_finish(task)
		except glib.GError:
			return
		if file is None:
			return
		self.setFilePathFunc(file.get_path())

	def onFiledialogSave(
		self,
		filedialog: gtk.FileDialog,
		task: gio.Task,
	) -> None:
		try:
			file = filedialog.save_finish(task)
		except glib.GError:
			return
		if file is None:
			return
		self.setFilePathFunc(file.get_path())

	def onClick(self, _widget: gtk.Widget) -> None:
		dialog = gtk.FileDialog.new()
		dialog.set_title(self.title)
		# dialog.set_initial_folder(dir_name)
		if self.actionSave:
			dialog.save(
				parent=self.get_root(),
				cancellable=None,
				callback=self.onFiledialogSave,
			)
		else:
			dialog.open(
				parent=self.get_root(),
				cancellable=None,
				callback=self.onFiledialogOpen,
			)
