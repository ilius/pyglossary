# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.

from __future__ import annotations

from os.path import join

from PyQt4 import QtGui as qt

from pyglossary.core import homeDir
from pyglossary.glossary_v2 import Glossary

from .base import UIBase, logo

noneItem = "Not Selected"


class UI(qt.QWidget, UIBase):
	def __init__(self) -> None:
		qt.QWidget.__init__(self)
		UIBase.__init__(self)
		self.setWindowTitle("PyGlossary (Qt)")
		self.setWindowIcon(qt.QIcon(logo))
		######################
		self.running = False
		self.glos = Glossary(ui=self)
		self.glos.config = self.config
		self.pathI = ""
		self.pathO = ""
		self.fcd_dir = join(homeDir, "Desktop")
		######################
		vbox = qt.QVBoxLayout()
		self.setLayout(vbox)
