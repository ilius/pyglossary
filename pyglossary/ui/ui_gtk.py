# -*- coding: utf-8 -*-
# ui_gtk.py
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

from pyglossary.glossary import (
	Glossary,
	homePage,
)

from .base import (
	UIBase,
	logo,
	aboutText,
	authors,
	licenseText,
)

from pyglossary import core
from .dependency import checkDepends

import gi
gi.require_version("Gtk", "3.0")

from .gtk3_utils import *
from .gtk3_utils.utils import *
from .gtk3_utils.dialog import MyDialog
from .gtk3_utils.resize_button import ResizeButton
from .gtk3_utils.about import AboutWidget

# from gi.repository import GdkPixbuf

log = logging.getLogger("pyglossary")

gtk.Window.set_default_icon_from_file(logo)

_ = str  # later replace with translator function


def buffer_get_text(b):
	return b.get_text(
		b.get_start_iter(),
		b.get_end_iter(),
		True,
	)


class FormatOptionsDialog(gtk.Dialog):
	def __init__(self, formatName: str, options: "List[str]", optionsValues: "Dict[str, Any]", parent=None):
		gtk.Dialog.__init__(self, parent=parent)
		optionsProp = Glossary.plugins[formatName].optionsProp
		self.optionsProp = optionsProp
		##
		self.connect("response", lambda w, e: self.hide())
		dialog_add_button(
			self,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		dialog_add_button(
			self,
			"gtk-cancel",
			"_Cancel",
			gtk.ResponseType.CANCEL,
		)
		###
		treev = gtk.TreeView()
		trees = gtk.ListStore(
			bool, # enable
			str, # name
			str, # comment
			str, # value
		)
		treev.set_headers_clickable(True)
		treev.set_model(trees)
		treev.connect("row-activated", self.rowActivated)
		treev.connect("button-press-event", self.treeviewButtonPress)
		###
		self.treev = treev
		#############
		cell = gtk.CellRendererToggle()
		#cell.set_property("activatable", True)
		cell.connect("toggled", self.enableToggled)
		col = gtk.TreeViewColumn(title="Enable", cell_renderer=cell)
		col.add_attribute(cell, "active", 0)
		#cell.set_active(False)
		col.set_property("expand", False)
		col.set_resizable(True)
		treev.append_column(col)
		###
		col = gtk.TreeViewColumn(title="Name", cell_renderer=gtk.CellRendererText(), text=1)
		col.set_property("expand", False)
		col.set_resizable(True)
		treev.append_column(col)
		###
		cell = gtk.CellRendererText(editable=True)
		self.valueCell = cell
		self.valueCol = 3
		cell.connect("edited", self.valueEdited)
		col = gtk.TreeViewColumn(title="Value", cell_renderer=cell, text=self.valueCol)
		col.set_property("expand", True)
		col.set_resizable(True)
		col.set_min_width(200)
		treev.append_column(col)
		###
		col = gtk.TreeViewColumn(title="Comment", cell_renderer=gtk.CellRendererText(), text=2)
		col.set_property("expand", False)
		col.set_resizable(False)
		treev.append_column(col)
		#############
		for name in options:
			prop = optionsProp[name]
			comment = prop.typ
			if prop.comment:
				comment += ", " + prop.comment
			if prop.typ == "str" and not prop.values:
				comment += ", double-click to edit"
			trees.append([
				name in optionsValues, # enable
				name, # name
				comment, # comment
				str(optionsValues.get(name, "")), # value
			])
		############
		pack(self.vbox, treev, 1, 1)
		self.vbox.show_all()

	def enableToggled(self, cell, path):
		# enable is column 0
		model = self.treev.get_model()
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 0, active)

	def valueEdited(self, cell, path, rawValue):
		# value is column 3
		model = self.treev.get_model()
		itr = model.get_iter(path)
		optName = model.get_value(itr, 1)
		prop = self.optionsProp[optName]
		if not prop.customValue:
			return
		enable = True
		if rawValue == "" and prop.typ != "str":
			enable = False
		elif not prop.validateRaw(rawValue):
			log.error(f"invalid {prop.typ} value: {optName} = {rawValue!r}")
			return
		model.set_value(itr, self.valueCol, rawValue)
		model.set_value(itr, 0, enable)

	def rowActivated(self, treev, path, col):
		# forceMenu=True because we can not enter edit mode
		# if double-clicked on a cell other than Value
		return self.valueCellClicked(path, forceMenu=True)

	def treeviewButtonPress(self, treev, gevent):
		if gevent.button != 1:
			return False
		pos_t = treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return False
		# pos_t == path, col, xRel, yRel
		path = pos_t[0]
		col = pos_t[1]
		# cell = col.get_cells()[0]
		if col.get_title() == "Value":
			return self.valueCellClicked(path)
		return False

	def valueItemActivate(self, item: gtk.MenuItem, itr: gtk.TreeIter):
		# value is column 3
		value = item.get_label()
		model = self.treev.get_model()
		model.set_value(itr, self.valueCol, value)
		model.set_value(itr, 0, True) # enable it

	def valueCustomOpenDialog(self, itr: gtk.TreeIter, optName: str):
		model = self.treev.get_model()
		prop = self.optionsProp[optName]
		currentValue = model.get_value(itr, self.valueCol)
		optDesc = optName
		if prop.comment:
			optDesc += f" ({prop.comment})"
		label = gtk.Label(label=f"Value for {optDesc}")
		dialog = gtk.Dialog(parent=self, title="Option Value")
		dialog.connect("response", lambda w, e: dialog.hide())
		dialog_add_button(
			dialog,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		dialog_add_button(
			dialog,
			"gtk-cancel",
			"_Cancel",
			gtk.ResponseType.CANCEL,
		)
		pack(dialog.vbox, label, 0, 0)
		entry = gtk.Entry()
		entry.set_text(currentValue)
		entry.connect("activate", lambda w: dialog.response(gtk.ResponseType.OK))
		pack(dialog.vbox, entry, 0, 0)
		dialog.vbox.show_all()
		if dialog.run() != gtk.ResponseType.OK:
			return
		value = entry.get_text()
		model.set_value(itr, self.valueCol, value)
		model.set_value(itr, 0, True) # enable it

	def valueItemCustomActivate(self, item: gtk.MenuItem, itr: gtk.TreeIter):
		model = self.treev.get_model()
		optName = model.get_value(itr, 1)
		self.valueCustomOpenDialog(itr, optName)

	def valueCellClicked(self, path, forceMenu=False) -> bool:
		"""
		returns True if event is handled, False if not handled (need to enter edit mode)
		"""
		model = self.treev.get_model()
		itr = model.get_iter(path)
		optName = model.get_value(itr, 1)
		prop = self.optionsProp[optName]
		if prop.typ == "bool":
			rawValue = model.get_value(itr, self.valueCol)
			if rawValue == "":
				value = False
			else:
				value, isValid = prop.evaluate(rawValue)
				if not isValid:
					log.error(f"invalid {optName} = {rawValue!r}")
					value = False
			model.set_value(itr, self.valueCol, str(not value))
			model.set_value(itr, 0, True) # enable it
			return True
		propValues = prop.values
		if not propValues:
			if forceMenu:
				propValues = []
			else:
				return False
		menu = gtk.Menu()
		if prop.customValue:
			item = gtk.MenuItem("[Custom Value]")
			item.connect("activate", self.valueItemCustomActivate, itr)
			item.show()
			menu.append(item)
		groupedValues = None
		if len(propValues) > 10:
			groupedValues = prop.groupValues()
		if groupedValues:
			for groupName, values in groupedValues.items():
				item = gtk.MenuItem()
				item.set_label(groupName)
				if values is None:
					item.connect("activate", self.valueItemActivate, itr)
				else:
					subMenu = gtk.Menu()
					for subValue in values:
						subItem = gtk.MenuItem(label=str(subValue))
						subItem.connect("activate", self.valueItemActivate, itr)
						subItem.show()
						subMenu.append(subItem)
					item.set_submenu(subMenu)
				item.show()
				menu.append(item)
		else:
			for value in propValues:
				item = gtk.MenuItem(value)
				item.connect("activate", self.valueItemActivate, itr)
				item.show()
				menu.append(item)
		etime = gtk.get_current_event_time()
		menu.popup(None, None, None, None, 3, etime)
		return True

	def getOptionsValues(self):
		model = self.treev.get_model()
		optionsValues = {}
		for row in model:
			if not row[0]: # not enable
				continue
			optName = row[1]
			rawValue = row[3]
			prop = self.optionsProp[optName]
			value, isValid = prop.evaluate(rawValue)
			if not isValid:
				log.error(f"invalid option value {optName} = {rawValue}")
				continue
			optionsValues[optName] = value
		return optionsValues



class FormatComboBox(gtk.ComboBox):
	def __init__(self, parent=None):
		gtk.ComboBox.__init__(self)
		self._parent = parent
		self.model = gtk.ListStore(
			str,  # format name, hidden
			# GdkPixbuf.Pixbuf,# icon
			str,  # format description, shown
		)
		self.set_model(self.model)

		cell = gtk.CellRendererText()
		cell.set_visible(False)
		pack(self, cell)
		self.add_attribute(cell, "text", 0)

		# cell = gtk.CellRendererPixbuf()
		# pack(self, cell, False)
		# self.add_attribute(cell, "pixbuf", 1)

		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 1)

		self.optionsValues = {}

		self.optionsButton = gtk.Button(label="Options")
		self.optionsButton.connect("clicked", self.optionsButtonClicked)

		self.dependsButton = gtk.Button(label="Install dependencies")
		self.dependsButton.pkgNames = []
		self.dependsButton.connect("clicked", self.dependsButtonClicked)

		self.connect("changed", self.onChanged)

	def setOptionsValues(self, optionsValues: "Dict[str, Any]"):
		self.optionsValues = optionsValues

	def kind(self):
		"returns 'r' or 'w'"
		raise NotImplementedError

	def getActiveOptions(self):
		raise NotImplementedError

	def addFormat(self, _format):
		self.get_model().append((
			_format,
			# icon,
			Glossary.plugins[_format].description,
		))

	def getActive(self):
		index = gtk.ComboBox.get_active(self)
		if index is None or index < 0:
			return ""
		return self.get_model()[index][0]

	def setActive(self, _format):
		for i, row in enumerate(self.get_model()):
			if row[0] == _format:
				gtk.ComboBox.set_active(self, i)
				return

	def optionsButtonClicked(self, button):
		formatName = self.getActive()
		options = self.getActiveOptions()
		dialog = FormatOptionsDialog(
			formatName,
			options,
			self.optionsValues,
			parent=self._parent,
		)
		dialog.set_title("Options for " + formatName)
		if dialog.run() != gtk.ResponseType.OK:
			dialog.destroy()
			return
		self.optionsValues = dialog.getOptionsValues()
		dialog.destroy()

	def dependsButtonClicked(self, button):
		formatName = self.getActive()
		pkgNames = button.pkgNames
		if not pkgNames:
			print("All dependencies are stattisfied for " + formatName)
			return
		pkgNamesStr = " ".join(pkgNames)
		msg = (
			"Run the following command:\n"
			f"{core.pip} install {pkgNamesStr}"
		)
		showInfo(
			msg,
			title="Dependencies for " + formatName,
			selectable=True,
			parent=self._parent,
		)
		self.onChanged(self)

	def onChanged(self, combo):
		name = self.getActive()
		self.optionsValues.clear()

		options = self.getActiveOptions()
		self.optionsButton.set_visible(bool(options))

		kind = self.kind()
		plugin = Glossary.plugins[name]
		if kind == "r":
			cls = plugin.readerClass
		elif kind == "w":
			cls = plugin.writerClass
		else:
			raise RuntimeError(f"invalid kind={kind}")
		uninstalled = checkDepends(cls.depends)

		self.dependsButton.pkgNames = uninstalled
		self.dependsButton.set_visible(bool(uninstalled))


class InputFormatComboBox(FormatComboBox):
	def __init__(self, **kwargs):
		FormatComboBox.__init__(self, **kwargs)
		for _format in Glossary.readFormats:
			self.addFormat(_format)

	def kind(self):
		"returns 'r' or 'w'"
		return "r"

	def getActiveOptions(self):
		return list(Glossary.formatsReadOptions[self.getActive()].keys())


class OutputFormatComboBox(FormatComboBox):
	def __init__(self, **kwargs):
		FormatComboBox.__init__(self, **kwargs)
		for _format in Glossary.writeFormats:
			self.addFormat(_format)

	def kind(self):
		"returns 'r' or 'w'"
		return "w"

	def getActiveOptions(self):
		return list(Glossary.formatsWriteOptions[self.getActive()].keys())


class GtkTextviewLogHandler(logging.Handler):
	def __init__(self, treeview_dict):
		logging.Handler.__init__(self)

		self.buffers = {}
		for levelname in (
			"CRITICAL",
			"ERROR",
			"WARNING",
			"INFO",
			"DEBUG",
		):
			textview = treeview_dict[levelname]

			buff = textview.get_buffer()
			tag = gtk.TextTag.new(levelname)
			buff.get_tag_table().add(tag)

			self.buffers[levelname] = buff

	def getTag(self, levelname):
		return self.buffers[levelname].get_tag_table().lookup(levelname)

	def setColor(self, levelname: str, rgba: gdk.RGBA) -> None:
		self.getTag(levelname).set_property("foreground-rgba", rgba)
		# foreground-gdk is deprecated since Gtk 3.4

	def emit(self, record):
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		# msg = msg.replace("\x00", "")

		if record.exc_info:
			_type, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(_type, value, tback)
			)
			if msg:
				msg += "\n"
			msg += tback_text

		buff = self.buffers[record.levelname]

		buff.insert_with_tags_by_name(
			buff.get_end_iter(),
			msg + "\n",
			record.levelname,
		)


class GtkSingleTextviewLogHandler(GtkTextviewLogHandler):
	def __init__(self, textview):
		GtkTextviewLogHandler.__init__(self, {
			"CRITICAL": textview,
			"ERROR": textview,
			"WARNING": textview,
			"INFO": textview,
			"DEBUG": textview,
		})


class BrowseButton(gtk.Button):
	def __init__(
		self,
		setFilePathFunc,
		label="Browse",
		actionSave=False,
		title="Select File",
	):
		gtk.Button.__init__(self)

		self.set_label(label)
		self.set_image(gtk.Image.new_from_icon_name(
			"document-save" if actionSave else "document-open",
			gtk.IconSize.BUTTON,
		))

		self.actionSave = actionSave
		self.setFilePathFunc = setFilePathFunc
		self.title = title

		self.connect("clicked", self.onClick)

	def onClick(self, widget):
		fcd = gtk.FileChooserDialog(
			transient_for=self.get_toplevel(),
			action=gtk.FileChooserAction.SAVE if self.actionSave
			else gtk.FileChooserAction.OPEN,
			title=self.title,
		)
		fcd.add_button(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL)
		fcd.add_button(gtk.STOCK_OK, gtk.ResponseType.OK)
		fcd.connect("response", lambda w, e: fcd.hide())
		fcd.connect(
			"file-activated",
			lambda w: fcd.response(gtk.ResponseType.OK)
		)
		if fcd.run() == gtk.ResponseType.OK:
			self.setFilePathFunc(fcd.get_filename())
		fcd.destroy()


class UI(gtk.Dialog, MyDialog, UIBase):
	def status(self, msg):
		# try:
		#	_id = self.statusMsgDict[msg]
		# except KeyError:
		#	_id = self.statusMsgDict[msg] = self.statusNewId
		#	self.statusNewId += 1
		_id = self.statusBar.get_context_id(msg)
		self.statusBar.push(_id, msg)

	def __init__(self):
		gtk.Dialog.__init__(self)
		UIBase.__init__(self)
		self.set_title("PyGlossary (Gtk3)")
		self.resize(800, 800)
		self.connect("delete-event", self.onDeleteEvent)
		self.pages = []
		# self.statusNewId = 0
		# self.statusMsgDict = {}## message -> id
		#####
		self._convertOptions = {}
		#####
		self.assert_quit = False
		self.path = ""
		self.glos = Glossary(ui=self)
		# ____________________ Tab 1 - Convert ____________________ #
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		vbox = VBox()
		vbox.label = _("Convert")
		vbox.icon = ""  # "*.png"
		self.pages.append(vbox)
		######
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Input Format")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.convertInputFormatCombo = InputFormatComboBox(parent=self)
		pack(hbox, self.convertInputFormatCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.convertInputFormatCombo.dependsButton)
		pack(hbox, self.convertInputFormatCombo.optionsButton)
		pack(vbox, hbox)
		###
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Input File")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.convertInputEntry = gtk.Entry()
		pack(hbox, self.convertInputEntry, 1, 1)
		button = BrowseButton(
			self.convertInputEntry.set_text,
			label="Browse",
			actionSave=False,
			title="Select Input File",
		)
		pack(hbox, button)
		pack(vbox, hbox)
		##
		self.convertInputEntry.connect(
			"changed",
			self.convertInputEntryChanged,
		)
		#####
		vbox.sep1 = gtk.Label(label="")
		vbox.sep1.show()
		pack(vbox, vbox.sep1)
		#####
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Output Format")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.convertOutputFormatCombo = OutputFormatComboBox(parent=self)
		pack(hbox, self.convertOutputFormatCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.convertOutputFormatCombo.dependsButton)
		pack(hbox, self.convertOutputFormatCombo.optionsButton)
		pack(vbox, hbox)
		###
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Output File")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.convertOutputEntry = gtk.Entry()
		pack(hbox, self.convertOutputEntry, 1, 1)
		button = BrowseButton(
			self.convertOutputEntry.set_text,
			label="Browse",
			actionSave=True,
			title="Select Output File",
		)
		pack(hbox, button)
		pack(vbox, hbox)
		##
		self.convertOutputEntry.connect(
			"changed",
			self.convertOutputEntryChanged,
		)
		#####
		hbox = HBox(spacing=10)
		label = gtk.Label(label="")
		pack(hbox, label, 1, 1, 10)
		self.convertButton = gtk.Button()
		self.convertButton.set_label("Convert")
		self.convertButton.connect("clicked", self.convertClicked)
		pack(hbox, self.convertButton, 1, 1, 10)
		pack(vbox, hbox, 0, 0, 15)
		####
		self.convertConsoleTextview = textview = gtk.TextView()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.set_border_width(0)
		swin.add(textview)
		pack(vbox, swin, 1, 1)
		# ____________________ Tab 2 - Reverse ____________________ #
		self.reverseStatus = ""
		####
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		vbox = VBox()
		vbox.label = _("Reverse")
		vbox.icon = ""  # "*.png"
		# self.pages.append(vbox)
		######
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Input Format")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.reverseInputFormatCombo = InputFormatComboBox()
		pack(hbox, self.reverseInputFormatCombo)
		pack(vbox, hbox)
		###
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Input File")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.reverseInputEntry = gtk.Entry()
		pack(hbox, self.reverseInputEntry, 1, 1)
		button = BrowseButton(
			self.reverseInputEntry.set_text,
			label="Browse",
			actionSave=False,
			title="Select Input File",
		)
		pack(hbox, button)
		pack(vbox, hbox)
		##
		self.reverseInputEntry.connect(
			"changed",
			self.reverseInputEntryChanged,
		)
		#####
		vbox.sep1 = gtk.Label(label="")
		vbox.sep1.show()
		pack(vbox, vbox.sep1)
		#####
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Output Tabfile")+":")
		pack(hbox, hbox.label)
		sizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.reverseOutputEntry = gtk.Entry()
		pack(hbox, self.reverseOutputEntry, 1, 1)
		button = BrowseButton(
			self.reverseOutputEntry.set_text,
			label="Browse",
			actionSave=True,
			title="Select Output File",
		)
		pack(hbox, button)
		pack(vbox, hbox)
		##
		self.reverseOutputEntry.connect(
			"changed",
			self.reverseOutputEntryChanged,
		)
		#####
		hbox = HBox(spacing=3)
		label = gtk.Label(label="")
		pack(hbox, label, 1, 1, 5)
		###
		self.reverseStartButton = gtk.Button()
		self.reverseStartButton.set_label(_("Start"))
		self.reverseStartButton.connect("clicked", self.reverseStartClicked)
		pack(hbox, self.reverseStartButton, 1, 1, 2)
		###
		self.reversePauseButton = gtk.Button()
		self.reversePauseButton.set_label(_("Pause"))
		self.reversePauseButton.set_sensitive(False)
		self.reversePauseButton.connect("clicked", self.reversePauseClicked)
		pack(hbox, self.reversePauseButton, 1, 1, 2)
		###
		self.reverseResumeButton = gtk.Button()
		self.reverseResumeButton.set_label(_("Resume"))
		self.reverseResumeButton.set_sensitive(False)
		self.reverseResumeButton.connect("clicked", self.reverseResumeClicked)
		pack(hbox, self.reverseResumeButton, 1, 1, 2)
		###
		self.reverseStopButton = gtk.Button()
		self.reverseStopButton.set_label(_("Stop"))
		self.reverseStopButton.set_sensitive(False)
		self.reverseStopButton.connect("clicked", self.reverseStopClicked)
		pack(hbox, self.reverseStopButton, 1, 1, 2)
		###
		pack(vbox, hbox, 0, 0, 5)
		######
		about = AboutWidget(
			logo=logo,
			header=f"PyGlossary\nVersion {core.VERSION}",
			# about=summary,
			about=f'{aboutText}\n<a href="{homePage}">{homePage}</a>',
			authors="\n".join(authors),
			license=licenseText,
		)
		about.label = _("About")
		about.icon = ""  # "*.png"
		self.pages.append(about)
		#####
		# ____________________________________________________________ #
		notebook = gtk.Notebook()
		self.notebook = notebook
		#########
		for vbox in self.pages:
			l = gtk.Label(label=vbox.label)
			l.set_use_underline(True)
			vb = VBox(spacing=3)
			if vbox.icon:
				vbox.image = imageFromFile(vbox.icon)
				pack(vb, vbox.image)
			pack(vb, l)
			vb.show_all()
			notebook.append_page(vbox, vb)
			try:
				notebook.set_tab_reorderable(vbox, True)
			except AttributeError:
				pass
		#######################
		pack(self.vbox, notebook, 1, 1)
		# for i in ui.pagesOrder:
		#	try:
		#		j = pagesOrder[i]
		#	except IndexError:
		#		continue
		#	notebook.reorder_child(self.pages[i], j)
		# ____________________________________________________________ #
		handler = GtkSingleTextviewLogHandler(textview)
		log.addHandler(handler)
		###
		textview.override_background_color(
			gtk.StateFlags.NORMAL,
			gdk.RGBA(0, 0, 0, 1),
		)
		###
		handler.setColor("CRITICAL", rgba_parse("red"))
		handler.setColor("ERROR", rgba_parse("red"))
		handler.setColor("WARNING", rgba_parse("yellow"))
		handler.setColor("INFO", rgba_parse("white"))
		handler.setColor("DEBUG", rgba_parse("white"))
		###
		textview.get_buffer().set_text("Output & Error Console:\n")
		textview.set_editable(False)
		# ____________________________________________________________ #
		self.progressTitle = ""
		self.progressBar = pbar = gtk.ProgressBar()
		pbar.set_fraction(0)
		# pbar.set_text(_("Progress Bar"))
		# pbar.get_style_context()
		# pbar.set_property("height-request", 20)
		pack(self.vbox, pbar, 0, 0)
		############
		hbox = HBox(spacing=5)
		clearButton = gtk.Button(
			use_stock=gtk.STOCK_CLEAR,
			always_show_image=True,
			label=_("Clear"),
		)
		clearButton.show_all()
		# image = gtk.Image()
		# image.set_from_stock(gtk.STOCK_CLEAR, gtk.IconSize.MENU)
		# clearButton.add(image)
		clearButton.set_border_width(0)
		clearButton.connect("clicked", self.consoleClearButtonClicked)
		set_tooltip(clearButton, "Clear Console")
		pack(hbox, clearButton, 0, 0)
		####
		# hbox.sepLabel1 = gtk.Label(label="")
		# pack(hbox, hbox.sepLabel1, 1, 1)
		######
		hbox.verbosityLabel = gtk.Label(label=_("Verbosity")+":")
		pack(hbox, hbox.verbosityLabel, 0, 0)
		##
		self.verbosityCombo = combo = gtk.ComboBoxText()
		for level, levelName in enumerate(log.levelNamesCap):
			combo.append_text(f"{level} - {_(levelName)}")
		combo.set_active(log.getVerbosity())
		combo.set_border_width(0)
		combo.connect("changed", self.verbosityComboChanged)
		pack(hbox, combo, 0, 0)
		####
		# hbox.sepLabel2 = gtk.Label(label="")
		# pack(hbox, hbox.sepLabel2, 1, 1)
		####
		self.statusBar = sbar = gtk.Statusbar()
		pack(hbox, self.statusBar, 1, 1)
		####
		hbox.resizeButton = ResizeButton(self)
		pack(hbox, hbox.resizeButton, 0, 0)
		######
		pack(self.vbox, hbox, 0, 0)
		# ____________________________________________________________ #
		self.vbox.show_all()
		notebook.set_current_page(0)  # Convert tab
		self.convertInputFormatCombo.dependsButton.hide()
		self.convertOutputFormatCombo.dependsButton.hide()
		self.convertInputFormatCombo.optionsButton.hide()
		self.convertOutputFormatCombo.optionsButton.hide()
		########
		self.status("Select input file")

	def run(
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		configOptions: "Optional[Dict]" = None,
		readOptions: "Optional[Dict]" = None,
		writeOptions: "Optional[Dict]" = None,
		convertOptions: "Optional[Dict]" = None,
	):
		self.loadConfig(**configOptions)

		if inputFilename:
			self.convertInputEntry.set_text(abspath(inputFilename))
		if outputFilename:
			self.convertOutputEntry.set_text(abspath(outputFilename))

		if inputFormat:
			self.convertInputFormatCombo.setActive(inputFormat)
		if outputFormat:
			self.convertOutputFormatCombo.setActive(outputFormat)

		if reverse:
			log.error(f"Gtk interface does not support Reverse feature")

		if readOptions:
			self.convertInputFormatCombo.setOptionsValues(readOptions)
		if writeOptions:
			self.convertOutputFormatCombo.setOptionsValues(writeOptions)

		self._convertOptions = convertOptions
		if convertOptions:
			log.info(f"Using convertOptions={convertOptions}")

		gtk.Dialog.present(self)
		gtk.main()

	def onDeleteEvent(self, widget, event):
		self.destroy()
		# gtk.main_quit()
		# if callled while converting, main_quit does not exit program,
		# it keeps printing warnings,
		# and makes you close the terminal or force kill the proccess
		sys.exit(0)

	def consoleClearButtonClicked(self, widget=None):
		self.convertConsoleTextview.get_buffer().set_text("")

	def verbosityComboChanged(self, widget=None):
		verbosity = self.verbosityCombo.get_active()
		# or int(self.verbosityCombo.get_active_text())
		log.setVerbosity(verbosity)

	def convertClicked(self, widget=None):
		inPath = self.convertInputEntry.get_text()
		if not inPath:
			self.status("Input file path is empty!")
			log.critical("Input file path is empty!")
			return
		inFormat = self.convertInputFormatCombo.getActive()
		if inFormat:
			inFormatDesc = Glossary.plugins[inFormat].description
		else:
			inFormatDesc = ""
			# log.critical("Input format is empty!");return

		outPath = self.convertOutputEntry.get_text()
		if not outPath:
			self.status("Output file path is empty!")
			log.critical("Output file path is empty!")
			return
		outFormat = self.convertOutputFormatCombo.getActive()
		if outFormat:
			outFormatDesc = Glossary.plugins[outFormat].description
		else:
			outFormatDesc = ""
			# log.critical("Output format is empty!");return

		while gtk.events_pending():
			gtk.main_iteration_do(False)

		self.convertButton.set_sensitive(False)
		self.progressTitle = "Converting"
		readOptions = self.convertInputFormatCombo.optionsValues
		writeOptions = self.convertOutputFormatCombo.optionsValues
		try:
			# if inFormat=="Omnidic":
			#	dicIndex = self.xml.get_widget("spinbutton_omnidic_i")\
			#		.get_value_as_int()
			#	ex = self.glos.readOmnidic(inPath, dicIndex=dicIndex)
			# else:
			log.debug(f"readOptions: {readOptions}")
			log.debug(f"writeOptions: {writeOptions}")
			finalOutputFile = self.glos.convert(
				inPath,
				inputFormat=inFormat,
				outputFilename=outPath,
				outputFormat=outFormat,
				readOptions=readOptions,
				writeOptions=writeOptions,
				**self._convertOptions,
			)
			if finalOutputFile:
				self.status("Convert finished")
			else:
				self.status("Convert failed")
			return bool(finalOutputFile)

		finally:
			self.convertButton.set_sensitive(True)
			self.assert_quit = False
			self.progressTitle = ""

		return True

	def convertInputEntryChanged(self, widget=None):
		inPath = self.convertInputEntry.get_text()
		inFormat = self.convertInputFormatCombo.getActive()
		if inPath.startswith("file://"):
			inPath = urlToPath(inPath)
			self.convertInputEntry.set_text(inPath)

		if self.config["ui_autoSetFormat"] and not inFormat:
			inputArgs = Glossary.detectInputFormat(inPath, quiet=True)
			if inputArgs:
				inFormatNew = inputArgs[1]
				self.convertInputFormatCombo.setActive(inFormatNew)

		if not isfile(inPath):
			return

		self.status("Select output file")

	def convertOutputEntryChanged(self, widget=None):
		outPath = self.convertOutputEntry.get_text()
		outFormat = self.convertOutputFormatCombo.getActive()
		if not outPath:
			return
		if outPath.startswith("file://"):
			outPath = urlToPath(outPath)
			self.convertOutputEntry.set_text(outPath)

		if self.config["ui_autoSetFormat"] and not outFormat:
			outputArgs = Glossary.detectOutputFormat(
				filename=outPath,
				inputFilename=self.convertInputEntry.get_text(),
				quiet=True,
			)
			if outputArgs:
				outFormat = outputArgs[1]
				self.convertOutputFormatCombo.setActive(outFormat)

		if outFormat:
			self.status("Press \"Convert\"")
		else:
			self.status("Select output format")

	def reverseLoad(self):
		pass

	def reverseStartLoop(self):
		pass

	def reverseStart(self):
		if not self.reverseLoad():
			return
		###
		self.reverseStatus = "doing"
		self.reverseStartLoop()
		###
		self.reverseStartButton.set_sensitive(False)
		self.reversePauseButton.set_sensitive(True)
		self.reverseResumeButton.set_sensitive(False)
		self.reverseStopButton.set_sensitive(True)

	def reverseStartClicked(self, widget=None):
		self.waitingDo(self.reverseStart)

	def reversePause(self):
		self.reverseStatus = "pause"
		###
		self.reverseStartButton.set_sensitive(False)
		self.reversePauseButton.set_sensitive(False)
		self.reverseResumeButton.set_sensitive(True)
		self.reverseStopButton.set_sensitive(True)

	def reversePauseClicked(self, widget=None):
		self.waitingDo(self.reversePause)

	def reverseResume(self):
		self.reverseStatus = "doing"
		###
		self.reverseStartButton.set_sensitive(False)
		self.reversePauseButton.set_sensitive(True)
		self.reverseResumeButton.set_sensitive(False)
		self.reverseStopButton.set_sensitive(True)

	def reverseResumeClicked(self, widget=None):
		self.waitingDo(self.reverseResume)

	def reverseStop(self):
		self.reverseStatus = "stop"
		###
		self.reverseStartButton.set_sensitive(True)
		self.reversePauseButton.set_sensitive(False)
		self.reverseResumeButton.set_sensitive(False)
		self.reverseStopButton.set_sensitive(False)

	def reverseStopClicked(self, widget=None):
		self.waitingDo(self.reverseStop)

	def reverseInputEntryChanged(self, widget=None):
		inPath = self.reverseInputEntry.get_text()
		inFormat = self.reverseInputFormatCombo.getActive()
		if inPath.startswith("file://"):
			inPath = urlToPath(inPath)
			self.reverseInputEntry.set_text(inPath)

		if not inFormat and self.config["ui_autoSetFormat"]:
			inputArgs = Glossary.detectInputFormat(inPath, quiet=True)
			if inputArgs:
				inFormat = inputArgs[1]
				self.reverseInputFormatCombo.setActive(inFormat)

	def reverseOutputEntryChanged(self, widget=None):
		pass

	def progressInit(self, title):
		self.progressTitle = title

	def progress(self, rat, text=None):
		if not text:
			text = "%" + str(int(rat * 100))
		text += " - " + self.progressTitle
		self.progressBar.set_fraction(rat)
		# self.progressBar.set_text(text)  # not working
		self.status(text)
		while gtk.events_pending():
			gtk.main_iteration_do(False)
