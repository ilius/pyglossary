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
from pathlib import Path
from tkinter import filedialog, ttk
from tkinter import font as tkFont
from typing import TYPE_CHECKING, Any

from pyglossary.core import confDir, homeDir, sysName
from pyglossary.glossary_utils import Error
from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.os_utils import abspath2
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import UIBase
from pyglossary.ui.ui_tk.about import createAboutFrame

from .ui_tk.format_widgets import FormatButton, FormatOptionsDialog
from .ui_tk.general_options import GeneralOptionsDialog
from .ui_tk.info import PreConvertInfoDialog
from .ui_tk.log_handler import TkTextLogHandler
from .ui_tk.progressbar import ProgressBar
from .ui_tk.utils import centerWindow, newButton, set_window_icon

if TYPE_CHECKING:
	from pyglossary.config_type import ConfigType
	from pyglossary.logger import Logger


__all__ = ["UI"]

log: Logger = logging.getLogger("pyglossary")

# Compact file-picker buttons:
_PATH_BUTTON_PLACEHOLDER = "[Select...]"
_PATH_BUTTON_WIDTH = 20  # characters

readDesc = [plugin.description for plugin in Glossary.plugins.values() if plugin.canRead]
writeDesc = [
	plugin.description for plugin in Glossary.plugins.values() if plugin.canWrite
]
pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}


class UI(tk.Frame, UIBase):
	fcd_dir_save_path = join(confDir, "ui-tk-fcd-dir")

	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		rootWin = self.rootWin = tk.Tk(className="PyGlossary")
		if os.sep == "\\":
			rootWin.attributes("-alpha", 0.0)
		else:
			rootWin.withdraw()

		tk.Frame.__init__(self, rootWin)
		UIBase.__init__(self)
		self._baseWindowTitle = "PyGlossary Wizard (Tkinter)"
		rootWin.title(self._baseWindowTitle)
		rootWin.resizable(True, False)
		max_w = max(400, rootWin.winfo_screenwidth() - 48)
		max_h = max(300, rootWin.winfo_screenheight() - 48)
		rootWin.wm_maxsize(max_w, max_h)
		set_window_icon(rootWin)
		rootWin.bind("<Escape>", lambda _e: rootWin.quit())

		style = ttk.Style()
		style.configure("TButton", borderwidth=3)

		self.pack(fill="both", expand=True)

		defaultFont = tkFont.nametofont("TkDefaultFont")
		if sysName in {"linux", "freebsd"}:
			defaultFont.configure(size=int(defaultFont.cget("size") * 1.4))

		self.progressbar = progressbar
		self.infoOverride: dict[str, Any] = {}
		self.convertOptions: dict[str, Any] = {}
		self.readOptions: dict[str, Any] = {}
		self.writeOptions: dict[str, Any] = {}
		self.pathI = ""
		self.pathO = ""
		self.currentPage = 0

		fcd_dir = join(homeDir, "Desktop")
		if isfile(self.fcd_dir_save_path):
			try:
				with open(self.fcd_dir_save_path, encoding="utf-8") as fp:
					fcd_dir = fp.read().strip("\n")
			except Exception:
				log.exception("")
		self.fcd_dir = fcd_dir

		mainFrame = ttk.Frame(self)
		mainFrame.pack(fill="both", expand=True, padx=8, pady=8)
		mainFrame.rowconfigure(0, weight=1)
		mainFrame.columnconfigure(0, weight=1)

		pageContainer = ttk.Frame(mainFrame)
		pageContainer.grid(row=0, column=0, sticky="nsew")
		self.pageContainer = pageContainer

		self.pages = [
			self._makePageInput(pageContainer),
			self._makePageOutput(pageContainer),
			self._makePageFormats(pageContainer),
			self._makePageConvert(pageContainer),
		]
		for page in self.pages:
			page.grid(row=0, column=0, sticky="nsew")
		pageContainer.rowconfigure(0, weight=1)
		pageContainer.columnconfigure(0, weight=1)

		nav = ttk.Frame(mainFrame)
		nav.grid(row=1, column=0, sticky="ew", pady=(8, 0))
		# Keep controls in view:
		# cluster at bottom-right with margin (not flush to corner).
		navButtonFrame = ttk.Frame(nav)
		navButtonFrame.pack(side="bottom", fill="x", padx=(8, 4), pady=2)
		self._navButtonFrame = navButtonFrame

		self.aboutButton = newButton(
			navButtonFrame,
			text="About",
			command=self.aboutClicked,
		)
		self.aboutButton.pack(side="left", padx=(6, 4))

		self.clearButton = newButton(
			navButtonFrame,
			text="Clear",
			command=self.console_clear,
		)
		self.prevButton = newButton(
			navButtonFrame,
			text="Previous",
			command=self.prevPage,
		)
		self.nextButton = newButton(
			navButtonFrame,
			text="Next",
			command=self.nextPage,
		)

		self._showPage(0)

	def aboutClicked(self) -> None:
		print("aboutClicked")
		dialog = tk.Toplevel()
		defaultFont = tkFont.nametofont("TkDefaultFont")
		# if sysName in {"linux", "freebsd"}:
		# 	defaultFont.configure(size=int(defaultFont.cget("size") * 1.4))
		####
		bigFont = defaultFont.copy()
		# bigFont.configure(size=int(defaultFont.cget("size") * 1.6))
		frame = createAboutFrame(dialog, bigFont)
		frame.pack(fill="x")
		set_window_icon(dialog)
		dialog.bind("<Escape>", lambda _e: dialog.destroy())
		dialog.resizable(width=True, height=True)
		dialog.title("Set Info / Metedata")
		buttonBox = ttk.Frame(master=dialog)

		def okClicked() -> None:
			dialog.destroy()

		okButton = newButton(
			buttonBox,
			text="  OK  ",
			command=okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		okButton.pack(side="right")
		buttonBox.pack(fill="x")

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

	def console_clear(self, _event: tk.Event | None = None) -> None:
		self.console.delete("1.0", "end")
		self.console.insert("end", "Console:\n")

	def _centerBlock(
		self,
		page: ttk.Frame,
		*,
		vertical: str = "center",
	) -> ttk.Frame:
		"""
		Place content in a horizontally centered column;
		optional vertical centering.
		"""
		page.grid_columnconfigure(0, weight=1)
		page.grid_columnconfigure(2, weight=1)
		if vertical == "center":
			page.grid_rowconfigure(0, weight=1)
			page.grid_rowconfigure(2, weight=1)
			row = 1
			sticky = "n"
		else:
			page.grid_rowconfigure(1, weight=1)
			row = 0
			sticky = "new"
		inner = ttk.Frame(page)
		inner.grid(row=row, column=1, sticky=sticky)
		return inner

	def _path_label_wraplength(self) -> int:
		"""Pixels; keeps format-review path labels from forcing an over-wide window."""
		try:
			sw = self.rootWin.winfo_screenwidth()
		except tk.TclError:
			sw = 1024
		# Comfortable margin from screen edges; cap like the convert-page summary.
		inner = max(280, sw - 160)
		return min(520, inner)

	def _truncate_for_button_label(self, text: str, max_chars: int = 48) -> str:
		if len(text) <= max_chars:
			return text
		keep = max_chars - 3
		left = max(1, keep // 2)
		right = keep - left
		return text[:left] + "..." + text[-right:]

	def _path_button_text(self, path: str, empty_placeholder: str) -> str:
		path = path.strip()
		if not path:
			return empty_placeholder
		p = path.rstrip(os.sep)
		name = os.path.basename(p)
		display = name or p
		return self._truncate_for_button_label(
			display,
			max_chars=_PATH_BUTTON_WIDTH,
		)

	def _file_name_for_summary(self, path: str) -> str:
		path = path.strip()
		if not path:
			return "—"
		p = path.rstrip(os.sep)
		name = os.path.basename(p)
		return name or p

	def _sync_path_buttons(self) -> None:
		self.inputPathButton.configure(
			text=self._path_button_text(
				self.entryInputConvert.get(),
				_PATH_BUTTON_PLACEHOLDER,
			),
		)
		self.outputPathButton.configure(
			text=self._path_button_text(
				self.entryOutputConvert.get(),
				_PATH_BUTTON_PLACEHOLDER,
			),
		)

	def _page_inputs_complete(self, page_index: int | None = None) -> bool:
		idx = self.currentPage if page_index is None else page_index
		if idx == 0:
			return bool(self.entryInputConvert.get().strip())
		if idx == 1:
			return bool(self.entryOutputConvert.get().strip())
		if idx == 2:
			return (
				bool(self.entryInputConvert.get().strip())
				and bool(self.entryOutputConvert.get().strip())
				and bool(self.formatButtonInputConvert.get())
				and bool(self.formatButtonOutputConvert.get())
			)
		# Last page: same requirements as convert() (input format may be empty)
		return (
			bool(self.entryInputConvert.get().strip())
			and bool(self.entryOutputConvert.get().strip())
			and bool(self.formatButtonOutputConvert.get())
		)

	def _update_next_button_state(self) -> None:
		nav_ok = self._page_inputs_complete()
		self.nextButton.configure(state=tk.NORMAL if nav_ok else tk.DISABLED)

	def _makePageInput(self, parent: ttk.Frame) -> ttk.Frame:
		page = ttk.Frame(parent)
		content = self._centerBlock(page)
		content.columnconfigure(0, weight=1)
		ttk.Label(content, text="Input File", anchor="center").grid(
			row=0, column=0, sticky="ew", padx=5, pady=(5, 2)
		)
		entry = ttk.Entry(content)
		self.entryInputConvert = entry
		self.inputPathButton = newButton(
			content,
			text="Select input file...",
			command=self.browseInputConvert,
			width=_PATH_BUTTON_WIDTH,
		)
		self.inputPathButton.grid(row=1, column=0, sticky="w", padx=5, pady=4)
		return page

	def _makePageOutput(self, parent: ttk.Frame) -> ttk.Frame:
		page = ttk.Frame(parent)
		content = self._centerBlock(page)
		content.columnconfigure(0, weight=1)
		ttk.Label(content, text="Output File", anchor="center").grid(
			row=0, column=0, sticky="ew", padx=5, pady=(5, 2)
		)
		entry = ttk.Entry(content)
		self.entryOutputConvert = entry
		self.outputPathButton = newButton(
			content,
			text="Select output file...",
			command=self.browseOutputConvert,
			width=_PATH_BUTTON_WIDTH,
		)
		self.outputPathButton.grid(row=1, column=0, sticky="w", padx=5, pady=4)
		return page

	def _makePageFormats(self, parent: ttk.Frame) -> ttk.Frame:
		page = ttk.Frame(parent)
		content = self._centerBlock(page)
		content.columnconfigure(1, weight=1)

		ttk.Label(content, text="Input File:").grid(
			row=0, column=0, sticky="e", padx=5, pady=(5, 2)
		)
		self.page3InputPathVar = tk.StringVar()
		wrap = self._path_label_wraplength()
		ttk.Label(
			content,
			textvariable=self.page3InputPathVar,
			wraplength=wrap,
			justify="left",
		).grid(
			row=0,
			column=1,
			sticky="nw",
			padx=5,
			pady=(5, 2),
		)

		ttk.Label(content, text="Output File:").grid(
			row=1,
			column=0,
			sticky="e",
			padx=5,
			pady=2,
		)
		self.page3OutputPathVar = tk.StringVar()
		ttk.Label(
			content,
			textvariable=self.page3OutputPathVar,
			wraplength=wrap,
			justify="left",
		).grid(
			row=1,
			column=1,
			sticky="nw",
			padx=5,
			pady=2,
		)

		ttk.Label(content, text="Input Format:").grid(
			row=2,
			column=0,
			sticky="e",
			padx=5,
			pady=(12, 5),
		)
		self.formatButtonInputConvert = FormatButton(
			self.rootWin,
			master=content,
			descList=readDesc,
			dialogTitle="Select Input Format",
			onChange=self.inputFormatChanged,
		)
		self.formatButtonInputConvert.grid(
			row=2,
			column=1,
			sticky="w",
			padx=5,
			pady=(12, 5),
		)

		ttk.Label(content, text="Output Format:").grid(
			row=3,
			column=0,
			sticky="e",
			padx=5,
			pady=5,
		)
		self.formatButtonOutputConvert = FormatButton(
			self.rootWin,
			master=content,
			descList=writeDesc,
			dialogTitle="Select Output Format",
			onChange=self.outputFormatChanged,
		)
		self.formatButtonOutputConvert.grid(
			row=3,
			column=1,
			sticky="w",
			padx=5,
			pady=5,
		)

		return page

	def _makePageConvert(self, parent: ttk.Frame) -> ttk.Frame:
		page = ttk.Frame(parent)
		content = self._centerBlock(page, vertical="top")
		content.columnconfigure(1, weight=1)

		self.page4SummaryVar = tk.StringVar()

		ttk.Label(
			content,
			textvariable=self.page4SummaryVar,
			wraplength=self._path_label_wraplength(),
			justify="left",
		).grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 10))

		buttonRow = ttk.Frame(content)
		buttonRow.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
		btnInner = ttk.Frame(buttonRow)
		btnInner.pack(anchor="center")
		newButton(
			btnInner,
			text="Read Options",
			command=self.readOptionsClicked,
		).pack(side="left", padx=4)
		newButton(
			btnInner,
			text="Write Options",
			command=self.writeOptionsClicked,
		).pack(side="left", padx=4)

		optionsMenu = tk.Menu(tearoff=False)
		optionsMenu.add_command(
			label="General Options",
			command=self.generalOptionsClicked,
		)
		optionsMenu.add_command(
			label="Info / Metadata",
			command=self.infoOptionClicked,
		)
		optionsButton = ttk.Menubutton(
			btnInner,
			text="General Options",
			menu=optionsMenu,
		)
		optionsButton.pack(side="left", padx=4)

		console = tk.Text(content, height=12, background="#000", foreground="#fff")
		console.bind("<Key>", self.consoleKeyPress)
		console.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0))
		log.addHandler(TkTextLogHandler(console))
		console.insert("end", "Console:\n")
		self.console = console

		self.statusBarFrame = ttk.Frame(content)
		self.statusBarFrame.grid(
			row=3,
			column=0,
			columnspan=2,
			sticky="ew",
			padx=5,
			pady=(4, 0),
		)

		return page

	def _showPage(self, index: int) -> None:
		self.currentPage = index
		self.pages[index].tkraise()
		self._updateSummaryLabels()
		self._updateNavigationButtons()

	def _updateNavigationButtons(self) -> None:
		self.rootWin.title(f"{self._baseWindowTitle} - Step {self.currentPage + 1}")
		if self.currentPage == len(self.pages) - 1:
			self.nextButton.configure(text="Convert", command=self.convert)
		else:
			self.nextButton.configure(text="Next", command=self.nextPage)
		self.clearButton.pack_forget()
		self.nextButton.pack_forget()
		self.prevButton.pack_forget()
		self.nextButton.pack(side="right", padx=(6, 4))
		if self.currentPage != 0:
			self.prevButton.pack(side="right", padx=6)
		if self.currentPage == len(self.pages) - 1:
			self.clearButton.pack(side="right", padx=6)
		self._update_next_button_state()

	def _updateSummaryLabels(self) -> None:
		inPath = self.entryInputConvert.get().strip()
		outPath = self.entryOutputConvert.get().strip()
		inFormat = self.formatButtonInputConvert.get() or "-"
		outFormat = self.formatButtonOutputConvert.get() or "-"

		self.page3InputPathVar.set(Path(inPath or "-").name)
		self.page3OutputPathVar.set(Path(outPath or "-").name)
		self.page4SummaryVar.set(
			'Converting {} at "{}" to {} at "{}"'.format(
				inFormat,
				inPath or "—",
				outFormat,
				outPath or "—",
			)
		)
		self._sync_path_buttons()
		self._update_next_button_state()

	def nextPage(self) -> None:
		if self.currentPage < len(self.pages) - 1:
			self.anyEntryChanged()
			self._showPage(self.currentPage + 1)

	def prevPage(self) -> None:
		if self.currentPage > 0:
			self.anyEntryChanged()
			self._showPage(self.currentPage - 1)

	def inputFormatChangedAuto(self) -> None:
		self.inputFormatChanged(self.formatButtonInputConvert.get())

	def outputFormatChangedAuto(self) -> None:
		self.outputFormatChanged(self.formatButtonOutputConvert.get())

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
		self._updateSummaryLabels()

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
		self._updateSummaryLabels()

	def inputFormatChanged(self, formatDesc: str) -> None:
		if not formatDesc:
			return
		self.readOptions.clear()  # reset the options, DO NOT re-assign
		self._updateSummaryLabels()

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

		self._updateSummaryLabels()

	def save_fcd_dir(self) -> None:
		if not self.fcd_dir:
			return
		with open(self.fcd_dir_save_path, mode="w", encoding="utf-8") as fp:
			fp.write(self.fcd_dir)

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
		self._updateSummaryLabels()

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
		self._updateSummaryLabels()

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

	def before_mainloop(self) -> None:
		# After layout, lock size so button label changes do not resize the window.
		self.rootWin.update_idletasks()
		self.rootWin.geometry("800x400")
		# self.rootWin.resizable(False, False)

	def progress(self, ratio: float, text: str = "") -> None:
		if not text:
			text = "%" + str(int(ratio * 100))
		title = self.progressTitle
		if (ratio >= 1.0 or int(ratio * 100) >= 100) and title == "Converting":
			title = "Done"
		text += " - " + title
		self.pbar.updateProgress(ratio * 100, None, text)
		try:
			self.rootWin.update()
		except tk.TclError:
			pass

	def anyEntryChanged(self, _event: tk.Event | None = None) -> None:
		self.inputEntryChanged()
		self.outputEntryChanged()
