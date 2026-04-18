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

import logging
import os
import tkinter as tk
from os.path import isfile, join, splitext
from tkinter import filedialog, ttk
from tkinter import font as tkFont
from typing import TYPE_CHECKING, Any

from pyglossary.core import confDir, homeDir, sysName
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.os_utils import abspath2
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import UIBase

from .about import createAboutFrame
from .format_widgets import FormatButton, FormatOptionsDialog
from .general_options import GeneralOptionsDialog
from .info import PreConvertInfoDialog
from .log_handler import TkTextLogHandler
from .progressbar import ProgressBar
from .utils import (
	centerWindow,
	decodeGeometry,
	encodeLocation,
	newButton,
	set_window_icon,
)

if TYPE_CHECKING:
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
		aboutFrame = createAboutFrame(notebook, self.bigFont)

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

		if convertOptions:
			log.info(f"Using {convertOptions=}")
			self.infoOverride = convertOptions.pop("infoOverride", None) or {}

		self.convertOptions: dict[str, Any] = convertOptions or {}

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
