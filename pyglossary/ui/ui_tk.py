# -*- coding: utf-8 -*-
# mypy: ignore-errors
# ui_tk.py
#
# Copyright © 2009-2021 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
import os
import tkinter as tk
import traceback
from os.path import abspath, isfile, join, splitext
from tkinter import filedialog, ttk
from tkinter import font as tkFont
from typing import TYPE_CHECKING, Any, Literal

from pyglossary import core
from pyglossary.core import confDir, homeDir
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.text_utils import urlToPath

from .base import (
	UIBase,
	aboutText,
	authors,
	licenseText,
	logo,
)
from .version import getVersion

if TYPE_CHECKING:
	from collections.abc import Callable

log = logging.getLogger("pyglossary")

pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}
readDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canRead
]
writeDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canWrite
]


def set_window_icon(window):
	window.iconphoto(
		True,
		tk.PhotoImage(file=logo),
	)


def decodeGeometry(gs):
	"""
	Example for gs: "253x252+30+684"
	returns (x, y, w, h).
	"""
	p = gs.split("+")
	w, h = p[0].split("x")
	return (int(p[1]), int(p[2]), int(w), int(h))


def encodeGeometry(x, y, w, h):
	return f"{w}x{h}+{x}+{y}"


def encodeLocation(x, y):
	return f"+{x}+{y}"


def centerWindow(win):
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


def newButton(*args, **kwargs):
	button = ttk.Button(*args, **kwargs)

	def onEnter(_event):
		button.invoke()

	button.bind("<Return>", onEnter)
	button.bind("<KP_Enter>", onEnter)
	return button


def newLabelWithImage(parent, file=""):
	image = tk.PhotoImage(file=file)
	label = ttk.Label(parent, image=image)
	label.image = image  # keep a reference!
	return label


def newReadOnlyText(
	parent,
	text="",
	borderwidth=10,
	font=None,
):
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
	widget.configure(state="disabled")

	return widget


class TkTextLogHandler(logging.Handler):
	def __init__(self, tktext) -> None:
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

	def emit(self, record):
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
def CallWrapper__call__(self, *args):
	"""Apply first function SUBST to arguments, than FUNC."""
	if self.subst:
		args = self.subst(*args)
	try:
		return self.func(*args)
	except Exception:
		log.exception("Exception in Tkinter callback:")


tk.CallWrapper.__call__ = CallWrapper__call__


class ProgressBar(ttk.Frame):

	"""
	Comes from John Grayson's book "Python and Tkinter programming"
	Edited by Saeed Rasooli.
	"""

	def __init__(  # noqa: PLR0913
		self,
		rootWin=None,
		orientation="horizontal",
		min_=0,
		max_=100,
		width=100,
		height=18,
		appearance="sunken",
		fillColor="blue",
		background="gray",
		labelColor="yellow",
		labelFont="Verdana",
		labelFormat="%d%%",
		value=0,
	) -> None:
		# preserve various values
		self.rootWin = rootWin
		self.orientation = orientation
		self.min = min_
		self.max = max_
		self.width = width
		self.height = height
		self.fillColor = fillColor
		self.labelFont = labelFont
		self.labelColor = labelColor
		self.background = background
		self.labelFormat = labelFormat
		self.value = value
		ttk.Frame.__init__(self, rootWin, relief=appearance)
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
			anchor="c",
			fill=labelColor,
			font=self.labelFont,
		)
		self.update()
		self.bind("<Configure>", self.update)
		self.canvas.pack(side="top", fill="x", expand="no")

	def updateProgress(self, value, max_=None, text=""):
		if max_:
			self.max = max_
		self.value = value
		self.update(None, text)

	def update(self, event=None, labelText=""):  # noqa: ARG002
		# Trim the values to be between min and max
		value = self.value
		value = min(value, self.max)
		value = max(value, self.min)
		# Adjust the rectangle
		width = int(self.winfo_width())
		# width = self.width
		ratio = float(value) / self.max
		if self.orientation == "horizontal":
			self.canvas.coords(
				self.scale,
				0,
				0,
				width * ratio,
				self.height,
			)
		else:
			self.canvas.coords(
				self.scale,
				0,
				self.height * (1 - ratio),
				width,
				self.height,
			)
		# Now update the colors
		self.canvas.itemconfig(self.scale, fill=self.fillColor)
		self.canvas.itemconfig(self.label, fill=self.labelColor)
		# And update the label
		if not labelText:
			labelText = self.labelFormat % int(ratio * 100)
		self.canvas.itemconfig(self.label, text=labelText)
		# FIXME: resizing window causes problem in progressbar
		# self.canvas.move(self.label, width/2, self.height/2)
		# self.canvas.scale(self.label, 0, 0, float(width)/self.width, 1)
		self.canvas.update_idletasks()


class FormatDialog(tk.Toplevel):
	def __init__(  # noqa: PLR0913
		self,
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
		label = ttk.Label(master=entryBox, text="Search: ")
		label.pack(side="left")
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

	def setActiveRow(self, desc):
		self.treev.selection_set(desc)
		self.treev.see(desc)

	def updateTree(self):
		treev = self.treev
		current = treev.get_children()
		if current:
			treev.delete(*current)
		for desc in self.items:
			treev.insert("", "end", values=[desc], iid=desc)
			# iid should be rowId
		if self.activeDesc in self.items:
			self.setActiveRow(self.activeDesc)

	def onEntryKeyRelease(self, _event):
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

	def onTreeDoubleClick(self, _event):
		self.okClicked()

	def cancelClicked(self):
		self.destroy()

	def onReturnPress(self, _event):
		self.okClicked()

	def onDownPress(self, _event):
		treev = self.treev
		selection = treev.selection()
		if selection:
			nextDesc = treev.next(selection[0])
			if nextDesc:
				self.setActiveRow(nextDesc)
		elif self.items:
			self.setActiveRow(self.items[0])
		treev.focus()

	def onUpPress(self, _event):
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

	def onKeyPress(self, event):
		print(f"FormatDialog: onKeyPress: {event}")

	def okClicked(self):
		treev = self.treev
		selectedList = treev.selection()
		desc = selectedList[0] if selectedList else ""
		self.onOk(desc)
		self.destroy()


class FormatButton(ttk.Button):
	noneLabel = "[Select Format]"

	def __init__(
		self,
		descList: list[str],
		dialogTitle: str,
		onChange: Callable,
		master=None,
	) -> None:
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

	def onEnter(self, _event=None):
		self.invoke()

	def onChange(self, desc):
		self.setValue(desc)
		self._onChange(desc)

	def get(self):
		return self.activeDesc

	def setValue(self, desc):
		if desc:
			self.var.set(desc)
		else:
			self.var.set(self.noneLabel)
		self.activeDesc = desc

	def onClick(self):
		dialog = FormatDialog(
			descList=self.descList,
			title=self.dialogTitle,
			onOk=self.onChange,
			button=self,
			activeDesc=self.activeDesc,
		)
		dialog.focus()


class FormatOptionsDialog(tk.Toplevel):
	commentLen = 60
	kindFormatsOptions = {
		"Read": Glossary.formatsReadOptions,
		"Write": Glossary.formatsWriteOptions,
	}

	def __init__(
		self,
		formatName,
		kind,
		values,
		master=None,  # noqa: ARG002
	) -> None:
		tk.Toplevel.__init__(self)
		# bg="#0f0" does not work
		self.resizable(width=True, height=True)
		self.title(kind + " Options")
		set_window_icon(self)
		self.bind("<Escape>", lambda _e: self.destroy())

		self.menu = None
		self.format = formatName
		self.kind = kind
		self.values = values
		self.options = list(self.kindFormatsOptions[kind][formatName])
		self.optionsProp = Glossary.plugins[formatName].optionsProp

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

	def createOptionsList(self):
		values = self.values
		self.valueCol = "#3"
		cols = [
			"Enable",  # bool
			"Name",  # str
			"Value",  # str
			"Comment",  # str
		]
		treev = self.treev = ttk.Treeview(
			master=self,
			columns=cols,
			show="headings",
		)
		for col in cols:
			treev.heading(
				col,
				text=col,
				# command=lambda c=col: sortby(treev, c, 0),
			)
			# adjust the column's width to the header string
			treev.column(
				col,
				width=tkFont.Font().measure(col.title()),
			)
		###
		treev.bind(
			"<Button-1>",
			# "<<TreeviewSelect>>", # event.x and event.y are zero
			self.treeClicked,
		)
		treev.pack(fill="x", expand=True)
		###
		for optName in self.options:
			prop = self.optionsProp[optName]
			comment = prop.longComment
			if len(comment) > self.commentLen:
				comment = comment[: self.commentLen] + "..."
			row = [
				int(optName in values),
				optName,
				str(values.get(optName, "")),
				comment,
			]
			treev.insert("", "end", values=row, iid=optName)  # iid should be rowId
			# adjust column's width if necessary to fit each value
			for col_i, valueTmp in enumerate(row):
				value = str(valueTmp)
				if col_i == 3:
					value = value.zfill(20)
					# to reserve window width, because it's hard to resize it later
				col_w = tkFont.Font().measure(value)
				if treev.column(cols[col_i], width=None) < col_w:
					treev.column(cols[col_i], width=col_w)

	def valueMenuItemCustomSelected(
		self,
		treev,
		formatName: str,
		optName: str,
		menu=None,
	):
		if menu:
			menu.destroy()
			self.menu = None

		value = treev.set(optName, self.valueCol)

		dialog = tk.Toplevel(master=treev)  # bg="#0f0" does not work
		dialog.resizable(width=True, height=True)
		dialog.title(optName)
		set_window_icon(dialog)
		dialog.bind("<Escape>", lambda _e: dialog.destroy())

		px, py, pw, ph = decodeGeometry(treev.winfo_toplevel().geometry())
		width = 300
		height = 100
		dialog.geometry(
			encodeGeometry(
				px + pw // 2 - width // 2,
				py + ph // 2 - height // 2,
				width,
				height,
			),
		)

		frame = ttk.Frame(master=dialog)

		label = ttk.Label(master=frame, text="Value for " + optName)
		label.pack()

		entry = ttk.Entry(master=frame)
		entry.insert(0, value)
		entry.pack(fill="x")

		prop = Glossary.plugins[formatName].optionsProp[optName]

		def customOkClicked(_event=None):
			rawValue = entry.get()
			if not prop.validateRaw(rawValue):
				log.error(f"invalid {prop.typ} value: {optName} = {rawValue!r}")
				return
			treev.set(optName, self.valueCol, rawValue)
			treev.set(optName, "#1", "1")  # enable it
			col_w = tkFont.Font().measure(rawValue)
			if treev.column("Value", width=None) < col_w:
				treev.column("Value", width=col_w)
			dialog.destroy()

		entry.bind("<Return>", customOkClicked)

		label = ttk.Label(master=frame)
		label.pack(fill="x")

		customOkbutton = newButton(
			frame,
			text="  OK  ",
			command=customOkClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		customOkbutton.pack(side="right")
		###
		frame.pack(fill="x")
		dialog.focus()

	def valueMenuItemSelected(self, optName, menu, value):
		treev = self.treev
		treev.set(optName, self.valueCol, value)
		treev.set(optName, "#1", "1")  # enable it
		col_w = tkFont.Font().measure(value)
		if treev.column("Value", width=None) < col_w:
			treev.column("Value", width=col_w)
		menu.destroy()
		self.menu = None

	def valueCellClicked(self, event, optName):
		if not optName:
			return
		treev = self.treev
		prop = self.optionsProp[optName]
		propValues = prop.values
		if not propValues:
			if prop.customValue:
				self.valueMenuItemCustomSelected(treev, self.format, optName, None)
			else:
				log.error(
					f"invalid option {optName}, values={propValues}"
					f", customValue={prop.customValue}",
				)
			return
		if prop.typ == "bool":
			rawValue = treev.set(optName, self.valueCol)
			if rawValue == "":  # noqa: PLC1901
				value = False
			else:
				value, isValid = prop.evaluate(rawValue)
				if not isValid:
					log.error(f"invalid {optName} = {rawValue!r}")
					value = False
			treev.set(optName, self.valueCol, str(not value))
			treev.set(optName, "#1", "1")  # enable it
			return
		menu = tk.Menu(
			master=treev,
			title=optName,
			tearoff=False,
		)
		self.menu = menu  # to destroy it later
		if prop.customValue:
			menu.add_command(
				label="[Custom Value]",
				command=lambda: self.valueMenuItemCustomSelected(
					treev,
					self.format,
					optName,
					menu,
				),
			)
		groupedValues = None
		if len(propValues) > 10:
			groupedValues = prop.groupValues()
		maxItemW = 0

		def valueMenuItemSelectedCommand(value):
			def callback():
				self.valueMenuItemSelected(optName, menu, value)

			return callback

		if groupedValues:
			for groupName, subValues in groupedValues.items():
				if subValues is None:
					menu.add_command(
						label=str(value),
						command=valueMenuItemSelectedCommand(value),
					)
					maxItemW = max(maxItemW, tkFont.Font().measure(str(value)))
				else:
					subMenu = tk.Menu(tearoff=False)
					for subValue in subValues:
						subMenu.add_command(
							label=str(subValue),
							command=valueMenuItemSelectedCommand(subValue),
						)
					menu.add_cascade(label=groupName, menu=subMenu)
					maxItemW = max(maxItemW, tkFont.Font().measure(groupName))
		else:
			for valueTmp in propValues:
				value = str(valueTmp)
				menu.add_command(
					label=value,
					command=valueMenuItemSelectedCommand(value),
				)

		def close():
			menu.destroy()
			self.menu = None

		menu.add_command(
			label="[Close]",
			command=close,
		)
		try:
			menu.tk_popup(
				event.x_root,
				event.y_root,
			)
			# do not pass the third argument (entry), so that the menu
			# appears where the pointer is on its top-left corner
		finally:
			# make sure to release the grab (Tk 8.0a1 only)
			menu.grab_release()

	def treeClicked(self, event):
		treev = self.treev
		if self.menu:
			self.menu.destroy()
			self.menu = None
			return
		optName = treev.identify_row(event.y)  # optName is rowId
		if not optName:
			return
		col = treev.identify_column(event.x)  # "#1" to self.valueCol
		if col == "#1":
			value = treev.set(optName, col)
			treev.set(optName, col, 1 - int(value))
			return
		if col == self.valueCol:
			self.valueCellClicked(event, optName)

	def okClicked(self):
		treev = self.treev
		for optName in self.options:
			enable = bool(int(treev.set(optName, "#1")))
			if not enable:
				if optName in self.values:
					del self.values[optName]
				continue
			rawValue = treev.set(optName, self.valueCol)
			prop = self.optionsProp[optName]
			value, isValid = prop.evaluate(rawValue)
			if not isValid:
				log.error(f"invalid option value {optName} = {rawValue}")
				continue
			self.values[optName] = value
		self.destroy()


class FormatOptionsButton(ttk.Button):
	def __init__(
		self,
		kind: Literal["Read", "Write"],
		values: dict,
		formatInput: FormatButton,
		master=None,
	) -> None:
		ttk.Button.__init__(
			self,
			master=master,
			text="Options",
			command=self.buttonClicked,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		self.kind = kind
		self.values = values
		self.formatInput = formatInput

	def setOptionsValues(self, values):
		self.values = values

	def buttonClicked(self):
		formatD = self.formatInput.get()
		if not formatD:
			return

		dialog = FormatOptionsDialog(
			pluginByDesc[formatD].name,
			self.kind,
			self.values,
			master=self,
		)

		# x, y, w, h = decodeGeometry(dialog.geometry())
		w, h = 380, 250
		# w and h are rough estimated width and height of `dialog`
		px, py, pw, ph = decodeGeometry(self.winfo_toplevel().geometry())
		# move dialog without changing the size
		dialog.geometry(
			encodeLocation(
				px + pw // 2 - w // 2,
				py + ph // 2 - h // 2,
			),
		)
		dialog.focus()


class UI(tk.Frame, UIBase):
	fcd_dir_save_path = join(confDir, "ui-tk-fcd-dir")

	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		rootWin = self.rootWin = tk.Tk()
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
		#           'xpnative')
		style = ttk.Style()
		style.configure("TButton", borderwidth=3)
		# style.theme_use("default")
		# there is no tk.Style()
		########
		self.pack(fill="x")
		# rootWin.bind("<Configure>", self.resized)
		#######################
		defaultFont = tkFont.nametofont("TkDefaultFont")
		if core.sysName in {"linux", "freebsd"}:
			defaultFont.configure(size=int(defaultFont.cget("size") * 1.4))
		####
		self.biggerFont = defaultFont.copy()
		self.biggerFont.configure(size=int(defaultFont.cget("size") * 1.8))
		######################
		self.glos = Glossary(ui=self)
		self.glos.config = self.config
		self.glos.progressbar = progressbar
		self._convertOptions = {}
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
		label = ttk.Label(convertFrame, text="Input File: ")
		label.grid(
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
		label = ttk.Label(convertFrame, text="Input Format: ")
		label.grid(
			row=row,
			column=0,
			sticky=tk.W,
			padx=5,
		)
		##
		self.formatButtonInputConvert = FormatButton(
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
		##
		self.readOptionsButton = FormatOptionsButton(
			"Read",
			self.readOptions,
			self.formatButtonInputConvert,
			master=convertFrame,
		)
		self.inputFormatRow = row
		######################
		row += 1
		label = ttk.Label(convertFrame)
		label.grid(
			row=row,
			column=0,
			sticky=tk.W,
		)
		######################
		row += 1
		label = ttk.Label(convertFrame, text="Output Format: ")
		label.grid(
			row=row,
			column=0,
			sticky=tk.W,
			padx=5,
		)
		##
		self.formatButtonOutputConvert = FormatButton(
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
		##
		self.writeOptionsButton = FormatOptionsButton(
			"Write",
			self.writeOptions,
			self.formatButtonOutputConvert,
			master=convertFrame,
		)
		self.outputFormatRow = row
		###################
		row += 1
		label = ttk.Label(convertFrame, text="Output File: ")
		label.grid(
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
		button = newButton(
			convertFrame,
			text="Browse",
			command=self.browseOutputConvert,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.grid(
			row=row,
			column=3,
			sticky=tk.W + tk.E,
			padx=5,
		)
		###################
		row += 1
		button = newButton(
			convertFrame,
			text="Convert",
			command=self.convert,
			# background="#00e000",
			# activebackground="#22f022",
			# borderwidth=7,
			# font=self.biggerFont,
			# padx=5,
			# pady=5,
		)
		button.grid(
			row=row,
			column=2,
			columnspan=3,
			sticky=tk.W + tk.E + tk.S,
			padx=5,
			pady=5,
		)
		# print(f"row number for Convert button: {row}")
		######
		convertFrame.pack(fill="x")
		# convertFrame.grid(sticky=tk.W + tk.E + tk.N + tk.S)
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
		versionFrame = ttk.Frame(notebook)
		label = newLabelWithImage(versionFrame, file=logo)
		label.pack(fill="both", expand=True)
		##
		##
		label = ttk.Label(versionFrame, text=f"PyGlossary\nVersion {getVersion()}")
		label.pack(fill="both", expand=True)
		##
		versionFrame.pack(side="top", fill="x")

		aboutFrame = ttk.Frame(notebook)
		authorsFrame = ttk.Frame(notebook)
		licenseFrame = ttk.Frame(notebook)

		notebook.add(convertFrame, text="Convert", underline=0)
		notebook.add(authorsFrame, text="Authors", underline=0)
		notebook.add(licenseFrame, text="License", underline=0)
		notebook.add(aboutFrame, text="About", underline=0)
		notebook.add(versionFrame, text="Version", underline=0)

		label = newReadOnlyText(
			aboutFrame,
			text=f"{aboutText}\nHome page: {core.homePage}",
			font=("DejaVu Sans", 11, ""),
		)
		label.pack(fill="x")

		authorsText = "\n".join(authors)
		authorsText = authorsText.replace("\t", "    ")
		label = newReadOnlyText(
			authorsFrame,
			text=authorsText,
			font=("DejaVu Sans", 11, ""),
		)
		label.pack(fill="x")

		label = newReadOnlyText(
			licenseFrame,
			text=licenseText,
			font=("DejaVu Sans", 11, ""),
		)
		label.pack(fill="x")

		######################
		tk.Grid.columnconfigure(convertFrame, 0, weight=1)
		tk.Grid.columnconfigure(convertFrame, 1, weight=30)
		tk.Grid.columnconfigure(convertFrame, 2, weight=20)
		tk.Grid.columnconfigure(convertFrame, 3, weight=1)
		tk.Grid.rowconfigure(convertFrame, 0, weight=50)
		tk.Grid.rowconfigure(convertFrame, 1, weight=50)
		tk.Grid.rowconfigure(convertFrame, 2, weight=1)
		tk.Grid.rowconfigure(convertFrame, 3, weight=50)
		tk.Grid.rowconfigure(convertFrame, 4, weight=50)
		tk.Grid.rowconfigure(convertFrame, 5, weight=1)
		tk.Grid.rowconfigure(convertFrame, 6, weight=50)

		# _________________________________________________________________ #

		notebook.pack(fill="both", expand=True)

		# _________________________________________________________________ #

		statusBarframe = ttk.Frame(self)
		clearB = newButton(
			statusBarframe,
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
		label = ttk.Label(statusBarframe, text="Verbosity")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			statusBarframe,
			comboVar,
			log.getVerbosity(),  # default
			0,
			1,
			2,
			3,
			4,
			5,
		)
		comboVar.trace_add("write", self.verbosityChanged)
		combo.pack(side="left")
		self.verbosityCombo = comboVar
		comboVar.set(log.getVerbosity())
		#####
		pbar = ProgressBar(statusBarframe, width=700, height=28)
		pbar.pack(side="left", fill="x", expand=True)
		self.pbar = pbar
		statusBarframe.pack(fill="x")
		self.progressTitle = ""
		# _________________________________________________________________ #

		centerWindow(rootWin)
		# show the window
		if os.sep == "\\":  # Windows
			rootWin.attributes("-alpha", 1.0)
		else:  # Linux
			rootWin.deiconify()

	def textSelectAll(self, tktext):
		tktext.tag_add(tk.SEL, "1.0", tk.END)
		tktext.mark_set(tk.INSERT, "1.0")
		tktext.see(tk.INSERT)

	def consoleKeyPress(self, e):
		# print(e.state, e.keysym)
		if e.state > 0:
			if e.keysym == "c":
				return None
			if e.keysym == "a":
				self.textSelectAll(self.console)
				return "break"
		if e.keysym == "Escape":
			return None
		return "break"

	def verbosityChanged(self, _index, _value, _op):
		log.setVerbosity(
			int(self.verbosityCombo.get()),
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

	def inputFormatChanged(self, *_args):
		formatDesc = self.formatButtonInputConvert.get()
		if not formatDesc:
			return
		self.readOptions.clear()  # reset the options, DO NOT re-assign
		if Glossary.formatsReadOptions[pluginByDesc[formatDesc].name]:
			self.readOptionsButton.grid(
				row=self.inputFormatRow,
				column=3,
				sticky=tk.W + tk.E,
				padx=5,
				pady=0,
			)
		else:
			self.readOptionsButton.grid_forget()

	def outputFormatChanged(self, *_args):
		formatDesc = self.formatButtonOutputConvert.get()
		if not formatDesc:
			return

		formatName = pluginByDesc[formatDesc].name
		plugin = Glossary.plugins.get(formatName)
		if not plugin:
			log.error(f"plugin {formatName} not found")
			return

		self.writeOptions.clear()  # reset the options, DO NOT re-assign
		if Glossary.formatsWriteOptions[formatName]:
			self.writeOptionsButton.grid(
				row=self.outputFormatRow,
				column=3,
				sticky=tk.W + tk.E,
				padx=5,
				pady=0,
			)
		else:
			self.writeOptionsButton.grid_forget()

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

	def anyEntryChanged(self, _event=None):
		self.inputEntryChanged()
		self.outputEntryChanged()

	def inputEntryChanged(self, _event=None):
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
						self.inputFormatChanged()
		self.pathI = pathI

	def outputEntryChanged(self, _event=None):
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
					self.outputFormatChanged()
		self.pathO = pathO

	def save_fcd_dir(self):
		if not self.fcd_dir:
			return
		with open(self.fcd_dir_save_path, mode="w", encoding="utf-8") as fp:
			fp.write(self.fcd_dir)

	def browseInputConvert(self):
		path = filedialog.askopenfilename(initialdir=self.fcd_dir)
		if path:
			self.entryInputConvert.delete(0, "end")
			self.entryInputConvert.insert(0, path)
			self.inputEntryChanged()
			self.fcd_dir = os.path.dirname(path)
			self.save_fcd_dir()

	def browseOutputConvert(self):
		path = filedialog.asksaveasfilename()
		if path:
			self.entryOutputConvert.delete(0, "end")
			self.entryOutputConvert.insert(0, path)
			self.outputEntryChanged()
			self.fcd_dir = os.path.dirname(path)
			self.save_fcd_dir()

	def convert(self):
		inPath = self.entryInputConvert.get()
		if not inPath:
			log.critical("Input file path is empty!")
			return None
		inFormatDesc = self.formatButtonInputConvert.get()
		# if not inFormatDesc:
		# 	log.critical("Input format is empty!");return
		inFormat = pluginByDesc[inFormatDesc].name if inFormatDesc else ""

		outPath = self.entryOutputConvert.get()
		if not outPath:
			log.critical("Output file path is empty!")
			return None
		outFormatDesc = self.formatButtonOutputConvert.get()
		if not outFormatDesc:
			log.critical("Output format is empty!")
			return None
		outFormat = pluginByDesc[outFormatDesc].name

		for attr, value in self._glossarySetAttrs.items():
			setattr(self.glos, attr, value)

		try:
			finalOutputFile = self.glos.convert(
				ConvertArgs(
					inPath,
					inputFormat=inFormat,
					outputFilename=outPath,
					outputFormat=outFormat,
					readOptions=self.readOptions,
					writeOptions=self.writeOptions,
					**self._convertOptions,
				),
			)
		except Error as e:
			log.critical(str(e))
			self.glos.cleanup()
			return False
		# if finalOutputFile:
		# 	self.status("Convert finished")
		# else:
		# 	self.status("Convert failed")
		return bool(finalOutputFile)

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
	):
		self.config = config

		if inputFilename:
			self.entryInputConvert.insert(0, abspath(inputFilename))
			self.inputEntryChanged()
		if outputFilename:
			self.entryOutputConvert.insert(0, abspath(outputFilename))
			self.outputEntryChanged()

		if inputFormat:
			self.formatButtonInputConvert.setValue(
				Glossary.plugins[inputFormat].description,
			)
			self.inputFormatChanged()
		if outputFormat:
			self.formatButtonOutputConvert.setValue(
				Glossary.plugins[outputFormat].description,
			)
			self.outputFormatChanged()

		if reverse:
			log.error("Tkinter interface does not support Reverse feature")

		# must be before setting self.readOptions and self.writeOptions
		self.anyEntryChanged()

		if readOptions:
			self.readOptionsButton.setOptionsValues(readOptions)
			self.readOptions = readOptions

		if writeOptions:
			self.writeOptionsButton.setOptionsValues(writeOptions)
			self.writeOptions = writeOptions

		self._convertOptions = convertOptions
		if convertOptions:
			log.info(f"Using {convertOptions=}")

		self._glossarySetAttrs = glossarySetAttrs or {}

		# inputFilename and readOptions are for DB Editor
		# which is not implemented
		self.mainloop()

	def progressInit(self, title):
		self.progressTitle = title

	def progress(self, ratio, text=""):
		if not text:
			text = "%" + str(int(ratio * 100))
		text += " - " + self.progressTitle
		self.pbar.updateProgress(ratio * 100, None, text)
		# self.pbar.value = ratio * 100
		# self.pbar.update()
		self.rootWin.update()

	def console_clear(self, _event=None):
		self.console.delete("1.0", "end")
		self.console.insert("end", "Console:\n")

	# def reverseBrowseInput(self):
	# 	pass

	# def reverseBrowseOutput(self):
	# 	pass

	# def reverseLoad(self):
	# 	pass


if __name__ == "__main__":
	import sys

	_path = sys.argv[1] if len(sys.argv) > 1 else ""
	_ui = UI(_path)
	_ui.run()
