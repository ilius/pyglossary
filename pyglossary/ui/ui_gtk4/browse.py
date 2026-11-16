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

"""
Glossary entry browser for the GTK 4 UI.

Lets users search and preview entries from the loaded input glossary before or
after conversion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gi.repository import GLib as glib
from gi.repository import Gtk as gtk

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository import Gio as gio

__all__ = ["BrowseButton"]


class BrowseButton(gtk.Button):
	"""Browse Button."""

	def __init__(
		self,
		setFilePathFunc: Callable[[str], None],
		label: str = "Browse",
		actionSave: bool = False,
		title: str = "Select File",
		folderToggle: bool = False,
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
		self.folderToggle = folderToggle

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

	def _runWithFolderToggle(self) -> None:
		dialog = gtk.FileChooserDialog(
			title=self.title,
			transient_for=self.get_root(),
			action=gtk.FileChooserAction.OPEN,
		)
		dialog.add_button("Cancel", gtk.ResponseType.CANCEL)
		dialog.add_button("Open", gtk.ResponseType.ACCEPT)
		folderCheck = gtk.CheckButton(label="Select Folder")

		def onToggled(button: gtk.CheckButton) -> None:
			dialog.set_action(
				gtk.FileChooserAction.SELECT_FOLDER
				if button.get_active()
				else gtk.FileChooserAction.OPEN,
			)

		folderCheck.connect("toggled", onToggled)
		dialog.get_content_area().append(folderCheck)

		def onResponse(dlg: gtk.FileChooserDialog, response: int) -> None:
			if response == gtk.ResponseType.ACCEPT:
				file = dlg.get_file()
				if file is not None:
					self.setFilePathFunc(file.get_path())
			dlg.destroy()

		dialog.connect("response", onResponse)
		dialog.show()

	def onClick(self, _widget: gtk.Widget) -> None:
		if self.folderToggle and not self.actionSave:
			self._runWithFolderToggle()
			return
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
