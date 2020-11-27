# -*- coding: utf-8 -*-
# ui_wx.py
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Thanks to Pier Carteri <m3tr0@dei.unipd.it> for program Py_Shell.py
# Thanks to Milad Rastian for program pySQLiteGUI
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

import shutil
import sys
import os
from os.path import join, isfile, isabs, splitext, abspath
import logging
import traceback

from pyglossary.text_utils import urlToPath
from pyglossary.os_utils import click_website

from pyglossary.glossary import Glossary

from pyglossary import core
from pyglossary.core import homePage

from .base import (
	UIBase,
	logo,
	aboutText,
	authors,
	licenseText,
)

from .dependency import checkDepends

import wx


pluginByDesc = {
	plugin.description: plugin
	for plugin in Glossary.plugins.values()
}
readDesc = [
	plugin.description
	for plugin in Glossary.plugins.values()
	if plugin.canRead
]
writeDesc = [
	plugin.description
	for plugin in Glossary.plugins.values()
	if plugin.canWrite
]



log = logging.getLogger("pyglossary")

app = wx.App()


class FormatComboBox(wx.ComboBox) :
	def __init__(self, parent, choices=[], style=0, **kwargs):
		wx.ComboBox.__init__(
			self,
			parent,
			wx.ID_ANY,
			style=style|wx.CB_DROPDOWN,
			choices=choices,
			**kwargs
		)
		self.choices = choices
		self.Bind(wx.EVT_TEXT, self.OnText)
		self.Bind(wx.EVT_KEY_DOWN, self.OnPress)
		# self.deleteKey = False

	def OnPress(self, event):
		if event.GetKeyCode() == 8:
			self.deleteKey = True
		event.Skip()

	def OnText(self, event):
		currentText = event.GetString().lower()

		# if self.deleteKey:
		#	self.deleteKey = False

		if len(currentText) < 2:
			self.Set(self.choices)
			return

		starts_choices = []
		contains_choices = []
		for choice in self.choices:
			choiceLower = choice.lower()
			if choiceLower.startswith(currentText):
				starts_choices.append(choice)
			elif currentText in choiceLower:
				contains_choices.append(choice)

		matching = starts_choices + contains_choices
		if matching and len(matching) < 4:
			self.Set(matching)
			self.Popup()
		else:
			self.Set(self.choices)


class BrowseButton(wx.Button):
	def __init__(self, panel):
		wx.Button.__init__(self, panel, label="Browse")
		# self.Bind(wx.EVT_BUTTON, self.onClick)


class UI(wx.Dialog, UIBase):
	def __init__(self):
		wx.Dialog.__init__(
			self,
			parent=None,
			id=wx.ID_ANY,
			title="PyGlossary",
			style=(
				wx.RESIZE_BORDER | wx.CLOSE_BOX |
				wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX
			),
		)
		UIBase.__init__(self)

		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		panel_sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(panel_sizer)
		main_sizer.Add(panel, proportion=1, flag=wx.ALL | wx.EXPAND, border=15)

		bag = wx.GridBagSizer(3, 3)
		panel_sizer.Add(bag)
		border = 5

		row = 0
		bag.Add(
			wx.StaticText(panel, label="Input File:"),
			pos=(row, 0),
			flag=wx.LEFT,
			border=border,
		)
		##
		self.convertInputEntry = entry = wx.TextCtrl(
			panel,
			wx.ID_ANY,
			wx.EmptyString,
			wx.DefaultPosition,
			wx.DefaultSize,
			0,
		)
		entry.SetMinSize((300, 30))
		bag.Add(entry, pos=(row, 1), flag=wx.EXPAND, border=border)
		# bag.AddGrowableCol(1, 1) # not working
		##
		button = wx.Button(panel, label="Browse")
		bag.Add(button, pos=(row, 2))
		####
		row += 1
		bag.Add(
			wx.StaticText(panel, label="Input Format:"),
			pos=(row, 0),
			flag=wx.LEFT,
			border=border,
		)
		##
		combo = FormatComboBox(panel, choices=readDesc)
		bag.Add(combo, pos=(row, 1), flag=wx.LEFT | wx.EXPAND)
		##
		button = wx.Button(panel, label="Options")
		bag.Add(button, pos=(row, 2))

		row += 2
		bag.Add(
			wx.StaticText(panel, label="Output File:"),
			pos=(row, 0),
			flag=wx.LEFT, border=border,
		)
		##
		self.convertOutputEntry = entry = wx.TextCtrl(
			panel,
			wx.ID_ANY,
			wx.EmptyString,
			wx.DefaultPosition,
			wx.DefaultSize,
			0,
		)
		entry.SetMinSize((300, 30))
		bag.Add(entry, pos=(row, 1), flag=wx.EXPAND, border=border)
		##
		button = wx.Button(panel, label="Browse")
		bag.Add(button, pos=(row, 2))
		####
		row += 1
		bag.Add(
			wx.StaticText(panel, label="Output Format:"),
			pos=(row, 0),
			flag=wx.LEFT,
			border=border,
		)
		##
		combo = FormatComboBox(panel, choices=writeDesc)
		bag.Add(combo, pos=(row, 1), flag=wx.LEFT | wx.EXPAND)
		##
		button = wx.Button(panel, label="Options")
		bag.Add(button, pos=(row, 2))


		self.SetSizerAndFit(main_sizer)
		#self.SetAutoLayout(True)
		self.Layout()

	def run(
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		config: "Optional[Dict]" = None,
		readOptions: "Optional[Dict]" = None,
		writeOptions: "Optional[Dict]" = None,
		convertOptions: "Optional[Dict]" = None,
	):
		self.config = config

		if inputFilename:
			self.convertInputEntry.SetValue(abspath(inputFilename))

		if outputFilename:
			self.convertOutputEntry.SetValue(abspath(outputFilename))

		if inputFormat:
			self.convertInputFormatCombo.SetValue(
				Glossary.plugins[inputFormat].description
			)

		if outputFormat:
			self.convertOutputFormatCombo.SetValue(
				Glossary.plugins[outputFormat].description
			)

		if reverse:
			log.error(f"Gtk interface does not support Reverse feature")

		#if readOptions:
		#	self.convertInputFormatCombo.setOptionsValues(readOptions)
		#if writeOptions:
		#	self.convertOutputFormatCombo.setOptionsValues(writeOptions)

		self._convertOptions = convertOptions
		if convertOptions:
			log.info(f"Using convertOptions={convertOptions}")

		self.Show()
		app.MainLoop()






