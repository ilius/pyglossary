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
import os
import tkinter as tk
import traceback
from os.path import isfile, join, splitext
from tkinter import filedialog, ttk
from tkinter import font as tkFont
from typing import TYPE_CHECKING, Any, Protocol

from pyglossary.core import confDir, homeDir, homePage, sysName
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.option import IntOption, Option
from pyglossary.os_utils import abspath2
from pyglossary.sort_keys import namedSortKeyList
from pyglossary.text_utils import escapeNTB, unescapeNTB, urlToPath

from .base import (
	UIBase,
	aboutText,
	authors,
	licenseText,
	logo,
)
from .config import configDefDict
from .version import getVersion

if TYPE_CHECKING:
	from collections.abc import Callable
	from tkinter.font import Font

	from pyglossary.config_type import ConfigType
	from pyglossary.logger import Logger

__all__ = ["UI"]

log: Logger = logging.getLogger("pyglossary")

# on Windows: make app DPI-aware, fix blurry fonts
# this causes issues on tk 8.6.x with custom fonts or display scaling ≠ %100
# because many widgets worked based on an assumed system font metric that
# doesn’t always match your actual font
# see https://github.com/ilius/pyglossary/issues/689
if os.sep == "\\" and tk.TkVersion >= 8.7:
	import ctypes

	try:
		# 1 = system DPI aware
		ctypes.windll.shcore.SetProcessDpiAwareness(1)
	except Exception:
		log.exception("")


pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}
readDesc = [plugin.description for plugin in Glossary.plugins.values() if plugin.canRead]
writeDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canWrite
]


def set_window_icon(window: tk.Toplevel) -> None:
	window.iconphoto(
		True,
		tk.PhotoImage(file=logo),
	)


def decodeGeometry(gs: str) -> tuple[int, int, int, int]:
	"""
	Example for gs: "253x252+30+684"
	returns (x, y, w, h).
	"""
	p = gs.split("+")
	w, h = p[0].split("x")
	return (int(p[1]), int(p[2]), int(w), int(h))


def encodeGeometry(x: int, y: int, w: int, h: int) -> str:
	return f"{w}x{h}+{x}+{y}"


def encodeLocation(x: int, y: int) -> str:
	return f"+{x}+{y}"


def centerWindow(win: tk.Tk) -> None:
	"""
	Centers a tkinter window
	:param win: the root or Toplevel window to center.
	"""
	win.update_idletasks()
	width = win.winfo_width()
	frm_width = win.winfo_rootx() - win.winfo_x()
	win_width = width + 2 * frm_width
	height = win.winfo_height()
	titlebar_height = win.winfo_rooty() - win.winfo_y()
	win_height = height + titlebar_height + frm_width
	x = win.winfo_screenwidth() // 2 - win_width // 2
	y = win.winfo_screenheight() // 2 - win_height // 2
	win.geometry(encodeGeometry(x, y, width, height))
	win.deiconify()


def newButton(
	master: tk.Widget,
	text: str,
	command: Callable,
	**kwargs: Any,
) -> ttk.Button:
	button = ttk.Button(
		master,
		text=text,
		command=command,
		**kwargs,
	)

	def onEnter(_event: tk.Event) -> None:
		button.invoke()

	button.bind("<Return>", onEnter)
	button.bind("<KP_Enter>", onEnter)
	return button


def newLabelWithImage(parent: tk.Widget, file: str = "") -> ttk.Label:
	image = tk.PhotoImage(file=file)
	label = ttk.Label(parent, image=image)
	# keep a reference:
	label.image = image
	return label


def newReadOnlyText(
	parent: tk.Widget,
	text: str = "",
	borderwidth: int = 10,
	font: tuple[str, int, str] = ("DejaVu Sans", 11, ""),
) -> tk.Text:
	height = len(text.strip().split("\n"))
	widget = tk.Text(
		parent,
		height=height,
		borderwidth=borderwidth,
		font=font,
	)
	widget.insert(1.0, text)
	widget.pack()

	# widget.bind("<Key>", lambda e: break)
	widget.configure(state=tk.DISABLED)

	return widget


class TkTextLogHandler(logging.Handler):
	def __init__(self, tktext: tk.Text) -> None:
		logging.Handler.__init__(self)
		#####
		tktext.tag_config("CRITICAL", foreground="#ff0000")
		tktext.tag_config("ERROR", foreground="#ff0000")
		tktext.tag_config("WARNING", foreground="#ffff00")
		tktext.tag_config("INFO", foreground="#00ff00")
		tktext.tag_config("DEBUG", foreground="#ffffff")
		tktext.tag_config("TRACE", foreground="#ffffff")
		###
		self.tktext = tktext

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		###
		if record.exc_info:
			type_, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(type_, value, tback),
			)
			if msg:
				msg += "\n"
			msg += tback_text
		###
		self.tktext.insert(
			"end",
			msg + "\n",
			record.levelname,
		)


# Monkey-patch Tkinter
# http://stackoverflow.com/questions/5191830/python-exception-logging
def CallWrapper__call__(self: tk.CallWrapper, *args: str) -> Any:
	"""Apply first function SUBST to arguments, than FUNC."""
	if self.subst:
		args = self.subst(*args)
	try:
		return self.func(*args)
	except Exception:
		log.exception("Exception in Tkinter callback:")


tk.CallWrapper.__call__ = CallWrapper__call__


class ProgressBar(ttk.Frame):
	def __init__(  # noqa: PLR0913
		self,
		rootWin: tk.Tk,
		min_: float,
		max_: float,
		width: int,
		height: int,
		appearance: str,  # "sunken"
		fillColor: str,
		background: str,
		labelColor: str,
		labelFont: str,
		value: float = 0,
	) -> None:
		self.min = min_
		self.max = max_
		self.width = width
		self.height = height
		self.value = value
		ttk.Frame.__init__(
			self,
			rootWin,
			relief=appearance,
		)
		self.canvas = tk.Canvas(
			self,
			height=height,
			width=width,
			bd=0,
			highlightthickness=0,
			background=background,
		)
		self.scale = self.canvas.create_rectangle(
			0,
			0,
			width,
			height,
			fill=fillColor,
		)
		self.label = self.canvas.create_text(
			width / 2,
			height / 2,
			text="",
			anchor="center",
			fill=labelColor,
			font=labelFont,
		)
		self.update()
		self.bind("<Configure>", self.update)
		self.canvas.pack(side="top", fill="x", expand=False)

	def updateProgress(
		self,
		value: float,
		max_: float | None = None,
		text: str = "",
	) -> None:
		if max_:
			self.max = max_
		self.value = value
		self.update(None, text)

	def update(self, event: tk.Event | None = None, labelText: str = "") -> None:
		if event:  # instance of tkinter.Event
			width = getattr(event, "width", None) or int(self.winfo_width())
			if width != self.width:  # window is resized
				self.canvas.coords(self.label, width / 2, self.height / 2)
				self.width = width
		else:
			width = self.width

		self.canvas.coords(
			self.scale,
			0,
			0,
			width * max(min(self.value, self.max), self.min) / self.max,
			self.height,
		)

		if labelText:
			# TODO: replace below `// 10` with a number based on current font size
			self.canvas.itemconfig(
				self.label,
				text=labelText[: width // 10],
			)

		self.canvas.update_idletasks()


# class VerticalProgressBar(ProgressBar):
# def update(self, event=None, labelText="") -> None:
# ...
# self.canvas.coords(
# 	self.scale,
# 	0,
# 	self.height * (1 - value / self.max),
# 	width,
# 	self.height,
# )


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


sortKeyNames = [sk.name for sk in namedSortKeyList]
sortKeyNameByDesc = {sk.desc: sk.name for sk in namedSortKeyList}
sortKeyDescByName = {sk.name: sk.desc for sk in namedSortKeyList}


class SortOptionsBox(ttk.Frame):
	def __init__(
		self,
		ui: UI,
		master: tk.Widget | None = None,
	) -> None:
		self.ui = ui
		ttk.Frame.__init__(self, master=master)
		hbox = ttk.Frame(master=self)
		sortCheckVar = tk.IntVar()
		sortCheck = ttk.Checkbutton(
			master=hbox,
			text="Sort entries by",
			variable=sortCheckVar,
			command=self.onSortCheckClicked,
		)
		sortKeyVar = tk.StringVar()
		sortKeyDescList = [sk.desc for sk in namedSortKeyList]
		sortKeyCombo = ttk.OptionMenu(
			hbox,
			sortKeyVar,
			sortKeyDescList[0],
			*sortKeyDescList,
		)
		self.sortCheckVar = sortCheckVar
		self.sortKeyVar = sortKeyVar
		self.sortKeyCombo = sortKeyCombo
		sortCheck.pack(side="left")
		sortKeyCombo.pack(side="left")
		hbox.pack(side="top", expand=True, fill="both")
		###
		hbox = self.encodingHBox = ttk.Frame(master=self)
		encodingCheckVar = self.encodingCheckVar = tk.IntVar()
		encodingCheck = ttk.Checkbutton(
			master=hbox,
			text="Sort Encoding",
			variable=encodingCheckVar,
		)
		encodingEntry = self.encodingEntry = ttk.Entry(hbox, width=15)
		encodingEntry.delete(0, "end")
		encodingEntry.insert(0, "utf-8")
		ttk.Label(hbox, text="    ").pack(side="left")
		encodingCheck.pack(side="left")
		encodingEntry.pack(side="left")
		hbox.pack(side="top", expand=True, fill="both")
		###
		hbox = self.localeHBox = ttk.Frame(master=self)
		localeEntry = self.localeEntry = ttk.Entry(hbox, width=15)
		ttk.Label(master=hbox, text="    ").pack(side="left")
		ttk.Label(master=hbox, text="Sort Locale").pack(side="left")
		localeEntry.pack(side="left", expand=True, fill="x")
		hbox.pack(side="top", expand=True, fill="both")
		###

	def updateSortStates(self, sort: bool) -> None:
		state = tk.NORMAL if sort else tk.DISABLED
		self.sortKeyCombo.configure(state=state)
		# self.encodingHBox.configure(state=state) # unknown option "-state"
		# self.localeHBox.configure(state=state) # unknown option "-state"

	def onSortCheckClicked(self) -> None:
		sort = bool(self.sortCheckVar.get())
		self.updateSortStates(sort)

	def updateWidgets(self) -> None:
		convertOptions = self.ui.convertOptions
		sort = bool(convertOptions.get("sort", False))
		self.sortCheckVar.set(int(sort))
		self.updateSortStates(sort)

		sortKeyName = convertOptions.get("sortKeyName")
		if sortKeyName:
			sortKeyName, _, localeName = sortKeyName.partition(":")
			if sortKeyName:
				self.sortKeyVar.set(sortKeyDescByName[sortKeyName])
			self.localeEntry.delete(0, "end")
			self.localeEntry.insert(0, localeName)

		if "sortEncoding" in convertOptions:
			self.encodingCheckVar.set(1)
			self.encodingEntry.delete(0, "end")
			self.encodingEntry.insert(0, convertOptions["sortEncoding"])

	def applyChanges(self) -> None:
		convertOptions = self.ui.convertOptions
		sort = int(self.sortCheckVar.get())
		if not sort:
			for param in ("sort", "sortKeyName", "sortEncoding"):
				if param in convertOptions:
					del convertOptions[param]
			return

		sortKeyDesc = self.sortKeyVar.get()
		sortKeyName = sortKeyNameByDesc[sortKeyDesc]
		sortLocale = self.localeEntry.get()
		if sortLocale:
			sortKeyName = f"{sortKeyName}:{sortLocale}"

		convertOptions["sort"] = True
		convertOptions["sortKeyName"] = sortKeyName
		if self.encodingCheckVar.get():
			convertOptions["sortEncoding"] = self.encodingEntry.get()


class GeneralOptionsDialog(tk.Toplevel):
	def __init__(
		self,
		ui: UI,
		master: tk.Widget | None = None,
	) -> None:
		self.ui = ui
		tk.Toplevel.__init__(self, master=master)
		self.resizable(width=True, height=True)
		self.title("General Options")
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())
		####
		padx = 0
		pady = 0
		##
		self.sortOptionsBox = SortOptionsBox(ui, master=self)
		self.sortOptionsBox.pack(side="top", pady=pady, expand=True, fill="both")
		##
		hbox = ttk.Frame(self)
		self.sqliteCheckVar = tk.IntVar()
		self.sqliteCheck = ttk.Checkbutton(
			hbox,
			text="SQLite mode",
			variable=self.sqliteCheckVar,
		)
		self.sqliteCheck.pack(side="left", padx=padx, expand=True, fill="x")
		hbox.pack(side="top", pady=pady, expand=True, fill="both")
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
		self.configCheckVars: dict[str, tk.IntVar] = {}
		for param in self.configParams:
			# hbox = ttk.Frame(self)
			comment = configDefDict[param].comment
			comment = comment.split("\n")[0]
			checkVar = tk.IntVar()
			checkButton = ttk.Checkbutton(
				self,
				text=comment,
				variable=checkVar,
			)
			self.configCheckVars[param] = checkVar
			checkButton.pack(side="top", padx=padx, expand=True, fill="both")
			# hbox.pack(side="top", pady=pady)

		###
		buttonBox = ttk.Frame(self)
		okButton = newButton(
			buttonBox,
			text="  OK  ",
			command=self.okClicked,
		)
		okButton.pack(side="right")
		buttonBox.pack(fill="x")
		##
		self.updateWidgets()

	def getSQLite(self) -> bool:
		convertOptions = self.ui.convertOptions
		sqlite = convertOptions.get("sqlite")
		if sqlite is not None:
			return sqlite
		return self.ui.config.get("auto_sqlite", True)

	def updateWidgets(self) -> None:
		config = self.ui.config
		self.sortOptionsBox.updateWidgets()
		self.sqliteCheck.configure(state=tk.NORMAL if self.getSQLite() else tk.DISABLED)
		for param, checkVar in self.configCheckVars.items():
			default = self.configParams[param]
			checkVar.set(config.get(param, default))

	def applyChanges(self) -> None:
		# print("applyChanges")
		self.sortOptionsBox.applyChanges()

		convertOptions = self.ui.convertOptions
		config = self.ui.config

		convertOptions["sqlite"] = bool(self.sqliteCheckVar.get())

		for param, checkVar in self.configCheckVars.items():
			config[param] = bool(checkVar.get())

	def okClicked(self) -> None:
		self.applyChanges()
		self.destroy()


class PreConvertInfoDialog(tk.Toplevel):
	def __init__(
		self,
		info: dict[str, Any],
		okFunc: Callable[[dict[str, Any]]],
		master: tk.Widget,
	) -> None:
		tk.Toplevel.__init__(self, master=master)
		self.resizable(width=True, height=True)
		self.title("Set Info / Metedata")
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())

		self.info = info
		self.okFunc = okFunc

		mainFrame = self.frame = ttk.Frame(master=self)

		frame = ttk.Frame(master=mainFrame)
		ttk.Label(
			text="Glossary Name",
			master=frame,
		).pack(side="left", expand=False)
		nameEntry = ttk.Entry(master=frame, width=50)
		nameEntry.pack(side="left", fill="x", expand=True)
		nameEntry.insert(0, info.get("name", ""))
		self.nameEntry = nameEntry
		frame.pack(side="top", expand=True, fill="both")

		frame = ttk.Frame(master=mainFrame)
		ttk.Label(
			text="Source Language",
			master=frame,
		).pack(side="left", expand=False)
		sourceLangEntry = ttk.Entry(master=frame)
		sourceLangEntry.pack(side="right", fill="x", expand=True)
		sourceLangEntry.insert(0, info.get("sourceLang", ""))
		self.sourceLangEntry = sourceLangEntry
		frame.pack(side="top", expand=True, fill="both")

		frame = ttk.Frame(master=mainFrame)
		ttk.Label(
			text="Target Language",
			master=frame,
		).pack(side="left", expand=False)
		targetLangEntry = ttk.Entry(master=frame)
		targetLangEntry.pack(side="right", fill="x", expand=True)
		targetLangEntry.insert(0, info.get("targetLang", ""))
		self.targetLangEntry = targetLangEntry
		frame.pack(side="top", expand=True, fill="both")

		mainFrame.pack(fill="both", expand=True)

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

		px, py, pw, ph = decodeGeometry(master.winfo_toplevel().geometry())
		self.geometry(
			encodeLocation(
				px + pw // 2 - 200,
				py + ph // 2 - 100,
			)
		)

	def okClicked(self) -> None:
		name = self.nameEntry.get()
		if name:
			self.info["name"] = name
		sourceLang = self.sourceLangEntry.get()
		if sourceLang:
			self.info["sourceLang"] = sourceLang
		targetLang = self.targetLangEntry.get()
		if targetLang:
			self.info["targetLang"] = targetLang
		self.okFunc(self.info)
		self.destroy()


class VerticalNotebook(ttk.Frame):
	def __init__(
		self,
		parent: tk.Widget,
		font: Font,
		**kwargs: Any,
	) -> None:
		ttk.Frame.__init__(self, parent, **kwargs)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(2, weight=1)
		# scrollable tabs
		self._listbox = tk.Listbox(
			self,
			width=1,
			highlightthickness=0,
			relief="raised",
			justify="center",
			font=font,
		)
		self._listbox.configure()

		# list of widgets associated with the tabs
		self._tabs = []
		self._current_tab = None  # currently displayed tab

		self._listbox.grid(row=0, column=1, sticky="ns")
		# binding to display the selected tab
		self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
		self._maxWidth = 0

	# add tab
	def add(self, widget: tk.Widget, text: str) -> None:
		self._listbox.insert("end", text)
		# resize listbox to be large enough to show all tab labels
		self._maxWidth = max(self._maxWidth, len(text))
		self._listbox.configure(
			width=self._maxWidth + 2,
		)
		index = len(self._tabs)
		self._tabs.append(widget)
		if self._current_tab is None:
			self.switch_tab(index)

	def switch_tab(self, index: int) -> None:
		self._show_tab_index(index)
		self._listbox.selection_clear(0, "end")
		self._listbox.selection_set(index)
		self._listbox.see(index)

	def _show_tab_index(self, index: int) -> None:
		widget = self._tabs[index]
		if self._current_tab is not None:
			self._current_tab.grid_remove()
		self._current_tab = widget
		widget.grid(in_=self, column=2, row=0, sticky="ewns")

	def _on_listbox_select(self, _event: tk.Event | None = None) -> None:
		selection = self._listbox.curselection()
		if not selection:
			return
		index = selection[0]
		if index >= len(self._tabs):
			print(f"{index=}")
			return
		self._show_tab_index(index)


class UI(tk.Frame, UIBase):
	fcd_dir_save_path = join(confDir, "ui-tk-fcd-dir")

	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		rootWin = self.rootWin = tk.Tk(
			# baseName="PyGlossary",  # no effect
			className="PyGlossary",
			# ^ capitalized as Pyglossary regardless of case or spaces
		)
		# a hack that hides the window until we move it to the center of screen
		if os.sep == "\\":  # Windows
			rootWin.attributes("-alpha", 0.0)
		else:  # Linux
			rootWin.withdraw()
		tk.Frame.__init__(self, rootWin)
		UIBase.__init__(self)
		rootWin.title("PyGlossary (Tkinter)")
		rootWin.resizable(True, False)
		# self.progressbarEnable = progressbar
		########
		set_window_icon(rootWin)
		rootWin.bind("<Escape>", lambda _e: rootWin.quit())
		#########
		# Linux: ('clam', 'alt', 'default', 'classic')
		# Windows: ('winnative', 'clam', 'alt', 'default', 'classic', 'vista',
		# 'xpnative')
		style = ttk.Style()
		style.configure("TButton", borderwidth=3)
		# style.theme_use("default")
		# there is no tk.Style()
		########
		self.pack(fill="x")
		# rootWin.bind("<Configure>", self.resized)
		#######################
		defaultFont = tkFont.nametofont("TkDefaultFont")
		if sysName in {"linux", "freebsd"}:
			defaultFont.configure(size=int(defaultFont.cget("size") * 1.4))
		####
		self.bigFont = defaultFont.copy()
		self.bigFont.configure(size=int(defaultFont.cget("size") * 1.6))
		# self.biggerFont = defaultFont.copy()
		# self.biggerFont.configure(size=int(defaultFont.cget("size") * 1.8))
		####
		style.configure(
			"Treeview",
			rowheight=int(defaultFont.metrics("linespace") * 1.5),
		)
		######################
		self.progressbar = progressbar
		self.infoOverride = {}
		self.convertOptions = {}
		self.pathI = ""
		self.pathO = ""
		fcd_dir = join(homeDir, "Desktop")
		if isfile(self.fcd_dir_save_path):
			try:
				with open(self.fcd_dir_save_path, encoding="utf-8") as fp:
					fcd_dir = fp.read().strip("\n")
			except Exception:
				log.exception("")
		self.fcd_dir = fcd_dir
		######################
		notebook = ttk.Notebook(self)
		convertFrame = ttk.Frame(notebook, height=200)
		###################
		row = 0
		ttk.Label(convertFrame, text="Input File: ").grid(
			row=row,
			column=0,
			sticky=tk.W,
			padx=5,
		)
		##
		entry = ttk.Entry(convertFrame)
		entry.grid(
			row=row,
			column=1,
			columnspan=2,
			sticky=tk.W + tk.E,
			padx=0,
		)
		entry.bind_all("<KeyPress>", self.anyEntryChanged)
		self.entryInputConvert = entry
		##
		button = newButton(
			convertFrame,
			text="Browse",
			command=self.browseInputConvert,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.grid(
			row=row,
			column=3,
			sticky=tk.W + tk.E,
			padx=5,
		)
		######################
		row += 1
		ttk.Label(convertFrame, text="Input Format: ").grid(
			row=row,
			column=0,
			sticky=tk.W,
			padx=5,
		)
		##
		self.formatButtonInputConvert = FormatButton(
			rootWin,
			master=convertFrame,
			descList=readDesc,
			dialogTitle="Select Input Format",
			onChange=self.inputFormatChanged,
		)
		self.formatButtonInputConvert.grid(
			row=row,
			column=1,
			columnspan=2,
			sticky=tk.W,
			padx=0,
		)
		##
		self.readOptions: dict[str, Any] = {}
		self.writeOptions: dict[str, Any] = {}
		######################
		row += 1
		ttk.Label(convertFrame).grid(
			row=row,
			column=0,
			sticky=tk.W,
		)
		######################
		row += 1
		ttk.Label(convertFrame, text="Output File: ").grid(
			row=row,
			column=0,
			sticky=tk.W,
			padx=5,
		)
		##
		entry = ttk.Entry(convertFrame)
		entry.grid(
			row=row,
			column=1,
			columnspan=2,
			sticky=tk.W + tk.E,
			padx=0,
		)
		entry.bind_all("<KeyPress>", self.anyEntryChanged)
		self.entryOutputConvert = entry
		##
		newButton(
			convertFrame,
			text="Browse",
			command=self.browseOutputConvert,
			# bg="#f0f000",
			# activebackground="#f6f622",
		).grid(
			row=row,
			column=3,
			sticky=tk.W + tk.E,
			padx=5,
		)
		###################
		row += 1
		ttk.Label(convertFrame, text="Output Format: ").grid(
			row=row,
			column=0,
			sticky=tk.W,
			padx=5,
		)
		##
		self.formatButtonOutputConvert = FormatButton(
			rootWin,
			master=convertFrame,
			descList=writeDesc,
			dialogTitle="Select Output Format",
			onChange=self.outputFormatChanged,
		)
		self.formatButtonOutputConvert.grid(
			row=row,
			column=1,
			columnspan=2,
			sticky=tk.W,
			padx=0,
		)
		###################
		row += 1
		optionsMenu = tk.Menu(tearoff=False)
		optionsMenu.add_command(
			label="Read Options",
			command=self.readOptionsClicked,
			font=defaultFont,
		)
		optionsMenu.add_command(
			label="Write Options",
			command=self.writeOptionsClicked,
			font=defaultFont,
		)
		optionsMenu.add_command(
			label="General Options",
			command=self.generalOptionsClicked,
			font=defaultFont,
		)
		optionsMenu.add_command(
			label="Info / Metadata",
			command=self.infoOptionClicked,
			font=defaultFont,
		)
		optionsButton = ttk.Menubutton(
			convertFrame,
			text="Options    ",
			menu=optionsMenu,
		)
		optionsButton.grid(
			row=row,
			column=1,
			columnspan=1,
			sticky=tk.E + tk.S,
			padx=5,
			pady=5,
		)
		newButton(
			convertFrame,
			text="Convert",
			command=self.convert,
			# background="#00e000",
			# activebackground="#22f022",
			# borderwidth=7,
			# font=self.biggerFont,
			# padx=5,
			# pady=5,
		).grid(
			row=row,
			column=2,
			columnspan=3,
			sticky=tk.W + tk.E + tk.S,
			padx=5,
			pady=5,
		)
		# print(f"row number for Convert button: {row}")
		#################
		row += 1
		console = tk.Text(
			convertFrame,
			height=15,
			background="#000",
			foreground="#fff",
		)
		console.bind("<Key>", self.consoleKeyPress)
		# self.consoleH = 15
		# sbar = Tix.Scrollbar(
		# 	convertFrame,
		# 	orien=Tix.VERTICAL,
		# 	command=console.yview
		# )
		# sbar.grid (row=row, column=1)
		# console["yscrollcommand"] = sbar.set
		console.grid(
			row=row,
			column=0,
			columnspan=4,
			sticky=tk.W + tk.E,
			padx=5,
			pady=0,
		)
		log.addHandler(
			TkTextLogHandler(console),
		)
		console.insert("end", "Console:\n")
		####
		self.console = console
		##################
		aboutFrame = ttk.Frame(notebook)

		versionFrame = ttk.Frame(aboutFrame, borderwidth=5)
		newLabelWithImage(versionFrame, file=logo).pack(
			side="left", fill="both", expand=False
		)
		ttk.Label(versionFrame, text=f"PyGlossary\nVersion {getVersion()}").pack(
			side="left", fill="both", expand=False
		)
		versionFrame.pack(side="top", fill="x")
		##

		aboutNotebook = VerticalNotebook(aboutFrame, font=self.bigFont)

		aboutAboutFrame = ttk.Frame()
		newReadOnlyText(
			aboutAboutFrame,
			text=f"{aboutText}\nHome page: {homePage}",
			font=("DejaVu Sans", 11, ""),
		).pack(fill="both", expand=True)
		aboutAboutFrame.pack(side="top", fill="x")
		aboutNotebook.add(aboutAboutFrame, "About")

		authorsFrame = ttk.Frame()
		authorsText = "\n".join(authors).replace("\t", "    ")
		newReadOnlyText(
			authorsFrame,
			text=authorsText,
			font=("DejaVu Sans", 11, ""),
		).pack(fill="both", expand=True)
		aboutNotebook.add(authorsFrame, "Authors")

		licenseFrame = ttk.Frame()
		newReadOnlyText(
			licenseFrame,
			text=licenseText,
			font=("DejaVu Sans", 11, ""),
		).pack(fill="both", expand=True)
		aboutNotebook.add(licenseFrame, "License")

		aboutNotebook.pack(fill="both", expand=True)
		# aboutNotebook.show_tab_index(0)

		statusBarFrame = self.statusBarFrame = ttk.Frame(convertFrame)
		statusBarFrame.grid(
			row=row + 1,
			column=0,
			columnspan=4,
			sticky=tk.W + tk.E,
			padx=5,
			pady=0,
		)
		clearB = newButton(
			statusBarFrame,
			text="Clear",
			command=self.console_clear,
			# how to set borderwidth using style?
			# bg="black",
			# fg="#ffff00",
			# activebackground="#333333",
			# activeforeground="#ffff00",
			# borderwidth=3,
			# height=2,
		)
		clearB.pack(side="left")
		####
		ttk.Label(statusBarFrame, text="Verbosity").pack(side="left")
		##
		comboVar = tk.StringVar()
		verbosity = log.getVerbosity()
		combo = ttk.OptionMenu(
			statusBarFrame,
			comboVar,
			f"{verbosity} - {log.levelNamesCap[verbosity]}",
			"0 - Critical",
			"1 - Error",
			"2 - Warning",
			"3 - Info",
			"4 - Debug",
			"5 - Trace",
			"6 - All",
		)

		comboVar.trace_add("write", self.verbosityChanged)
		combo.pack(side="left")
		self.verbosityCombo = comboVar

		notebook.add(convertFrame, text="Convert", underline=-1)
		notebook.add(aboutFrame, text="About", underline=-1)

		# convertFrame.pack(fill="x")
		# convertFrame.grid(sticky=tk.W + tk.E + tk.N + tk.S)

		######################
		for column, weight in enumerate([1, 30, 20, 1]):
			tk.Grid.columnconfigure(convertFrame, column, weight=weight)
		for row, weight in enumerate([50, 50, 1, 50, 50, 1, 50]):
			tk.Grid.rowconfigure(convertFrame, row, weight=weight)
		# _________________________________________________________________ #

		notebook.pack(fill="both", expand=True)

	def openDialog(self, dialog: tk.Toplevel) -> None:
		# x, y, w, h = decodeGeometry(dialog.geometry())
		# w and h are rough estimated width and height of `dialog`
		px, py, pw, ph = decodeGeometry(self.winfo_toplevel().geometry())
		dialog.update_idletasks()
		width = dialog.winfo_width() + 400
		height = dialog.winfo_height()
		dialog.geometry(
			f"{width}x{height}"
			+ encodeLocation(
				px + pw // 2 - width // 2,
				py + ph // 2 - height // 2,
			),
		)
		dialog.focus()

	def readOptionsClicked(self) -> None:
		formatDesc = self.formatButtonInputConvert.get()
		if not formatDesc:
			return

		def okFunc(values: dict[str, Any]) -> None:
			self.readOptions = values

		dialog = FormatOptionsDialog(
			formatDesc,
			"Read",
			self.readOptions,
			okFunc,
			master=self,
		)
		self.openDialog(dialog)

	def writeOptionsClicked(self) -> None:
		formatDesc = self.formatButtonOutputConvert.get()
		if not formatDesc:
			return

		def okFunc(values: dict[str, Any]) -> None:
			self.writeOptions = values

		dialog = FormatOptionsDialog(
			formatDesc=formatDesc,
			kind="Write",
			values=self.writeOptions,
			okFunc=okFunc,
			master=self,
		)
		self.openDialog(dialog)

	def generalOptionsClicked(self) -> None:
		dialog = GeneralOptionsDialog(self, master=self.winfo_toplevel())
		self.openDialog(dialog)

	def infoOptionClicked(self) -> None:
		def okFunc(info: dict[str, Any]) -> None:
			self.infoOverride = info

		dialog = PreConvertInfoDialog(
			info=self.infoOverride,
			okFunc=okFunc,
			master=self,
		)
		dialog.focus()

	def textSelectAll(self, tktext: tk.Text) -> None:
		tktext.tag_add(tk.SEL, "1.0", tk.END)
		tktext.mark_set(tk.INSERT, "1.0")
		tktext.see(tk.INSERT)

	def consoleKeyPress(self, event: tk.Event) -> str | None:
		# print(e.state, e.keysym)
		if event.state > 0:
			if event.keysym == "c":
				return None
			if event.keysym == "a":
				self.textSelectAll(self.console)
				return "break"
		if event.keysym == "Escape":
			return None
		return "break"

	def verbosityChanged(self, _index: str, _value: str, _op: str) -> None:
		log.setVerbosity(
			int(self.verbosityCombo.get()[0]),
		)

	# def resized(self, event):
	# 	self.rootWin.winfo_height() - self.winfo_height()
	# 	log.debug(dh, self.consoleH)
	# 	if dh > 20:
	# 		self.consoleH += 1
	# 		self.console["height"] = self.consoleH
	# 		self.console["width"] = int(self.console["width"]) + 1
	# 		self.console.grid()
	# 	for x in dir(self):
	# 		if "info" in x:
	# 			log.debug(x)

	def inputFormatChangedAuto(self) -> None:
		self.inputFormatChanged(self.formatButtonInputConvert.get())

	def outputFormatChangedAuto(self) -> None:
		self.outputFormatChanged(self.formatButtonOutputConvert.get())

	def inputFormatChanged(self, formatDesc: str) -> None:
		if not formatDesc:
			return
		self.readOptions.clear()  # reset the options, DO NOT re-assign

	def outputFormatChanged(self, formatDesc: str) -> None:
		if not formatDesc:
			return

		formatName = pluginByDesc[formatDesc].name
		plugin = Glossary.plugins.get(formatName)
		if not plugin:
			log.error(f"plugin {formatName} not found")
			return

		self.writeOptions.clear()  # reset the options, DO NOT re-assign

		pathI = self.entryInputConvert.get()
		if (
			pathI
			and not self.entryOutputConvert.get()
			and self.formatButtonInputConvert.get()
			and plugin.extensionCreate
		):
			pathNoExt, _ext = splitext(pathI)
			self.entryOutputConvert.insert(
				0,
				pathNoExt + plugin.extensionCreate,
			)

	def anyEntryChanged(self, _event: tk.Event | None = None) -> None:
		self.inputEntryChanged()
		self.outputEntryChanged()

	def inputEntryChanged(self, _event: tk.Event | None = None) -> None:
		# char = event.keysym
		pathI = self.entryInputConvert.get()
		if self.pathI == pathI:
			return

		if pathI.startswith("file://"):
			pathI = urlToPath(pathI)
			self.entryInputConvert.delete(0, "end")
			self.entryInputConvert.insert(0, pathI)
		if self.config["ui_autoSetFormat"]:
			formatDesc = self.formatButtonInputConvert.get()
			if not formatDesc:
				try:
					inputArgs = Glossary.detectInputFormat(pathI)
				except Error:
					pass
				else:
					plugin = Glossary.plugins.get(inputArgs.formatName)
					if plugin:
						self.formatButtonInputConvert.setValue(plugin.description)
						self.inputFormatChangedAuto()
		self.pathI = pathI

	def outputEntryChanged(self, _event: tk.Event | None = None) -> None:
		pathO = self.entryOutputConvert.get()
		if self.pathO == pathO:
			return

		if pathO.startswith("file://"):
			pathO = urlToPath(pathO)
			self.entryOutputConvert.delete(0, "end")
			self.entryOutputConvert.insert(0, pathO)
		if self.config["ui_autoSetFormat"]:
			formatDesc = self.formatButtonOutputConvert.get()
			if not formatDesc:
				try:
					outputArgs = Glossary.detectOutputFormat(
						filename=pathO,
						inputFilename=self.entryInputConvert.get(),
					)
				except Error:
					pass
				else:
					self.formatButtonOutputConvert.setValue(
						Glossary.plugins[outputArgs.formatName].description,
					)
					self.outputFormatChangedAuto()
		self.pathO = pathO

	def save_fcd_dir(self) -> None:
		if not self.fcd_dir:
			return
		with open(self.fcd_dir_save_path, mode="w", encoding="utf-8") as fp:
			fp.write(self.fcd_dir)

	def browseInputConvert(self) -> None:
		path = filedialog.askopenfilename(initialdir=self.fcd_dir)
		if path:
			self.entryInputConvert.delete(0, "end")
			self.entryInputConvert.insert(0, path)
			self.inputEntryChanged()
			self.fcd_dir = os.path.dirname(path)
			self.save_fcd_dir()

	def browseOutputConvert(self) -> None:
		path = filedialog.asksaveasfilename()
		if path:
			self.entryOutputConvert.delete(0, "end")
			self.entryOutputConvert.insert(0, path)
			self.outputEntryChanged()
			self.fcd_dir = os.path.dirname(path)
			self.save_fcd_dir()

	def convert(self) -> None:
		inPath = self.entryInputConvert.get()
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormatDesc = self.formatButtonInputConvert.get()
		# if not inFormatDesc:
		# 	log.critical("Input format is empty!");return
		inFormat = pluginByDesc[inFormatDesc].name if inFormatDesc else ""

		outPath = self.entryOutputConvert.get()
		if not outPath:
			log.critical("Output file path is empty!")
			return
		outFormatDesc = self.formatButtonOutputConvert.get()
		if not outFormatDesc:
			log.critical("Output format is empty!")
			return
		outFormat = pluginByDesc[outFormatDesc].name

		log.debug(f"config: {self.config}")

		glos = Glossary(ui=self)
		glos.config = self.config
		glos.progressbar = self.progressbar

		for attr, value in self._glossarySetAttrs.items():
			setattr(glos, attr, value)

		if self.infoOverride:
			log.info(f"infoOverride = {self.infoOverride}")

		if self.convertOptions:
			log.info(f"convertOptions: {self.convertOptions}")

		try:
			glos.convert(
				ConvertArgs(
					inPath,
					inputFormat=inFormat,
					outputFilename=outPath,
					outputFormat=outFormat,
					readOptions=self.readOptions,
					writeOptions=self.writeOptions,
					infoOverride=self.infoOverride or None,
					**self.convertOptions,
				),
			)
		except Error as e:
			log.critical(str(e))
			glos.cleanup()
			return

		# self.status("Convert finished")

	def run(  # noqa: PLR0913
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		config: ConfigType | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> None:
		config = config or {}
		self.config = config

		if inputFilename:
			self.entryInputConvert.insert(0, abspath2(inputFilename))
			self.inputEntryChanged()
		if outputFilename:
			self.entryOutputConvert.insert(0, abspath2(outputFilename))
			self.outputEntryChanged()

		if inputFormat and inputFormat not in Glossary.readFormats:
			log.error(f"invalid {inputFormat=}")
			inputFormat = ""

		if outputFormat and outputFormat not in Glossary.writeFormats:
			log.error(f"invalid {outputFormat=}")
			outputFormat = ""

		if inputFormat:
			self.formatButtonInputConvert.setValue(
				Glossary.plugins[inputFormat].description,
			)
			self.inputFormatChangedAuto()
		if outputFormat:
			self.formatButtonOutputConvert.setValue(
				Glossary.plugins[outputFormat].description,
			)
			self.outputFormatChangedAuto()

		if reverse:
			log.error("Tkinter interface does not support Reverse feature")

		pbar = ProgressBar(
			self.statusBarFrame,
			min_=0,
			max_=100,
			width=700,
			height=28,
			appearance="sunken",
			fillColor=config.get("tk.progressbar.color.fill", "blue"),
			background=config.get("tk.progressbar.color.background", "gray"),
			labelColor=config.get("tk.progressbar.color.text", "yellow"),
			labelFont=config.get("tk.progressbar.font", "Sans"),
		)
		pbar.pack(side="left", fill="x", expand=True, padx=10)
		self.pbar = pbar
		pbar.pack(fill="x")
		self.progressTitle = ""
		# _________________________________________________________________ #

		centerWindow(self.rootWin)
		# show the window
		if os.sep == "\\":  # Windows
			self.rootWin.attributes("-alpha", 1.0)
		else:  # Linux
			self.rootWin.deiconify()

		# must be before setting self.readOptions and self.writeOptions
		self.anyEntryChanged()

		if readOptions:
			self.readOptions = readOptions

		if writeOptions:
			self.writeOptions = writeOptions

		self.convertOptions: dict[str, Any] = convertOptions or {}
		if convertOptions:
			log.info(f"Using {convertOptions=}")

		self._glossarySetAttrs = glossarySetAttrs or {}

		# inputFilename and readOptions are for DB Editor
		# which is not implemented
		self.mainloop()

	def progressInit(self, title: str) -> None:
		self.progressTitle = title

	def progress(self, ratio: float, text: str = "") -> None:
		if not text:
			text = "%" + str(int(ratio * 100))
		text += " - " + self.progressTitle
		self.pbar.updateProgress(ratio * 100, None, text)
		# self.pbar.value = ratio * 100
		# self.pbar.update()
		self.rootWin.update()

	def console_clear(self, _event: tk.Event | None = None) -> None:
		self.console.delete("1.0", "end")
		self.console.insert("end", "Console:\n")

	# def reverseBrowseInput(self):
	# 	pass

	# def reverseBrowseOutput(self):
	# 	pass

	# def reverseLoad(self):
	# 	pass
