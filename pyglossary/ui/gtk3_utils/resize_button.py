# -*- coding: utf-8 -*-
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

from . import *
from .utils import *


class ResizeButton(gtk.EventBox):
	def __init__(self, win, edge=gdk.WindowEdge.SOUTH_EAST):
		gtk.EventBox.__init__(self)
		self.win = win
		self.edge = edge
		###
		self.image = imageFromFile('resize.png')
		self.add(self.image)
		self.connect('button-press-event', self.buttonPress)

	def buttonPress(self, obj, gevent):
		self.win.begin_resize_drag(
			self.edge,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
