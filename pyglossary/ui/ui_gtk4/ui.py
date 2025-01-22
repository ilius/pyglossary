# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2008-2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from gi.repository import Gio as gio
from gi.repository import Gtk as gtk

from pyglossary.ui.base import UIBase

from .mainwin import MainWindow

log = logging.getLogger("pyglossary")

# gtk.Window.set_default_icon_from_file(logo)  # removed in Gtk 4.0


class UI(UIBase, gtk.Application):
	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		UIBase.__init__(self)
		gtk.Application.__init__(
			self,
			application_id="apps.pyglossary",
			flags=gio.ApplicationFlags.FLAGS_NONE,
		)
		self.progressbar = progressbar
		self.runArgs = {}

	def run(self, **kwargs) -> None:
		self.runArgs = kwargs
		gtk.Application.run(self)

	def do_activate(self) -> None:
		MainWindow(
			ui=self,
			app=self,
			progressbar=self.progressbar,
		).run(**self.runArgs)
