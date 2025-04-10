# -*- coding: utf-8 -*-
# mypy: ignore-errors
# ui_gtk.py
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
import traceback
from os.path import abspath, isfile
from typing import TYPE_CHECKING, Any

import gi

from pyglossary import core
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.sort_keys import defaultSortKeyName, namedSortKeyList
from pyglossary.text_utils import urlToPath

from .base import (
	UIBase,
	aboutText,
	authors,
	licenseText,
	logo,
)
from .dependency import checkDepends
from .version import getVersion

gi.require_version("Gtk", "3.0")

from gi.repository import Gio as gio
from gi.repository import GLib as glib

from .gtk3_utils import gdk, gtk  # noqa: E402
from .gtk3_utils.about import AboutWidget  # noqa: E402
from .gtk3_utils.dialog import MyDialog  # noqa: E402
from .gtk3_utils.resize_button import ResizeButton  # noqa: E402
from .gtk3_utils.utils import (  # noqa: E402
	HBox,
	VBox,
	dialog_add_button,
	imageFromFile,
	pack,
	rgba_parse,
	showInfo,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.plugin_prop import PluginProp

# from gi.repository import GdkPixbuf

log = logging.getLogger("pyglossary")

glib.set_prgname("PyGlossary (Gtk3)")
glib.set_application_name("PyGlossary (Gtk3)")
gtk.Window.set_default_icon_from_file(logo)

_ = str  # later replace with translator function

pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}
readDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canRead
]
writeDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canWrite
]


def getMonitor() -> gdk.Monitor | None:
	display = gdk.Display.get_default()

	monitor = display.get_monitor_at_point(1, 1)
	if monitor is not None:
		log.debug("getMonitor: using get_monitor_at_point")
		return monitor

	monitor = display.get_primary_monitor()
	if monitor is not None:
		log.debug("getMonitor: using get_primary_monitor")
		return monitor

	monitor = display.get_monitor_at_window(gdk.get_default_root_window())
	if monitor is not None:
		log.debug("getMonitor: using get_monitor_at_window")
		return monitor

	return None


def getWorkAreaSize() -> tuple[int, int] | None:
	monitor = getMonitor()
	if monitor is None:
		return None
	rect = monitor.get_workarea()
	return rect.width, rect.height


class FormatDialog(gtk.Dialog):
	def __init__(
		self,
		descList: list[str],
		parent: gtk.Widget | None = None,
		**kwargs,
	) -> None:
		gtk.Dialog.__init__(self, parent=parent, **kwargs)
		self.descList = descList
		self.items = descList
		self.activeDesc = ""
		##
		self.connect("response", lambda _w, _e: self.hide())
		dialog_add_button(
			self,
			"gtk-cancel",
			"_Cancel",
			gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		###
		treev = gtk.TreeView()
		treeModel = gtk.ListStore(str)
		treev.set_headers_visible(False)
		treev.set_model(treeModel)
		treev.connect("row-activated", self.rowActivated)
		# treev.connect("response", self.onResponse)
		###
		self.treev = treev
		#############
		cell = gtk.CellRendererText(editable=False)
		col = gtk.TreeViewColumn(
			title="Descriptin",
			cell_renderer=cell,
			text=0,
		)
		col.set_property("expand", True)
		col.set_resizable(True)
		treev.append_column(col)
		self.descCol = col
		############
		hbox = HBox(spacing=15)
		hbox.set_border_width(10)
		pack(hbox, gtk.Label("Search:"))
		entry = self.entry = gtk.Entry()
		pack(hbox, entry, 1, 1)
		pack(self.vbox, hbox)
		###
		entry.connect("changed", self.onEntryChange)
		############
		self.swin = swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		pack(self.vbox, swin, 1, 1)
		self.vbox.show_all()
		##
		treev.set_can_focus(True)  # no need, just to be safe
		treev.set_can_default(True)
		treev.set_receives_default(True)
		# print("can_focus:", treev.get_can_focus())
		# print("can_default:", treev.get_can_default())
		# print("receives_default:", treev.get_receives_default())
		####
		self.updateTree()
		self.resize(400, 400)
		self.connect("realize", self.onRealize)

	def onRealize(self, _widget: Any = None) -> None:
		if self.activeDesc:
			self.treev.grab_focus()
		else:
			self.entry.grab_focus()

	def onEntryChange(self, entry: gtk.Entry) -> None:
		text = entry.get_text().strip()
		if not text:
			self.items = self.descList
			self.updateTree()
			return

		text = text.lower()
		descList = self.descList

		items1 = []
		items2 = []
		for desc in descList:
			if desc.lower().startswith(text):
				items1.append(desc)
			elif text in desc.lower():
				items2.append(desc)

		self.items = items1 + items2
		self.updateTree()

	def setCursor(self, desc: str) -> None:
		model = self.treev.get_model()
		iter_ = model.iter_children(None)
		while iter_ is not None:
			if model.get_value(iter_, 0) == desc:
				path = model.get_path(iter_)
				self.treev.set_cursor(path, self.descCol, False)
				self.treev.scroll_to_cell(path)
				return
			iter_ = model.iter_next(iter_)

	def updateTree(self) -> None:
		model = self.treev.get_model()
		model.clear()
		for desc in self.items:
			model.append([desc])

		if self.activeDesc:
			self.setCursor(self.activeDesc)

	def getActive(self) -> PluginProp | None:
		iter_ = self.treev.get_selection().get_selected()[1]
		if iter_ is None:
			return None
		model = self.treev.get_model()
		desc = model.get_value(iter_, 0)
		return pluginByDesc[desc]

	def setActive(self, plugin: PluginProp) -> None:
		if plugin is None:
			self.activeDesc = ""
			return
		desc = plugin.description
		self.activeDesc = desc
		self.setCursor(desc)

	def rowActivated(
		self,
		treev: gtk.TreeView,
		path: gtk.GtkTreePath,
		_col: Any,
	) -> None:
		model = treev.get_model()
		iter_ = model.get_iter(path)
		desc = model.get_value(iter_, 0)
		self.activeDesc = desc
		self.response(gtk.ResponseType.OK)

	# def onResponse


class FormatButton(gtk.Button):
	noneLabel = "[Select Format]"
	dialogTitle = "Select Format"

	def __init__(self, descList: list[str], parent: gtk.Widget | None = None) -> None:
		gtk.Button.__init__(self)
		self.set_label(self.noneLabel)
		###
		self.descList = descList
		self._parent = parent
		self.activePlugin = None
		###
		self.connect("clicked", self.onClick)

	def onChanged(self, _obj: Any = None) -> None:
		pass

	def onClick(self, _button: Any = None) -> None:
		dialog = FormatDialog(
			descList=self.descList,
			parent=self._parent,
			title=self.dialogTitle,
		)
		dialog.setActive(self.activePlugin)
		if dialog.run() != gtk.ResponseType.OK:
			return

		plugin = dialog.getActive()
		self.activePlugin = plugin
		if plugin:
			self.set_label(plugin.description)
		else:
			self.set_label(self.noneLabel)
		self.onChanged()

	def getActive(self) -> str:
		if self.activePlugin is None:
			return ""
		return self.activePlugin.name

	def setActive(self, formatName: str) -> None:
		plugin = Glossary.plugins[formatName]
		self.activePlugin = plugin
		self.set_label(plugin.description)
		self.onChanged()


class FormatOptionsDialog(gtk.Dialog):
	commentLen = 60

	def __init__(
		self,
		formatName: str,
		options: list[str],
		optionsValues: dict[str, Any],
		parent: gtk.Widget | None = None,
	) -> None:
		gtk.Dialog.__init__(self, parent=parent)
		optionsProp = Glossary.plugins[formatName].optionsProp
		self.optionsProp = optionsProp
		##
		self.connect("response", lambda _w, _e: self.hide())
		dialog_add_button(
			self,
			"gtk-cancel",
			"_Cancel",
			gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		###
		treev = gtk.TreeView()
		treeModel = gtk.ListStore(
			bool,  # enable
			str,  # name
			str,  # comment
			str,  # value
		)
		treev.set_headers_clickable(True)
		treev.set_model(treeModel)
		treev.connect("row-activated", self.rowActivated)
		treev.connect("button-press-event", self.treeviewButtonPress)
		###
		self.treev = treev
		#############
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.enableToggled)
		col = gtk.TreeViewColumn(title="Enable", cell_renderer=cell)
		col.add_attribute(cell, "active", 0)
		# cell.set_active(False)
		col.set_property("expand", False)
		col.set_resizable(True)
		treev.append_column(col)
		###
		col = gtk.TreeViewColumn(
			title="Name",
			cell_renderer=gtk.CellRendererText(),
			text=1,
		)
		col.set_property("expand", False)
		col.set_resizable(True)
		treev.append_column(col)
		###
		cell = gtk.CellRendererText(editable=True)
		self.valueCell = cell
		self.valueCol = 3
		cell.connect("edited", self.valueEdited)
		col = gtk.TreeViewColumn(
			title="Value",
			cell_renderer=cell,
			text=self.valueCol,
		)
		col.set_property("expand", True)
		col.set_resizable(True)
		col.set_min_width(200)
		treev.append_column(col)
		###
		col = gtk.TreeViewColumn(
			title="Comment",
			cell_renderer=gtk.CellRendererText(),
			text=2,
		)
		col.set_property("expand", False)
		col.set_resizable(False)
		treev.append_column(col)
		#############
		for name in options:
			prop = optionsProp[name]
			comment = prop.longComment
			if len(comment) > self.commentLen:
				comment = comment[: self.commentLen] + "..."
			if prop.typ != "bool" and not prop.values:
				comment += " (double-click to edit)"
			treeModel.append(
				[
					name in optionsValues,  # enable
					name,  # name
					comment,  # comment
					str(optionsValues.get(name, "")),  # value
				],
			)
		############
		pack(self.vbox, treev, 1, 1)
		self.vbox.show_all()

	def enableToggled(self, cell: gtk.CellRenderer, path: gtk.TreePath) -> None:
		# enable is column 0
		model = self.treev.get_model()
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 0, active)

	def valueEdited(self, _cell: Any, path: gtk.TreePath, rawValue: str) -> None:
		# value is column 3
		model = self.treev.get_model()
		itr = model.get_iter(path)
		optName = model.get_value(itr, 1)
		prop = self.optionsProp[optName]
		if not prop.customValue:
			return
		enable = True
		if rawValue == "" and prop.typ != "str":  # noqa: PLC1901
			enable = False
		elif not prop.validateRaw(rawValue):
			log.error(f"invalid {prop.typ} value: {optName} = {rawValue!r}")
			return
		model.set_value(itr, self.valueCol, rawValue)
		model.set_value(itr, 0, enable)

	def rowActivated(self, _treev: Any, path: gtk.TreePath, _col: Any) -> bool:
		# forceMenu=True because we can not enter edit mode
		# if double-clicked on a cell other than Value
		return self.valueCellClicked(path, forceMenu=True)

	def treeviewButtonPress(self, treev: gtk.TreeView, gevent: gdk.ButtonEvent) -> bool:
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

	def valueItemActivate(self, item: gtk.MenuItem, itr: gtk.TreeIter) -> None:
		# value is column 3
		value = item.get_label()
		model = self.treev.get_model()
		model.set_value(itr, self.valueCol, value)
		model.set_value(itr, 0, True)  # enable it

	def valueCustomOpenDialog(self, itr: gtk.TreeIter, optName: str) -> None:
		model = self.treev.get_model()
		prop = self.optionsProp[optName]
		currentValue = model.get_value(itr, self.valueCol)
		optDesc = optName
		if prop.comment:
			optDesc += f" ({prop.comment})"
		label = gtk.Label(label=f"Value for {optDesc}")
		dialog = gtk.Dialog(parent=self, title="Option Value")
		dialog.connect("response", lambda _w, _e: dialog.hide())
		dialog_add_button(
			dialog,
			"gtk-cancel",
			"_Cancel",
			gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			dialog,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		pack(dialog.vbox, label, 0, 0)
		entry = gtk.Entry()
		entry.set_text(currentValue)
		entry.connect("activate", lambda _w: dialog.response(gtk.ResponseType.OK))
		pack(dialog.vbox, entry, 0, 0)
		dialog.vbox.show_all()
		if dialog.run() != gtk.ResponseType.OK:
			return
		value = entry.get_text()
		model.set_value(itr, self.valueCol, value)
		model.set_value(itr, 0, True)  # enable it

	def valueItemCustomActivate(
		self,
		_item: gtk.MenuItem,
		itr: gtk.TreeIter,
	) -> None:
		model = self.treev.get_model()
		optName = model.get_value(itr, 1)
		self.valueCustomOpenDialog(itr, optName)

	def valueCellClicked(self, path: gtk.TreePath, forceMenu: bool = False) -> bool:
		"""
		Returns True if event is handled, False if not handled
		(need to enter edit mode).
		"""
		model = self.treev.get_model()
		itr = model.get_iter(path)
		optName = model.get_value(itr, 1)
		prop = self.optionsProp[optName]
		if prop.typ == "bool":
			rawValue = model.get_value(itr, self.valueCol)
			if rawValue == "":  # noqa: PLC1901
				value = False
			else:
				value, isValid = prop.evaluate(rawValue)
				if not isValid:
					log.error(f"invalid {optName} = {rawValue!r}")
					value = False
			model.set_value(itr, self.valueCol, str(not value))
			model.set_value(itr, 0, True)  # enable it
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

	def getOptionsValues(self) -> dict[str, Any]:
		model = self.treev.get_model()
		optionsValues: dict[str, Any] = {}
		for row in model:
			if not row[0]:  # not enable
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


class FormatBox(FormatButton):
	def __init__(
		self,
		descList: list[str],
		parent: gtk.Widget | None = None,
		onChange: Callable | None = None,
	) -> None:
		FormatButton.__init__(self, descList, parent=parent)

		self._onChange = onChange
		self.optionsValues = {}

		self.optionsButton = gtk.Button(label="Options")
		self.optionsButton.set_image(
			gtk.Image.new_from_icon_name(
				"gtk-preferences",
				gtk.IconSize.BUTTON,
			),
		)
		self.optionsButton.connect("clicked", self.openOptions)

		self.dependsButton = gtk.Button(label="Install dependencies")
		self.dependsButton.pkgNames = []
		self.dependsButton.connect("clicked", self.dependsButtonClicked)

	def setOptionsValues(self, optionsValues: dict[str, Any]) -> None:
		self.optionsValues = optionsValues

	def kind(self) -> str:
		"""Return 'r' or 'w'."""
		raise NotImplementedError

	def getActiveOptions(self) -> list[str] | None:
		raise NotImplementedError

	def hasOptions(self) -> bool:
		return bool(self.getActiveOptions())  # not None or []

	def openOptions(self, _button: Any = None) -> None:
		formatName = self.getActive()
		options = self.getActiveOptions()
		if options is None:
			return
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

	def dependsButtonClicked(self, button: gtk.Button) -> None:
		formatName = self.getActive()
		pkgNames = button.pkgNames
		if not pkgNames:
			print("All dependencies are stattisfied for " + formatName)
			return
		pkgNamesStr = " ".join(pkgNames)
		msg = f"Run the following command:\n{core.pip} install {pkgNamesStr}"
		showInfo(
			msg,
			title="Dependencies for " + formatName,
			selectable=True,
			parent=self._parent,
		)
		self.onChanged(self)

	def onChanged(self, _widget: Any = None) -> None:
		name = self.getActive()
		if not name:
			self.optionsButton.set_visible(False)
			return
		self.optionsValues.clear()

		self.optionsButton.set_visible(bool(self.getActiveOptions()))

		kind = self.kind()
		plugin = Glossary.plugins[name]
		if kind == "r":
			depends = plugin.readDepends
		elif kind == "w":
			depends = plugin.writeDepends
		else:
			raise RuntimeError(f"invalid {kind=}")
		uninstalled = checkDepends(depends)

		self.dependsButton.pkgNames = uninstalled
		self.dependsButton.set_visible(bool(uninstalled))

		if self._onChange:
			self._onChange()


class InputFormatBox(FormatBox):
	dialogTitle = "Select Input Format"

	def __init__(self, **kwargs) -> None:
		FormatBox.__init__(self, readDesc, **kwargs)

	def kind(self) -> str:
		"""Return 'r' or 'w'."""
		return "r"

	def getActiveOptions(self) -> list[str] | None:
		formatName = self.getActive()
		if not formatName:
			return None
		return list(Glossary.formatsReadOptions[formatName])


class OutputFormatBox(FormatBox):
	dialogTitle = "Select Output Format"

	def __init__(self, **kwargs) -> None:
		FormatBox.__init__(self, writeDesc, **kwargs)

	def kind(self) -> str:
		"""Return 'r' or 'w'."""
		return "w"

	def getActiveOptions(self) -> list[str] | None:
		formatName = self.getActive()
		if not formatName:
			return None
		return list(Glossary.formatsWriteOptions[formatName])


class GtkTextviewLogHandler(logging.Handler):
	def __init__(self, ui: UI, textview_dict: dict[str, gtk.TextView]) -> None:
		logging.Handler.__init__(self)

		self.ui = ui
		self.buffers = {}
		for levelNameCap in log.levelNamesCap[:-1]:
			levelName = levelNameCap.upper()
			textview = textview_dict[levelName]

			buff = textview.get_buffer()
			tag = gtk.TextTag.new(levelName)
			buff.get_tag_table().add(tag)

			self.buffers[levelName] = buff

	def getTag(self, levelname: str) -> gtk.TextTag:
		return self.buffers[levelname].get_tag_table().lookup(levelname)

	def setColor(self, levelname: str, rgba: gdk.RGBA) -> None:
		self.getTag(levelname).set_property("foreground-rgba", rgba)
		# foreground-gdk is deprecated since Gtk 3.4

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		# msg = msg.replace("\x00", "")

		if record.exc_info:
			type_, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(type_, value, tback),
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

		if record.levelno == logging.CRITICAL:
			self.ui.status(record.getMessage())


class GtkSingleTextviewLogHandler(GtkTextviewLogHandler):
	def __init__(self, ui: UI, textview: gtk.TextView) -> None:
		GtkTextviewLogHandler.__init__(
			self,
			ui,
			{
				"CRITICAL": textview,
				"ERROR": textview,
				"WARNING": textview,
				"INFO": textview,
				"DEBUG": textview,
				"TRACE": textview,
			},
		)


class BrowseButton(gtk.Button):
	def __init__(
		self,
		setFilePathFunc: Callable[[str], None],
		label: str = "Browse",
		actionSave: bool = False,
		title: str = "Select File",
	) -> None:
		gtk.Button.__init__(self)

		self.set_label(label)
		self.set_image(
			gtk.Image.new_from_icon_name(
				"document-save" if actionSave else "document-open",
				gtk.IconSize.BUTTON,
			),
		)

		self.actionSave = actionSave
		self.setFilePathFunc = setFilePathFunc
		self.title = title

		self.connect("clicked", self.onClick)

	def onClick(self, _widget: Any) -> None:
		fcd = gtk.FileChooserNative(
			transient_for=(
				self.get_root() if hasattr(self, "get_root") else self.get_toplevel()
			),
			action=gtk.FileChooserAction.SAVE
			if self.actionSave
			else gtk.FileChooserAction.OPEN,
			title=self.title,
		)
		fcd.connect("response", lambda _w, _e: fcd.hide())
		fcd.connect(
			"file-activated",
			lambda _w: fcd.response(gtk.ResponseType.ACCEPT),
		)
		if fcd.run() == gtk.ResponseType.ACCEPT:
			self.setFilePathFunc(fcd.get_filename())
		fcd.destroy()


sortKeyNameByDesc = {_sk.desc: _sk.name for _sk in namedSortKeyList}
sortKeyNames = [_sk.name for _sk in namedSortKeyList]


class SortOptionsBox(gtk.Box):
	def __init__(self, ui: UI) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.ui = ui
		###
		hbox = gtk.HBox()
		sortCheck = gtk.CheckButton("Sort entries by")
		sortKeyCombo = gtk.ComboBoxText()
		for _sk in namedSortKeyList:
			sortKeyCombo.append_text(_sk.desc)
		sortKeyCombo.set_active(sortKeyNames.index(defaultSortKeyName))
		sortKeyCombo.set_border_width(0)
		sortKeyCombo.set_sensitive(False)
		# sortKeyCombo.connect("changed", self.sortKeyComboChanged)
		self.sortCheck = sortCheck
		self.sortKeyCombo = sortKeyCombo
		sortCheck.connect("clicked", self.onSortCheckClicked)
		pack(hbox, sortCheck, 0, 0, padding=5)
		pack(hbox, sortKeyCombo, 0, 0, padding=5)
		pack(self, hbox, 0, 0, padding=5)
		###
		hbox = self.encodingHBox = gtk.HBox()
		encodingCheck = self.encodingCheck = gtk.CheckButton(label="Sort Encoding")
		encodingEntry = self.encodingEntry = gtk.Entry()
		encodingEntry.set_text("utf-8")
		encodingEntry.set_width_chars(15)
		pack(hbox, gtk.Label(label="    "))
		pack(hbox, encodingCheck, 0, 0)
		pack(hbox, encodingEntry, 0, 0, padding=5)
		pack(self, hbox, 0, 0, padding=5)
		###
		# RadioButton in Gtk3 is very unstable,
		# I could not make set_group work at all!
		# encodingRadio.get_group() == [encodingRadio]
		# localeRadio.set_group(encodingRadio) says:
		#     TypeError: Must be sequence, not RadioButton
		# localeRadio.set_group([encodingRadio]) causes a crash!!
		# but localeRadio.join_group(encodingRadio) works,
		#     so does group= argument to RadioButton()
		# Note: RadioButton does not exist in Gtk 4.0,
		# you have to use CheckButton with its new set_group() method

		hbox = self.localeHBox = gtk.HBox()
		localeEntry = self.localeEntry = gtk.Entry()
		localeEntry.set_width_chars(15)
		pack(hbox, gtk.Label(label="    "))
		pack(hbox, gtk.Label(label="Sort Locale"), 0, 0)
		pack(hbox, localeEntry, 0, 0, padding=5)
		pack(self, hbox, 0, 0, padding=5)
		###
		self.show_all()

	def onSortCheckClicked(self, check: gtk.CheckButton) -> None:
		sort = check.get_active()
		self.sortKeyCombo.set_sensitive(sort)
		self.encodingHBox.set_sensitive(sort)
		self.localeHBox.set_sensitive(sort)

	def updateWidgets(self) -> None:
		convertOptions = self.ui.convertOptions
		sort = convertOptions.get("sort")
		self.sortCheck.set_active(sort)
		self.sortKeyCombo.set_sensitive(sort)
		self.encodingHBox.set_sensitive(sort)
		self.localeHBox.set_sensitive(sort)

		sortKeyName = convertOptions.get("sortKeyName")
		if sortKeyName:
			sortKeyName, _, localeName = sortKeyName.partition(":")
			if sortKeyName:
				self.sortKeyCombo.set_active(sortKeyNames.index(sortKeyName))
			self.localeEntry.set_text(localeName)

		if "sortEncoding" in convertOptions:
			self.encodingCheck.set_active(True)
			self.encodingEntry.set_text(convertOptions["sortEncoding"])

	def applyChanges(self) -> None:
		convertOptions = self.ui.convertOptions
		sort = self.sortCheck.get_active()
		if not sort:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				if param in convertOptions:
					del convertOptions[param]
			return

		sortKeyDesc = self.sortKeyCombo.get_active_text()
		sortKeyName = sortKeyNameByDesc[sortKeyDesc]
		sortLocale = self.localeEntry.get_text()
		if sortLocale:
			sortKeyName = f"{sortKeyName}:{sortLocale}"

		convertOptions["sort"] = True
		convertOptions["sortKeyName"] = sortKeyName
		if self.encodingCheck.get_active():
			convertOptions["sortEncoding"] = self.encodingEntry.get_text()


class GeneralOptionsDialog(gtk.Dialog):
	def onDeleteEvent(self, _widget: Any, _event: Any) -> bool:
		self.hide()
		return True

	def onResponse(self, _widget: Any, _event: Any) -> bool:
		self.applyChanges()
		self.hide()
		return True

	def __init__(self, ui: UI, **kwargs) -> None:
		gtk.Dialog.__init__(
			self,
			transient_for=ui,
			**kwargs,
		)
		self.set_title("General Options")
		self.ui = ui
		##
		self.resize(600, 500)
		self.connect("delete-event", self.onDeleteEvent)
		##
		self.connect("response", self.onResponse)
		dialog_add_button(
			self,
			"gtk-ok",
			"_OK",
			gtk.ResponseType.OK,
		)
		##
		hpad = 10
		vpad = 5
		##
		self.sortOptionsBox = SortOptionsBox(ui)
		pack(self.vbox, self.sortOptionsBox, 0, 0, padding=vpad)
		##
		hbox = gtk.HBox()
		self.sqliteCheck = gtk.CheckButton(label="SQLite mode")
		pack(hbox, self.sqliteCheck, 0, 0, padding=hpad)
		pack(self.vbox, hbox, 0, 0, padding=vpad)
		##
		self.configParams = {
			"save_info_json": False,
			"lower": False,
			"skip_resources": False,
			"rtl": False,
			"enable_alts": True,
			"cleanup": True,
			"remove_html_all": True,
		}
		self.configCheckButtons = {}
		configDefDict = UIBase.configDefDict
		for param in self.configParams:
			hbox = gtk.HBox()
			comment = configDefDict[param].comment
			comment = comment.split("\n")[0]
			checkButton = gtk.CheckButton(
				label=comment,
			)
			self.configCheckButtons[param] = checkButton
			pack(hbox, checkButton, 0, 0, padding=hpad)
			pack(self.vbox, hbox, 0, 0, padding=vpad)
		##
		self.updateWidgets()
		self.vbox.show_all()

	def getSQLite(self) -> bool:
		convertOptions = self.ui.convertOptions
		sqlite = convertOptions.get("sqlite")
		if sqlite is not None:
			return sqlite
		return self.ui.config.get("auto_sqlite", True)

	def updateWidgets(self) -> None:
		config = self.ui.config
		self.sortOptionsBox.updateWidgets()
		self.sqliteCheck.set_active(self.getSQLite())
		for param, check in self.configCheckButtons.items():
			default = self.configParams[param]
			check.set_active(config.get(param, default))

	def applyChanges(self) -> None:
		# print("applyChanges")
		self.sortOptionsBox.applyChanges()

		convertOptions = self.ui.convertOptions
		config = self.ui.config

		convertOptions["sqlite"] = self.sqliteCheck.get_active()

		for param, check in self.configCheckButtons.items():
			config[param] = check.get_active()


class OptionsButton(gtk.MenuButton):
	def __init__(
		self,
		ui: UI,
		onReadOptionClick: Callable,
		onWriteOptionClick: Callable,
	) -> None:
		gtk.MenuButton.__init__(self, label=" Options ")
		self.ui = ui
		self.generalDialog = None
		###
		menu = gtk.Menu()
		##
		itemGeneral = gtk.MenuItem("General Options")
		itemGeneral.connect("activate", self._onGeneralOptionClick)
		menu.append(itemGeneral)
		##
		self.itemRead = gtk.MenuItem("Input Options")
		self.itemRead.connect("activate", onReadOptionClick)
		self.itemRead.set_sensitive(False)
		menu.append(self.itemRead)
		##
		self.itemWrite = gtk.MenuItem("Output Options")
		self.itemWrite.connect("activate", onWriteOptionClick)
		self.itemWrite.set_sensitive(False)
		menu.append(self.itemWrite)
		##
		menu.show_all()
		self.set_popup(menu)

	def _onGeneralOptionClick(self, _widget: Any) -> None:
		if self.generalDialog is None:
			self.generalDialog = GeneralOptionsDialog(self.ui)
		self.generalDialog.present()

	def setEnableReadOptions(self, enable: bool) -> None:
		self.itemRead.set_sensitive(enable)

	def setEnableWriteOptions(self, enable: bool) -> None:
		self.itemWrite.set_sensitive(enable)


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
		if progressbar:
			self.progressBar = gtk.ProgressBar()
			self.progressBar.set_fraction(0)
		else:
			self.progressBar = None
		self.runArgs = {}
		self.progressTitle = ""
		self.mainWin: MainWindow | None = None

	def run(self, **kwargs) -> None:
		self.runArgs = kwargs
		gtk.Application.run(self)

	def do_activate(self) -> None:
		self.mainWin = MainWindow(
			ui=self,
			app=self,
			progressBar=self.progressBar,
		)
		self.mainWin.run(**self.runArgs)

	def progressInit(self, title: str) -> None:
		self.progressTitle = title

	def progress(self, ratio: float, text: str = "") -> None:
		if self.mainWin is None:
			return
		if not text:
			text = "%" + str(int(ratio * 100))
		text += " - " + self.progressTitle
		self.progressBar.set_fraction(ratio)
		# self.progressBar.set_text(text)  # not working
		self.mainWin.status(text)
		while gtk.events_pending():
			gtk.main_iteration_do(False)


class MainWindow(gtk.Dialog, MyDialog):
	def status(self, msg: str) -> None:
		# try:
		# 	_id = self.statusMsgDict[msg]
		# except KeyError:
		# 	_id = self.statusMsgDict[msg] = self.statusNewId
		# 	self.statusNewId += 1
		id_ = self.statusBar.get_context_id(msg)
		self.statusBar.push(id_, msg)

	def __init__(
		self,
		ui: UIBase,
		app: gtk.Application,
		progressBar: gtk.ProgressBar | None,
	) -> None:
		self.app = app
		self.ui = ui
		###
		gtk.Dialog.__init__(self)
		self.set_title("PyGlossary (Gtk3)")
		###
		self.progressBar = progressBar
		self.progressbarEnable = progressBar is not None
		#####
		screenSize = getWorkAreaSize()
		if screenSize:
			winSize = min(800, screenSize[0] - 50, screenSize[1] - 50)
			self.resize(winSize, winSize)
			# print(f"{screenSize = }")
		#####
		self.connect("delete-event", self.onDeleteEvent)
		self.pages = []
		# self.statusNewId = 0
		# self.statusMsgDict = {}## message -> id
		#####
		self.convertOptions = {}
		#####
		self.styleProvider = gtk.CssProvider()
		gtk.StyleContext.add_provider_for_screen(
			gdk.Screen.get_default(),
			self.styleProvider,
			gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		css = "check {min-width: 1.25em; min-height: 1.25em;}\n"
		self.styleProvider.load_from_data(css.encode("utf-8"))
		#####
		self.assert_quit = False
		self.path = ""
		# ____________________ Tab 1 - Convert ____________________ #
		labelSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		buttonSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		vbox = VBox()
		vbox.label = _("Convert")
		vbox.icon = ""  # "*.png"
		self.pages.append(vbox)
		######
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Input File:"))
		pack(hbox, hbox.label)
		labelSizeGroup.add_widget(hbox.label)
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
		buttonSizeGroup.add_widget(button)
		pack(vbox, hbox)
		##
		self.convertInputEntry.connect(
			"changed",
			self.convertInputEntryChanged,
		)
		###
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Input Format:"))
		pack(hbox, hbox.label)
		labelSizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.inputFormatBox = InputFormatBox(
			parent=self,
			onChange=self.onInputFormatChange,
		)
		buttonSizeGroup.add_widget(self.inputFormatBox.optionsButton)
		pack(hbox, self.inputFormatBox)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.inputFormatBox.dependsButton)
		pack(hbox, self.inputFormatBox.optionsButton)
		pack(vbox, hbox)
		#####
		vbox.sep1 = gtk.Label(label="")
		vbox.sep1.show()
		pack(vbox, vbox.sep1)
		#####
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Output File:"))
		pack(hbox, hbox.label)
		labelSizeGroup.add_widget(hbox.label)
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
		buttonSizeGroup.add_widget(button)
		pack(vbox, hbox)
		##
		self.convertOutputEntry.connect(
			"changed",
			self.convertOutputEntryChanged,
		)
		###
		hbox = HBox(spacing=3)
		hbox.label = gtk.Label(label=_("Output Format:"))
		pack(hbox, hbox.label)
		labelSizeGroup.add_widget(hbox.label)
		hbox.label.set_property("xalign", 0)
		self.outputFormatBox = OutputFormatBox(
			parent=self,
			onChange=self.onOutputFormatChange,
		)
		buttonSizeGroup.add_widget(self.outputFormatBox.optionsButton)
		pack(hbox, self.outputFormatBox)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.outputFormatBox.dependsButton)
		pack(hbox, self.outputFormatBox.optionsButton)
		pack(vbox, hbox)
		#####
		hbox = HBox(spacing=10)
		label = gtk.Label(label="")
		pack(hbox, label, 1, 1, 5)
		##
		self.optionsButton = OptionsButton(
			self,
			onReadOptionClick=self.inputFormatBox.openOptions,
			onWriteOptionClick=self.outputFormatBox.openOptions,
		)
		# self.optionsButton.set_size_request(300, 40)
		pack(hbox, self.optionsButton, 0, 0, 0)
		##
		self.convertButton = gtk.Button()
		self.convertButton.set_label("Convert")
		self.convertButton.connect("clicked", self.convertClicked)
		self.convertButton.set_size_request(300, 40)
		pack(hbox, self.convertButton, 0, 0, 10)
		##
		pack(vbox, hbox, 0, 0, 15)
		#####
		self.convertConsoleTextview = textview = gtk.TextView()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.set_border_width(0)
		swin.add(textview)
		pack(vbox, swin, 1, 1)
		# ____________________________________________________________ #
		about = AboutWidget(
			logo=logo,
			header=f"PyGlossary\nVersion {getVersion()}",
			# about=summary,
			about=f'{aboutText}\n<a href="{core.homePage}">{core.homePage}</a>',
			authors="\n".join(authors),
			license_text=licenseText,
		)
		about.label = _("About")
		about.icon = ""  # "*.png"
		self.pages.append(about)
		# ____________________________________________________________ #
		handler = GtkSingleTextviewLogHandler(self, textview)
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
		handler.setColor("TRACE", rgba_parse("white"))
		###
		textview.get_buffer().set_text("Output & Error Console:\n")
		textview.set_editable(False)
		# ____________________________________________________________ #
		if progressBar:
			# progressBar.set_text(_("Progress Bar"))
			# progressBar.get_style_context()
			# progressBar.set_property("height-request", 20)
			pack(vbox, progressBar, 0, 0)
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
		clearButton.set_tooltip_text("Clear Console")
		pack(hbox, clearButton, 0, 0)
		####
		# hbox.sepLabel1 = gtk.Label(label="")
		# pack(hbox, hbox.sepLabel1, 1, 1)
		######
		hbox.verbosityLabel = gtk.Label(label=_("Verbosity:"))
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
		self.statusBar = gtk.Statusbar()
		pack(hbox, self.statusBar, 1, 1)
		####
		hbox.resizeButton = ResizeButton(self)
		pack(hbox, hbox.resizeButton, 0, 0)
		######
		pack(vbox, hbox, 0, 0)
		# ____________________________________________________________ #
		notebook = gtk.Notebook()
		self.notebook = notebook
		#########
		for vbox in self.pages:
			label = gtk.Label(label=vbox.label)
			label.set_use_underline(True)
			vb = VBox(spacing=3)
			if vbox.icon:
				vbox.image = imageFromFile(vbox.icon)
				pack(vb, vbox.image)
			pack(vb, label)
			vb.show_all()
			notebook.append_page(vbox, vb)
			try:
				notebook.set_tab_reorderable(vbox, True)
			except AttributeError:
				pass
		#######################
		pack(self.vbox, notebook, 1, 1)
		# for i in ui.pagesOrder:
		# 	try:
		# 		j = pagesOrder[i]
		# 	except IndexError:
		# 		continue
		# 	notebook.reorder_child(self.pages[i], j)
		# ____________________________________________________________ #
		self.vbox.show_all()
		notebook.set_current_page(0)  # Convert tab
		self.inputFormatBox.dependsButton.hide()
		self.outputFormatBox.dependsButton.hide()
		self.inputFormatBox.optionsButton.hide()
		self.outputFormatBox.optionsButton.hide()
		########
		self.status("Select input file")

	def onInputFormatChange(self) -> None:
		self.optionsButton.setEnableReadOptions(self.inputFormatBox.hasOptions())

	def onOutputFormatChange(self) -> None:
		self.optionsButton.setEnableWriteOptions(self.outputFormatBox.hasOptions())

	def run(  # noqa: PLR0913
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		config: dict[str, Any] | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> None:
		self.config = config

		if inputFilename:
			self.convertInputEntry.set_text(abspath(inputFilename))
		if outputFilename:
			self.convertOutputEntry.set_text(abspath(outputFilename))

		if inputFormat:
			self.inputFormatBox.setActive(inputFormat)
		if outputFormat:
			self.outputFormatBox.setActive(outputFormat)

		if reverse:
			log.error("Gtk interface does not support Reverse feature")

		if readOptions:
			self.inputFormatBox.setOptionsValues(readOptions)
		if writeOptions:
			self.outputFormatBox.setOptionsValues(writeOptions)

		self.convertOptions = convertOptions
		if convertOptions:
			log.debug(f"Using {convertOptions=}")

		self._glossarySetAttrs = glossarySetAttrs or {}

		self.convertInputEntry.grab_focus()
		gtk.Dialog.present(self)
		gtk.main()

	def onDeleteEvent(self, _widget: Any, _event: Any) -> None:
		self.destroy()
		# gtk.main_quit()
		# if called while converting, main_quit does not exit program,
		# it keeps printing warnings,
		# and makes you close the terminal or force kill the process
		gtk.main_quit()

	def consoleClearButtonClicked(self, _widget: Any = None) -> None:
		self.convertConsoleTextview.get_buffer().set_text("")

	def verbosityComboChanged(self, _widget: Any = None) -> None:
		verbosity = self.verbosityCombo.get_active()
		# or int(self.verbosityCombo.get_active_text())
		log.setVerbosity(verbosity)

	def convertClicked(self, _widget: Any = None) -> None:
		inPath = self.convertInputEntry.get_text()
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormat = self.inputFormatBox.getActive()

		outPath = self.convertOutputEntry.get_text()
		if not outPath:
			log.critical("Output file path is empty!")
			return
		outFormat = self.outputFormatBox.getActive()

		self.status("Converting...")
		while gtk.events_pending():
			gtk.main_iteration_do(False)

		self.convertButton.set_sensitive(False)
		self.progressTitle = "Converting"
		readOptions = self.inputFormatBox.optionsValues
		writeOptions = self.outputFormatBox.optionsValues

		glos = Glossary(ui=self.ui)
		glos.config = self.config
		glos.progressbar = self.progressbarEnable

		for attr, value in self._glossarySetAttrs.items():
			setattr(glos, attr, value)

		log.debug(f"readOptions: {readOptions}")
		log.debug(f"writeOptions: {writeOptions}")
		log.debug(f"convertOptions: {self.convertOptions}")
		log.debug(f"config: {self.config}")

		try:
			glos.convert(
				ConvertArgs(
					inPath,
					inputFormat=inFormat,
					outputFilename=outPath,
					outputFormat=outFormat,
					readOptions=readOptions,
					writeOptions=writeOptions,
					**self.convertOptions,
				),
			)
			self.status("Convert finished")

		except Error as e:
			log.critical(str(e))
			glos.cleanup()

		finally:
			self.convertButton.set_sensitive(True)
			self.assert_quit = False
			self.progressTitle = ""

	def convertInputEntryChanged(self, _widget: Any = None) -> None:
		inPath = self.convertInputEntry.get_text()
		inFormat = self.inputFormatBox.getActive()
		if inPath.startswith("file://"):
			inPath = urlToPath(inPath)
			self.convertInputEntry.set_text(inPath)

		if self.config["ui_autoSetFormat"] and not inFormat:
			try:
				inputArgs = Glossary.detectInputFormat(inPath)
			except Error:
				pass
			else:
				self.inputFormatBox.setActive(inputArgs.formatName)

		if not isfile(inPath):
			return

		self.status("Select output file")

	def convertOutputEntryChanged(self, _widget: Any = None) -> None:
		outPath = self.convertOutputEntry.get_text()
		outFormat = self.outputFormatBox.getActive()
		if not outPath:
			return
		if outPath.startswith("file://"):
			outPath = urlToPath(outPath)
			self.convertOutputEntry.set_text(outPath)

		if self.config["ui_autoSetFormat"] and not outFormat:
			try:
				outputArgs = Glossary.detectOutputFormat(
					filename=outPath,
					inputFilename=self.convertInputEntry.get_text(),
				)
			except Error:
				pass
			else:
				outFormat = outputArgs.formatName
				self.outputFormatBox.setActive(outFormat)

		if outFormat:
			self.status('Press "Convert"')
		else:
			self.status("Select output format")
