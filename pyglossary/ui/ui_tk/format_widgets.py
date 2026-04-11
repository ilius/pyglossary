# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Protocol

from pyglossary.glossary_v2 import Glossary
from pyglossary.option import IntOption, Option
from pyglossary.text_utils import escapeNTB, unescapeNTB

from .utils import (
	decodeGeometry,
	encodeGeometry,
	newButton,
	set_window_icon,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.logger import Logger
	from pyglossary.option import Option

__all__ = ["FormatButton", "FormatOptionsDialog"]

log: Logger = logging.getLogger("pyglossary")

pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}


class FormatDialog(tk.Toplevel):
	def __init__(  # noqa: PLR0913
		self,
		rootWin: tk.Tk,
		descList: list[str],
		title: str,
		onOk: Callable,
		button: FormatButton,
		activeDesc: str = "",
	) -> None:
		tk.Toplevel.__init__(self)
		# bg="#0f0" does not work
		self.descList = descList
		self.items = self.descList
		self.onOk = onOk
		self.activeDesc = activeDesc
		self.lastSearch = None
		self.resizable(width=True, height=True)
		if title:
			self.title(title)
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())

		px, py, pw, ph = decodeGeometry(button.winfo_toplevel().geometry())
		width = 400
		height = 400
		self.geometry(
			encodeGeometry(
				px + pw // 2 - width // 2,
				py + ph // 2 - height // 2,
				width,
				height,
			),
		)

		entryBox = ttk.Frame(master=self)
		ttk.Label(master=entryBox, text="Search: ").pack(side="left")
		entry = self.entry = ttk.Entry(master=entryBox)
		entry.pack(fill="x", expand=True, side="left")
		entryBox.pack(fill="x", padx=5, pady=5)

		entry.bind("<KeyRelease>", self.onEntryKeyRelease)
		entry.focus()

		treevBox = ttk.Frame(master=self)

		treev = self.treev = ttk.Treeview(
			master=treevBox,
			columns=["Description"],
			show="",
		)
		treev.bind("<Double-1>", self.onTreeDoubleClick)
		treev.pack(
			side="left",
			fill="both",
			expand=True,
		)

		vsb = ttk.Scrollbar(
			master=treevBox,
			orient="vertical",
			command=treev.yview,
		)
		vsb.pack(side="right", fill="y")

		treevBox.pack(
			fill="both",
			expand=True,
			padx=5,
			pady=5,
		)

		treev.configure(yscrollcommand=vsb.set)

		if rootWin.tk.call("tk", "windowingsystem") == "x11":
			treev.bind("<Button-4>", self.onTreeviewMouseWheel)
			treev.bind("<Button-5>", self.onTreeviewMouseWheel)

		self.updateTree()

		buttonBox = ttk.Frame(master=self)

		cancelButton = newButton(
			buttonBox,
			text="Cancel",
			command=self.cancelClicked,
		)
		cancelButton.pack(side="right")

		okButton = newButton(
			buttonBox,
			text="  OK  ",
			command=self.okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		okButton.pack(side="right")

		buttonBox.pack(fill="x")

		self.bind("<Return>", self.onReturnPress)
		self.bind("<KP_Enter>", self.onReturnPress)

		self.bind("<Down>", self.onDownPress)
		self.bind("<Up>", self.onUpPress)

		# self.bind("<KeyPress>", self.onKeyPress)

	def onTreeviewMouseWheel(self, event: tk.Event) -> str | None:
		# only register this on X11 (Linux / BSD)
		if not hasattr(event, "num"):
			return None

		self.treev.yview_scroll(-1 if event.num == 4 else 1, "units")
		return "break"

	def setActiveRow(self, desc: str) -> None:
		self.treev.selection_set(desc)
		self.treev.see(desc)

	def updateTree(self) -> None:
		treev = self.treev
		current = treev.get_children()
		if current:
			treev.delete(*current)
		for desc in self.items:
			treev.insert("", "end", values=[desc], iid=desc)
			# iid should be rowId
		if self.activeDesc in self.items:
			self.setActiveRow(self.activeDesc)

	def onEntryKeyRelease(self, _event: tk.Event) -> None:
		text = self.entry.get().strip()
		if text == self.lastSearch:
			return

		if not text:
			self.items = self.descList
			self.updateTree()
			self.lastSearch = text
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
		self.lastSearch = text

	def onTreeDoubleClick(self, _event: tk.Event) -> None:
		self.okClicked()

	def cancelClicked(self) -> None:
		self.destroy()

	def onReturnPress(self, _event: tk.Event) -> None:
		self.okClicked()

	def onDownPress(self, _event: tk.Event) -> None:
		treev = self.treev
		selection = treev.selection()
		if selection:
			nextDesc = treev.next(selection[0])
			if nextDesc:
				self.setActiveRow(nextDesc)
		elif self.items:
			self.setActiveRow(self.items[0])
		treev.focus()

	def onUpPress(self, _event: tk.Event) -> None:
		treev = self.treev
		treev.focus()
		selection = treev.selection()
		if not selection:
			if self.items:
				self.setActiveRow(self.items[0])
			return
		nextDesc = treev.prev(selection[0])
		if nextDesc:
			self.setActiveRow(nextDesc)

	def onKeyPress(self, event: tk.Event) -> None:
		print(f"FormatDialog: onKeyPress: {event}")

	def okClicked(self) -> None:
		treev = self.treev
		selectedList = treev.selection()
		desc = selectedList[0] if selectedList else ""
		self.onOk(desc)
		self.destroy()


class FormatButton(ttk.Button):
	noneLabel = "[Select Format]"

	def __init__(
		self,
		rootWin: tk.Tk,
		descList: list[str],
		dialogTitle: str,
		onChange: Callable,
		master: tk.Widget | None = None,
	) -> None:
		self.rootWin = rootWin
		self.var = tk.StringVar()
		self.var.set(self.noneLabel)
		ttk.Button.__init__(
			self,
			master=master,
			textvariable=self.var,
			command=self.onClick,
		)
		self.descList = descList
		self.dialogTitle = dialogTitle
		self._onChange = onChange
		self.activeDesc = ""
		self.bind("<Return>", self.onEnter)
		self.bind("<KP_Enter>", self.onEnter)

	def onEnter(self, _event: tk.Event | None = None) -> None:
		self.invoke()

	def onChange(self, desc: str) -> None:
		self.setValue(desc)
		self._onChange(desc)

	def get(self) -> str:
		return self.activeDesc

	def setValue(self, desc: str) -> None:
		if desc:
			self.var.set(desc)
		else:
			self.var.set(self.noneLabel)
		self.activeDesc = desc

	def onClick(self) -> None:
		dialog = FormatDialog(
			self.rootWin,
			descList=self.descList,
			title=self.dialogTitle,
			onOk=self.onChange,
			button=self,
			activeDesc=self.activeDesc,
		)
		dialog.focus()


class OptionTkType(Protocol):
	def __init__(self, opt: Option, parent: ttk.Widget) -> None: ...
	@property
	def value(self) -> Any: ...
	@value.setter
	def value(self, x: Any) -> None: ...
	@property
	def widget(self) -> ttk.Widget: ...


class BoolOptionTk:
	def __init__(self, opt: Option, parent: ttk.Widget) -> None:
		frame = ttk.Frame(master=parent)
		frame.pack(side="top", fill="y", expand=True)
		var = tk.IntVar()
		cb = ttk.Checkbutton(
			master=frame,
			variable=var,
			text=f"{opt.displayName} ({opt.comment})",
		)
		cb.pack(fill="x")
		self._frame = frame
		self._var = var

	@property
	def value(self) -> Any:
		return bool(self._var.get())

	@value.setter
	def value(self, x: Any) -> None:
		self._var.set(int(bool(x)))

	@property
	def widget(self) -> ttk.Widget:
		return self._frame


class IntOptionTk:
	def __init__(self, opt: Option, parent: ttk.Widget) -> None:
		assert isinstance(opt, IntOption)
		frame = ttk.Frame(master=parent)
		frame.pack(side="top", fill="y", expand=True)
		ttk.Label(
			master=frame,
			text=f"{opt.displayName}: ",
		).pack(
			side="left",
			expand=False,
		)
		minim = opt.minim
		if minim is None:
			minim = 0
		maxim = opt.maxim
		if maxim is None:
			maxim = 1_000_000_000
		spin = ttk.Spinbox(
			master=frame,
			from_=minim,
			to=maxim,
			increment=1,
			width=max(len(str(minim)), len(str(maxim))) + 1,
		)
		spin.pack(side="left", expand=False)
		ttk.Label(
			master=frame,
			text=opt.comment,
		).pack(
			side="left",
			fill="x",
			expand=True,
		)
		self._frame = frame
		self._spin = spin

	@property
	def value(self) -> Any:
		return int(self._spin.get())

	@value.setter
	def value(self, x: Any) -> None:
		self._spin.set(int(x))

	@property
	def widget(self) -> ttk.Widget:
		return self._frame


class StrOptionTk:
	def __init__(self, opt: Option, parent: ttk.Widget) -> None:
		self.opt = opt
		frame = ttk.Frame(master=parent)
		frame.pack(side="top", fill="y", expand=True)
		ttk.Label(
			master=frame,
			text=f"{opt.displayName} ({opt.comment}): ",
		).pack(side="left")
		entry = ttk.Entry(master=frame)
		entry.pack(side="left", fill="x", expand=True)
		self._frame = frame
		self._entry = entry

		self.valuesVar = None
		if opt.values:
			var = self.valuesVar = tk.StringVar()
			var.trace_add("write", self._optionMenuActivated)
			optMenu = ttk.OptionMenu(frame, var, *tuple(opt.values))
			optMenu.pack(side="left", fill="x")

	def _optionMenuActivated(self, *_args: Any) -> None:
		self.value = self.valuesVar.get()

	@property
	def value(self) -> Any:
		return self.opt.evaluate(self._entry.get())[0]

	@value.setter
	def value(self, x: Any) -> None:
		x = str(x)
		if self.valuesVar is not None:
			self.valuesVar.set(x)
		self._entry.delete(0, tk.END)
		self._entry.insert(0, x)

	@property
	def widget(self) -> ttk.Widget:
		return self._frame


class FileSizeOptionTk(StrOptionTk):
	pass


class HtmlColorOptionTk(StrOptionTk):
	pass


class MultiLineStrOptionTk:
	def __init__(self, opt: Option, parent: ttk.Widget) -> None:
		frame = ttk.Frame(master=parent)
		frame.pack(side="top", fill="y", expand=True)
		ttk.Label(
			master=frame, text=f"{opt.displayName}: {opt.comment} (escaped \\n\\t): "
		).pack(side="left")
		entry = ttk.Entry(master=frame)
		entry.pack(side="left", fill="x", expand=True)
		self._frame = frame
		self._entry = entry

	@property
	def value(self) -> Any:
		return unescapeNTB(self._entry.get())

	@value.setter
	def value(self, x: Any) -> None:
		self._entry.insert(0, escapeNTB(str(x)))

	@property
	def widget(self) -> ttk.Widget:
		return self._frame


class NewlineOptionTk(MultiLineStrOptionTk):
	pass


class LiteralEvalOptionTk:
	typeHint = ""

	def __init__(self, opt: Option, parent: ttk.Widget) -> None:
		frame = ttk.Frame(master=parent)
		frame.pack(side="top", fill="y", expand=True)
		ttk.Label(
			master=frame,
			text=f"{opt.displayName} ({opt.comment}, {self.typeHint}): ",
		).pack(side="left")
		entry = ttk.Entry(master=frame)
		entry.pack(side="left", fill="x", expand=True)
		self._frame = frame
		self._entry = entry

	@property
	def value(self) -> Any:
		return ast.literal_eval(self._entry.get())

	@value.setter
	def value(self, x: Any) -> None:
		self._entry.insert(0, repr(x))

	@property
	def widget(self) -> ttk.Widget:
		return self._frame


class ListOptionTk(LiteralEvalOptionTk):
	typeHint = "Python list"


class DictOptionTk(LiteralEvalOptionTk):
	typeHint = "Python dict"


optionClassByName: dict[str, OptionTkType] = {
	"BoolOption": BoolOptionTk,
	"IntOption": IntOptionTk,
	"StrOption": StrOptionTk,
	"EncodingOption": StrOptionTk,
	"FileSizeOption": FileSizeOptionTk,
	"UnicodeErrorsOption": StrOptionTk,
	"HtmlColorOption": HtmlColorOptionTk,
	"NewlineOption": NewlineOptionTk,
	"ListOption": ListOptionTk,
	"DictOption": DictOptionTk,
	# "FloatOption": FloatOptionTk,  # not used so far!
}


class FormatOptionsDialog(tk.Toplevel):
	commentLen = 60
	kindFormatsOptions = {
		"Read": Glossary.formatsReadOptions,
		"Write": Glossary.formatsWriteOptions,
	}

	def __init__(
		self,
		formatDesc: str,
		kind: str,  # "Read" or "Write"
		values: dict[str, Any],
		okFunc: Callable[[dict[str, Any]]],
		master: tk.Widget | None = None,  # noqa: ARG002
	) -> None:
		formatName = pluginByDesc[formatDesc].name
		tk.Toplevel.__init__(self, master=master)
		# bg="#0f0" does not work
		self.resizable(width=True, height=True)
		self.title(f"{formatDesc} {kind} Options")
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())

		self.format = formatName
		self.kind = kind
		self.values = values
		self.okFunc = okFunc
		self.options = self.kindFormatsOptions[kind][formatName]
		self.optionsProp = Glossary.plugins[formatName].optionsProp
		self.widgets: dict[str, OptionTkType] = {}

		self.createOptionsList()

		buttonBox = ttk.Frame(self)
		okButton = newButton(
			buttonBox,
			text="  OK  ",
			command=self.okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		okButton.pack(side="right")
		buttonBox.pack(fill="x")

	def createOptionsList(self) -> None:
		values = self.values
		frame = self.frame = ttk.Frame(master=self)
		frame.pack(fill="x", expand=True)
		for optName, default in self.options.items():
			prop = self.optionsProp[optName]
			comment = prop.longComment
			if len(comment) > self.commentLen:
				comment = comment[: self.commentLen] + "..."
			widgetClass = optionClassByName.get(prop.__class__.__name__)
			if widgetClass is None:
				log.warning(f"No widget class for option class {prop.__class__}")
				continue
			w = widgetClass(prop, frame)
			ww = w.widget
			ww.parent = frame
			ww.pack(fill="x")
			w.value = values.get(optName, default)
			self.widgets[optName] = w

	def okClicked(self) -> None:
		for optName, widget in self.widgets.items():
			self.values[optName] = widget.value
		self.okFunc(self.values)
		self.destroy()
