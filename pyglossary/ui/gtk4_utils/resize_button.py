# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2016-2017 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from . import gdk, gtk
from .utils import imageFromFile


class ResizeButton(gtk.Box):
	def __init__(self, win, edge=gdk.SurfaceEdge.SOUTH_EAST) -> None:
		gtk.Box.__init__(self)
		self.win = win
		self.edge = edge
		###
		self.image = imageFromFile("resize.png")
		self.append(self.image)
		gesture = gtk.GestureClick.new()
		gesture.connect("pressed", self.buttonPress)
		self.add_controller(gesture)

	def buttonPress(self, gesture, button, x, y):
		# Gesture is subclass of EventController
		pass  # FIXME
		# self.win.begin_resize(
		# 	self.edge,
		# 	button,
		# 	int(gevent.x_root),
		# 	int(gevent.y_root),
		# 	gesture.get_current_event_time(),
		# )
