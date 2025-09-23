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

import logging
from typing import Any

from gi.repository import Gdk as gdk
from gi.repository import Gio as gio
from gi.repository import GLib as glib
from gi.repository import Gtk as gtk

from pyglossary.core import appResDir
from pyglossary.ui.base import UIBase

from .mainwin import MainWindow
from .utils import gtk_event_iteration_loop

__all__ = ["UI"]

log = logging.getLogger("pyglossary")

glib.set_prgname("PyGlossary (Gtk4)")
gtk.Window.set_default_icon_name("pyglossary")

# ~/.local/share/icons/hicolor/scalable/apps/pyglossary.svg must exist
# unless we call iconTheme.add_search_path with our res dir, and make sure
# this file exists: res/hicolor/scalable/apps/pyglossary.svg
gtk.IconTheme.get_for_display(gdk.Display.get_default()).add_search_path(appResDir)


class UI(UIBase, gtk.Application):
	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		UIBase.__init__(self)
		gtk.Application.__init__(
			self,
			application_id="com.github.ilius.pyglossary",
			flags=gio.ApplicationFlags.DEFAULT_FLAGS,
		)
		if progressbar:
			self.progressBar = gtk.ProgressBar()
			self.progressBar.set_fraction(0)
		else:
			self.progressBar = None
		self.runArgs = {}
		self.mainWindow: MainWindow | None = None

	def run(self, **kwargs: Any) -> None:
		self.runArgs = kwargs
		gtk.Application.run(self)

	def do_activate(self) -> None:
		self.mainWindow = MainWindow(
			ui=self,
			app=self,
			progressBar=self.progressBar,
		)
		self.mainWindow.run(**self.runArgs)

	def progressInit(self, title: str) -> None:
		self.progressTitle = title

	def progress(self, ratio: float, text: str = "") -> None:
		if self.mainWindow is None:
			return
		if not text:
			text = "%" + str(int(ratio * 100))
		text += " - " + self.progressTitle
		self.progressBar.set_fraction(ratio)
		# self.progressBar.set_text(text)  # not working
		self.mainWindow.status(text)
		gtk_event_iteration_loop()
