# -*- coding: utf-8 -*-
# ui_qk.py
#
# Copyright © 2010 Saeed Rasooli <saeed.gnu@gmail.com>    (ilius)
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


from glossary import *
from .base import *
from os.path import join

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qc

stderr_saved = sys.stderr
stdout_saved = sys.stdout

# startBold = '\x1b[1m'  # Start Bold # len=4
# startUnderline = '\x1b[4m' # Start Underline # len=4
endFormat = '\x1b[0;0;0m'  # End Format # len=8
# redOnGray = '\x1b[0;1;31;47m'
startRed = '\x1b[31m'

noneItem = 'Not Selected'


class QVirtualFile(object):
	def __init__(self, qtext, mode):
		self.qtext = qtext
		self.mode = mode

	def write(self, text):
		self.qtext.insertPlainText(text)
		if self.mode == 'stdout':
			stdout_saved.write(text)
		elif self.mode == 'stderr':
			stderr_saved.write(startRed+text+endFormat)

	def writelines(self, lines):
		for line in lines:
			self.write(line)

	def flush(self):
		pass

	def isatty(self):
		return 1

	def fileno(self):
		pass


class UI(qt.QWidget, UIBase):
	def __init__(self, ipath, **options):
		qt.QWidget.__init__(self)
		self.setWindowTitle('PyGlossary (Qt)')
		self.setWindowIcon(qt.QIcon(join(uiDir, 'pyglossary.png')))
		######################
		self.running = False
		self.glos = Glossary(ui=self)
		self.pref = {}
		self.pref_load()
		self.pathI = ''
		self.pathO = ''
		self.fcd_dir = join(homeDir, 'Desktop')
		######################
		vbox = qt.QVBoxLayout()
		self.setLayout(vbox)
