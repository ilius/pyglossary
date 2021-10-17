# -*- coding: utf-8 -*-
# ui_qk.py
#
# Copyright © 2010-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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


from pyglossary.glossary import *
from .base import *
from os.path import join

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc

noneItem = 'Not Selected'


class UI(qt.QWidget, UIBase):
	def __init__(self):
		qt.QWidget.__init__(self)
		UIBase.__init__(self)
		self.setWindowTitle('PyGlossary (Qt)')
		self.setWindowIcon(qt.QIcon(join(uiDir, 'pyglossary.png')))
		######################
		self.running = False
		self.glos = Glossary(ui=self)
		self.glos.config = self.config
		self.pathI = ''
		self.pathO = ''
		self.fcd_dir = join(homeDir, 'Desktop')
		######################
		vbox = qt.QVBoxLayout()
		self.setLayout(vbox)
