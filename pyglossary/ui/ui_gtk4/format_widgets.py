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

import logging
from typing import TYPE_CHECKING, Any

from gi.repository import Gio as gio
from gi.repository import Gtk as gtk

from pyglossary.core import pip
from pyglossary.glossary_v2 import Glossary
from pyglossary.ui.dependency import checkDepends

from .utils import (
	HBox,
	dialog_add_button,
	pack,
	showInfo,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.plugin_prop import PluginProp

__all__ = ["InputFormatBox", "OutputFormatBox"]


_ = str

pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}
readDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canRead
]
writeDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canWrite
]

log = logging.getLogger("pyglossary")


class FormatDialog(gtk.Dialog):
	def __init__(
		self,
		descList: list[str],
		parent: gtk.Widget | None = None,
		**kwargs: Any,
	) -> None:
		gtk.Dialog.__init__(self, transient_for=parent, **kwargs)
		self.set_default_size(400, 400)
		self.vbox = self.get_content_area()
		##
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
		hbox.get_style_context().add_class("margin_05")
		pack(hbox, gtk.Label(label="Search:"))
		entry = self.entry = gtk.Entry()
		pack(hbox, entry, 1, 1)
		pack(self.vbox, hbox)
		###
		entry.connect("changed", self.onEntryChange)
		############
		self.swin = swin = gtk.ScrolledWindow()
		swin.set_child(treev)
		swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		pack(self.vbox, swin, 1, 1)
		self.vbox.show()
		##
		treev.set_can_focus(True)  # no need, just to be safe
		# treev.set_can_default(True)
		treev.set_receives_default(True)
		# print("can_focus:", treev.get_can_focus())
		# print("can_default:", treev.get_can_default())
		# print("receives_default:", treev.get_receives_default())
		####
		self.updateTree()
		self.connect("realize", self.onRealize)

	def onRealize(self, _widget: gtk.Widget = None) -> None:
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
		_col: object,
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

	def __init__(
		self,
		descList: list[str],
		onChanged: Callable,
		parent: gtk.Widget | None = None,
	) -> None:
		gtk.Button.__init__(self)
		self.set_label(self.noneLabel)
		###
		self.descList = descList
		self.onChanged = onChanged
		self._parent = parent
		self.activePlugin = None
		###
		self.connect("clicked", self.onClick)

	def onDialogResponse(self, dialog: gtk.Dialog, response_id: int) -> None:
		print(f"onDialogResponse: {dialog}, {response_id}")
		if response_id != gtk.ResponseType.OK:
			return

		plugin = dialog.getActive()
		self.activePlugin = plugin
		if plugin:
			self.set_label(plugin.description)
		else:
			self.set_label(self.noneLabel)
		self.onChanged()

	def onClick(self, _button: gtk.Widget = None) -> None:
		dialog = FormatDialog(
			descList=self.descList,
			parent=self._parent,
			title=self.dialogTitle,
		)
		dialog.setActive(self.activePlugin)
		dialog.connect("response", self.onDialogResponse)
		dialog.present()

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
	actionIds = set()

	def __init__(
		self,
		app: gtk.Application,
		formatName: str,
		options: list[str],
		optionsValues: dict[str, Any],
		**kwargs: Any,
	) -> None:
		self.app = app
		gtk.Dialog.__init__(self, **kwargs)
		self.vbox = self.get_content_area()
		##
		optionsProp = Glossary.plugins[formatName].optionsProp
		self.optionsProp = optionsProp
		self.formatName = formatName
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

		gesture = gtk.GestureClick.new()
		gesture.connect("pressed", self.treeviewButtonPress)
		treev.add_controller(gesture)
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
		self.vbox.show()

	def enableToggled(self, cell: gtk.CellRenderer, path: gtk.TreePath) -> None:
		# enable is column 0
		model = self.treev.get_model()
		active = not cell.get_active()
		itr = model.get_iter(path)
		model.set_value(itr, 0, active)

	def valueEdited(self, _cell: object, path: gtk.TreePath, rawValue: str) -> None:
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

	def rowActivated(
		self, _treev: gtk.Widget, path: gtk.TreePath, _col: object
	) -> bool:
		# forceMenu=True because we can not enter edit mode
		# if double-clicked on a cell other than Value
		return self.valueCellClicked(path, forceMenu=True)

	def treeviewButtonPress(
		self, _gesture: object, _n_press: object, x: int, y: int
	) -> bool:
		# if gevent.button != 1:
		# 	return False
		x2, y2 = self.treev.convert_widget_to_bin_window_coords(int(x), int(y))
		pos_t = self.treev.get_path_at_pos(x2, y2)
		if not pos_t:
			return False
		# pos_t == path, col, xRel, yRel
		path = pos_t[0]
		col = pos_t[1]
		# cell = col.get_cells()[0]
		if col.get_title() == "Value":
			return self.valueCellClicked(path)
		return False

	def valueItemActivate(self, item: gio.MenuItem, itr: gtk.TreeIter) -> None:
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
		dialog = gtk.Dialog(transient_for=self, title="Option Value")
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
		pack(dialog.vbox, label)
		entry = gtk.Entry()
		entry.set_text(currentValue)
		entry.connect("activate", lambda _w: dialog.response(gtk.ResponseType.OK))
		pack(dialog.vbox, entry)
		dialog.vbox.show()
		dialog.connect("response", self.valueCustomDialogResponse, entry)
		dialog.present()

	def valueCustomDialogResponse(
		self,
		_dialog: gtk.Window,
		response_id: int,
		entry: gtk.Entry,
	) -> None:
		if response_id != gtk.ResponseType.OK:
			return
		model = self.treev.get_model()
		value = entry.get_text()
		print(model, value)
		# FIXME
		# model.set_value(itr, self.valueCol, value)
		# model.set_value(itr, 0, True)  # enable it

	def valueItemCustomActivate(
		self,
		_item: gtk.MenuItem,
		itr: gtk.TreeIter,
	) -> None:
		model = self.treev.get_model()
		optName = model.get_value(itr, 1)
		self.valueCustomOpenDialog(itr, optName)

	def addAction(
		self,
		path: gtk.TreePath,
		name: str,
		callback: Callable,
		itr: gtk.TreeIter,  # noqa: ARG002
		# *args,  # noqa: ANN002
	) -> str:
		name = name.strip()
		actionId = self.formatName + "." + chr(97 + int(path[0])) + "." + name
		print(actionId)
		if actionId not in self.actionIds:
			action = gio.SimpleAction(name=actionId)
			action.set_enabled(True)
			action.connect("activate", callback)  # itr
			self.app.add_action(action)
			# self.install_action(actionId, None, callback)
			self.actionIds.add(actionId)

		return "app." + actionId

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

		print("valueCellClicked: building menu")

		menu = gtk.PopoverMenu()
		menu.set_parent(self.treev)
		# menu.get_menu_model() is None
		menuM = gio.Menu()
		menu.set_menu_model(menuM)  # gio.MenuModel

		# menu.add_child(gtk.Label("Test child"), "test")
		# menu.set_flags(gtk.PopoverMenuFlags.NESTED)

		def setAction(item: gio.MenuItem, name: str, callback: Callable) -> None:
			item.set_detailed_action(
				self.addAction(path, name, callback, itr),
			)

		def newItem(
			label: str,
			name: str = "",
			callback: Callable | None = None,
		) -> gio.MenuItem:
			item = gio.MenuItem()
			item.set_label(label)
			if name:
				setAction(item, name, callback)
			return item

		def addItem(label: str, name: str, callback: Callable) -> None:
			menuM.append_item(newItem(label, name, callback))

		if prop.customValue:
			addItem(
				"[Custom Value]",
				"__custom__",
				self.valueItemCustomActivate,
			)

		# addItem(
		# 	"Test test test",
		# 	"test123",
		# 	self.valueItemCustomActivate,
		# )

		groupedValues = None
		if len(propValues) > 10:
			groupedValues = prop.groupValues()
		if groupedValues:
			for groupName, values in groupedValues.items():
				item = newItem(groupName)
				if values is None:
					setAction(item, groupName, self.valueItemActivate)
				else:
					subMenu = gio.Menu()
					for subValue in values:
						# FIXME: need to pass subValue as arg?
						subMenu.append_item(
							newItem(
								str(subValue),
								f"{groupName}-{subValue}",
								self.valueItemActivate,
							)
						)
					item.set_submenu(subMenu)
				# item.show()
				menuM.append_item(item)
		else:
			for value in propValues:
				addItem(
					value,
					f"value-{value}",
					self.valueItemActivate,
				)

		# menu.show()
		# etime = gtk.get_current_event_time()
		menu.popup()
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


class FormatBox(gtk.Box):
	def __init__(
		self,
		app: gtk.Application,
		descList: list[str],
		parent: gtk.Widget | None = None,
		labelSizeGroup: gtk.SizeGroup = None,
		buttonSizeGroup: gtk.SizeGroup = None,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL, spacing=3)

		self.app = app
		self._parent = parent
		self.button = FormatButton(
			descList,
			parent=parent,
			onChanged=self.onChanged,
		)

		self._optionsValues = {}

		self.optionsButton = gtk.Button(label="Options")
		# TODO: self.optionsButton.set_icon_name
		# self.optionsButton.set_image(gtk.Image.new_from_icon_name(
		# 	"gtk-preferences",
		# 	gtk.IconSize.BUTTON,
		# ))
		self.optionsButton.connect("clicked", self.optionsButtonClicked)

		self.dependsButton = gtk.Button(label="Install dependencies")
		self.dependsButton.pkgNames = []
		self.dependsButton.connect("clicked", self.dependsButtonClicked)

		label = gtk.Label(label=_("Input Format:"), xalign=0)
		pack(self, label)
		pack(self, self.button)
		pack(self, gtk.Label(), 1, 1)
		pack(self, self.dependsButton)
		pack(self, self.optionsButton)

		self.show()
		self.dependsButton.hide()
		self.optionsButton.hide()

		if labelSizeGroup:
			labelSizeGroup.add_widget(label)
		if buttonSizeGroup:
			buttonSizeGroup.add_widget(self.optionsButton)

	def getActive(self) -> str:
		return self.button.getActive()

	def setActive(self, active: str) -> None:
		self.button.setActive(active)

	@property
	def optionsValues(self) -> dict[str, Any]:
		return self._optionsValues

	def setOptionsValues(self, optionsValues: dict[str, Any]) -> None:
		self._optionsValues = optionsValues

	def kind(self) -> str:
		"""Return 'r' or 'w'."""
		raise NotImplementedError

	def getActiveOptions(self) -> list[str] | None:
		raise NotImplementedError

	def optionsButtonClicked(self, _button: gtk.Widget) -> None:
		formatName = self.getActive()
		options = self.getActiveOptions()
		if options is None:
			return
		dialog = FormatOptionsDialog(
			self.app,
			formatName,
			options,
			self._optionsValues,
			transient_for=self._parent,
		)
		dialog.set_title("Options for " + formatName)
		dialog.connect("response", self.optionsDialogResponse)
		dialog.present()

	def optionsDialogResponse(
		self,
		dialog: FormatOptionsDialog,
		response_id: gtk.ResponseType,
	) -> None:
		if response_id == gtk.ResponseType.OK:
			self._optionsValues = dialog.getOptionsValues()
		dialog.destroy()

	def dependsButtonClicked(self, button: gtk.Button) -> None:
		formatName = self.getActive()
		pkgNames = button.pkgNames
		if not pkgNames:
			print("All dependencies are stattisfied for " + formatName)
			return
		pkgNamesStr = " ".join(pkgNames)
		msg = f"Run the following command:\n{pip} install {pkgNamesStr}"
		showInfo(
			msg,
			title="Dependencies for " + formatName,
			selectable=True,
			parent=self._parent,
		)
		self.onChanged(self)

	def onChanged(self, _obj: gtk.Widget = None) -> None:
		name = self.getActive()
		if not name:
			self.optionsButton.set_visible(False)
			return
		self._optionsValues.clear()

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


class InputFormatBox(FormatBox):
	dialogTitle = "Select Input Format"

	def __init__(self, app: gtk.Application, **kwargs: Any) -> None:
		FormatBox.__init__(self, app, readDesc, **kwargs)

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

	def __init__(self, app: gtk.Application, **kwargs: Any) -> None:
		FormatBox.__init__(self, app, writeDesc, **kwargs)

	def kind(self) -> str:
		"""Return 'r' or 'w'."""
		return "w"

	def getActiveOptions(self) -> list[str] | None:
		return list(Glossary.formatsWriteOptions[self.getActive()])
