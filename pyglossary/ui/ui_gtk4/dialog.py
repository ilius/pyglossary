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

from gi.repository import Gdk as gdk

from .utils import gtk_event_iteration_loop

if TYPE_CHECKING:
	from collections.abc import Callable


class MyDialog:
	def startWaiting(self) -> None:
		self.queue_draw()
		self.vbox.set_sensitive(False)
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.WATCH))
		gtk_event_iteration_loop()

	def endWaiting(self) -> None:
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
		self.vbox.set_sensitive(True)

	def waitingDo(self, func: Callable, *args, **kwargs) -> None:  # noqa: ANN002
		self.startWaiting()
		try:
			func(*args, **kwargs)
		except Exception as e:
			raise e
		finally:
			self.endWaiting()
