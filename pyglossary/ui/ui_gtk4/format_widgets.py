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

import ast
import logging
from typing import TYPE_CHECKING, Any, Protocol

from gi.repository import Gtk as gtk

from pyglossary.core import pip
from pyglossary.glossary_v2 import Glossary
from pyglossary.option import Option
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
readDesc = [plugin.description for plugin in Glossary.plugins.values() if plugin.canRead]
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


class OptionTkType(Protocol):
	def __init__(self, opt: Option) -> None: ...
	@property
	def value(self) -> Any: ...
	@value.setter
	def value(self, x: Any) -> None: ...
	@property
	def widget(self) -> gtk.Widget: ...


class BoolOptionGtk:
	def __init__(self, opt: Option) -> None:
		hbox = HBox()
		cb = gtk.CheckButton(
			label=f"{opt.displayName} ({opt.comment})",
		)
		pack(hbox, cb)
		self._hbox = hbox
		self._cb = cb

	@property
	def value(self) -> Any:
		return self._cb.get_active()

	@value.setter
	def value(self, x: Any) -> None:
		self._cb.set_active(bool(x))

	@property
	def widget(self) -> gtk.Widget:
		return self._hbox


class IntOptionGtk:
	def __init__(self, opt: Option) -> None:
		hbox = HBox()
		pack(
			hbox,
			gtk.Label(label=f"{opt.displayName}: "),
		)
		minim = opt.minim
		if minim is None:
			minim = 0
		maxim = opt.maxim
		if maxim is None:
			maxim = 1_000_000_000
		spin = gtk.SpinButton()
		spin.set_digits(0)
		spin.set_range(minim, maxim)
		# spin.set_width_chars
		pack(hbox, spin)
		self._hbox = hbox
		self._spin = spin

	@property
	def value(self) -> Any:
		return int(self._spin.get_value())

	@value.setter
	def value(self, x: Any) -> None:
		self._spin.set_value(int(x))

	@property
	def widget(self) -> gtk.Widget:
		return self._hbox


class StrOptionGtk:
	def __init__(self, opt: Option) -> None:
		self.opt = opt
		hbox = HBox()
		pack(
			hbox,
			gtk.Label(label=f"{opt.displayName} ({opt.comment}): "),
		)
		self._hbox = hbox
		if opt.customValue:
			combo = gtk.ComboBoxText.new_with_entry()
		else:
			combo = gtk.ComboBoxText.new()
		self._combo = combo
		pack(hbox, combo)
		if opt.values:
			for value in opt.values:
				combo.append_text(value)
			self._width = max(len(x) for x in opt.values)
		else:
			self._width = 10
		combo.get_child().set_width_chars(self._width)

	@property
	def value(self) -> Any:
		return self._combo.get_active_text()

	@value.setter
	def value(self, x: Any) -> None:
		st = str(x)
		values = self.opt.values or []
		try:
			index = values.index(st)
		except ValueError:
			self._combo.append_text(st)
			index = len(self._combo.get_model()) - 1
		self._combo.set_active(index)
		if len(st) > self._width:
			self._width = len(st)
			self._combo.get_child().set_width_chars(len(st))

	@property
	def widget(self) -> gtk.Widget:
		return self._hbox


class FileSizeOptionGtk(StrOptionGtk):
	pass


class HtmlColorOptionGtk(StrOptionGtk):
	pass


class MultiLineStrOptionGtk:
	def __init__(self, opt: Option) -> None:
		hbox = HBox()
		pack(
			hbox,
			gtk.Label(label=f"{opt.displayName} ({opt.comment}): "),
		)
		tview = gtk.TextView()
		frame = gtk.Frame()
		frame.set_child(tview)
		pack(hbox, frame, expand=True)
		self._hbox = hbox
		self._buf = tview.get_buffer()

	@property
	def value(self) -> Any:
		return self._buf.get_text(
			start=self._buf.get_start_iter(),
			end=self._buf.get_end_iter(),
			include_hidden_chars=True,
		)

	@value.setter
	def value(self, x: Any) -> None:
		self._buf.set_text(str(x))

	@property
	def widget(self) -> gtk.Widget:
		return self._hbox


class NewlineOptionGtk(MultiLineStrOptionGtk):
	pass


class LiteralEvalOptionGtk(MultiLineStrOptionGtk):
	@property
	def value(self) -> Any:
		return ast.literal_eval(self._buf.get_text())

	@value.setter
	def value(self, x: Any) -> None:
		self._buf.set_text(repr(x))


class ListOptionGtk(LiteralEvalOptionGtk):
	typeHint = "Python list"


class DictOptionGtk(LiteralEvalOptionGtk):
	typeHint = "Python dict"


optionClassByName: dict[str, OptionTkType] = {
	"BoolOption": BoolOptionGtk,
	"IntOption": IntOptionGtk,
	"StrOption": StrOptionGtk,
	"EncodingOption": StrOptionGtk,
	"FileSizeOption": FileSizeOptionGtk,
	"UnicodeErrorsOption": StrOptionGtk,
	"HtmlColorOption": HtmlColorOptionGtk,
	"NewlineOption": NewlineOptionGtk,
	"ListOption": ListOptionGtk,
	"DictOption": DictOptionGtk,
	# "FloatOption": FloatOptionGtk,  # not used so far!
}


class FormatOptionsDialog(gtk.Dialog):
	commentLen = 60
	actionIds = set()
	kindFormatsOptions = {
		"r": Glossary.formatsReadOptions,
		"w": Glossary.formatsWriteOptions,
	}

	def __init__(
		self,
		app: gtk.Application,
		formatName: str,
		kind: str,  # "Read" or "Write"
		values: dict[str, Any],
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
		self.options = self.kindFormatsOptions[kind][formatName]
		self.values = values
		self.widgets: dict[str, OptionTkType] = {}
		self.createOptionsList()
		###
		# self.treev REMOVED
		############
		self.vbox.show()

	def createOptionsList(self) -> None:
		values = self.values
		for optName, default in self.options.items():
			prop = self.optionsProp[optName]
			comment = prop.longComment
			if len(comment) > self.commentLen:
				comment = comment[: self.commentLen] + "..."
			widgetClass = optionClassByName.get(prop.__class__.__name__)
			if widgetClass is None:
				log.warning(f"No widget class for option class {prop.__class__}")
				continue
			w = widgetClass(prop)
			pack(self.vbox, w.widget)
			w.value = values.get(optName, default)
			self.widgets[optName] = w

	def getOptionsValues(self) -> dict[str, Any]:
		optionsValues: dict[str, Any] = {}
		for optName, widget in self.widgets.items():
			optionsValues[optName] = widget.value
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

	def getActiveOptions(self) -> dict[str, Any] | None:
		raise NotImplementedError

	def optionsButtonClicked(self, _button: gtk.Widget) -> None:
		formatName = self.getActive()
		dialog = FormatOptionsDialog(
			app=self.app,
			formatName=formatName,
			kind=self.kind(),
			values=self._optionsValues,
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

	def getActiveOptions(self) -> dict[str, Any] | None:
		formatName = self.getActive()
		if not formatName:
			return None
		return Glossary.formatsReadOptions[formatName]


class OutputFormatBox(FormatBox):
	dialogTitle = "Select Output Format"

	def __init__(self, app: gtk.Application, **kwargs: Any) -> None:
		FormatBox.__init__(self, app, writeDesc, **kwargs)

	def kind(self) -> str:
		"""Return 'r' or 'w'."""
		return "w"

	def getActiveOptions(self) -> dict[str, Any] | None:
		return Glossary.formatsWriteOptions[self.getActive()]
