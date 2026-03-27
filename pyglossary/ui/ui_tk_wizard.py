# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

# FIXME: bug: in page 1, the Next buttons moves out of view
# when I chnage the file


from __future__ import annotations

import os
import tkinter as tk
from os.path import isfile, join
from tkinter import font as tkFont
from tkinter import ttk
from typing import Any

from pyglossary.core import confDir, homeDir, sysName

from . import ui_tk
from .ui_tk import (
	FormatButton,
	GeneralOptionsDialog,
	PreConvertInfoDialog,
	TkTextLogHandler,
	newButton,
	set_window_icon,
)

__all__ = ["UI"]

log = ui_tk.log
readDesc = ui_tk.readDesc
writeDesc = ui_tk.writeDesc


class UI(ui_tk.UI):
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
		ui_tk.UIBase.__init__(self)
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

		pageContainer = ttk.Frame(mainFrame)
		pageContainer.pack(fill="both", expand=True)
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
		nav.pack(fill="x", pady=(8, 0))
		self.clearButton = newButton(nav, text="Clear", command=self.console_clear)
		self.prevButton = newButton(nav, text="Previous", command=self.prevPage)
		self.nextButton = newButton(nav, text="Next", command=self.nextPage)

		self._showPage(0)

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
		return self._truncate_for_button_label(display)

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
				"[Select...]",
			),
		)
		self.outputPathButton.configure(
			text=self._path_button_text(
				self.entryOutputConvert.get(),
				"[Select...]",
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
		)
		self.inputPathButton.grid(row=1, column=0, sticky="ew", padx=5, pady=4)
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
		)
		self.outputPathButton.grid(row=1, column=0, sticky="ew", padx=5, pady=4)
		return page

	def _makePageFormats(self, parent: ttk.Frame) -> ttk.Frame:
		page = ttk.Frame(parent)
		content = self._centerBlock(page)
		content.columnconfigure(1, weight=1)

		ttk.Label(content, text="Input File:").grid(
			row=0, column=0, sticky="e", padx=5, pady=(5, 2)
		)
		self.page3InputPathVar = tk.StringVar()
		ttk.Label(content, textvariable=self.page3InputPathVar).grid(
			row=0, column=1, sticky="w", padx=5, pady=(5, 2)
		)

		ttk.Label(content, text="Output File:").grid(
			row=1, column=0, sticky="e", padx=5, pady=2
		)
		self.page3OutputPathVar = tk.StringVar()
		ttk.Label(content, textvariable=self.page3OutputPathVar).grid(
			row=1, column=1, sticky="w", padx=5, pady=2
		)

		ttk.Label(content, text="Input Format:").grid(
			row=2, column=0, sticky="e", padx=5, pady=(12, 5)
		)
		self.formatButtonInputConvert = FormatButton(
			self.rootWin,
			master=content,
			descList=readDesc,
			dialogTitle="Select Input Format",
			onChange=self.inputFormatChanged,
		)
		self.formatButtonInputConvert.grid(
			row=2, column=1, sticky="w", padx=5, pady=(12, 5)
		)

		ttk.Label(content, text="Output Format:").grid(
			row=3, column=0, sticky="e", padx=5, pady=5
		)
		self.formatButtonOutputConvert = FormatButton(
			self.rootWin,
			master=content,
			descList=writeDesc,
			dialogTitle="Select Output Format",
			onChange=self.outputFormatChanged,
		)
		self.formatButtonOutputConvert.grid(row=3, column=1, sticky="w", padx=5, pady=5)

		return page

	def _makePageConvert(self, parent: ttk.Frame) -> ttk.Frame:
		page = ttk.Frame(parent)
		content = self._centerBlock(page, vertical="top")
		content.columnconfigure(1, weight=1)

		self.page4SummaryVar = tk.StringVar()

		ttk.Label(
			content,
			textvariable=self.page4SummaryVar,
			wraplength=520,
			justify="left",
		).grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 10))

		buttonRow = ttk.Frame(content)
		buttonRow.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
		btnInner = ttk.Frame(buttonRow)
		btnInner.pack(anchor="center")
		newButton(btnInner, text="Read Options", command=self.readOptionsClicked).pack(
			side="left", padx=4
		)
		newButton(btnInner, text="Write Options", command=self.writeOptionsClicked).pack(
			side="left", padx=4
		)

		optionsMenu = tk.Menu(tearoff=False)
		optionsMenu.add_command(
			label="General Options", command=self.generalOptionsClicked
		)
		optionsMenu.add_command(label="Info / Metadata", command=self.infoOptionClicked)
		optionsButton = ttk.Menubutton(btnInner, text="General Options", menu=optionsMenu)
		optionsButton.pack(side="left", padx=4)

		console = tk.Text(content, height=12, background="#000", foreground="#fff")
		console.bind("<Key>", self.consoleKeyPress)
		console.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 0))
		log.addHandler(TkTextLogHandler(console))
		console.insert("end", "Console:\n")
		self.console = console

		self.statusBarFrame = ttk.Frame(content)
		self.statusBarFrame.grid(
			row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(4, 0)
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
		self.nextButton.pack(side="right", padx=(6, 8))
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

		self.page3InputPathVar.set(inPath or "-")
		self.page3OutputPathVar.set(outPath or "-")
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

	def inputEntryChanged(self, _event: tk.Event | None = None) -> None:
		super().inputEntryChanged(_event)
		self._updateSummaryLabels()

	def outputEntryChanged(self, _event: tk.Event | None = None) -> None:
		super().outputEntryChanged(_event)
		self._updateSummaryLabels()

	def inputFormatChanged(self, formatDesc: str) -> None:
		super().inputFormatChanged(formatDesc)
		self._updateSummaryLabels()

	def outputFormatChanged(self, formatDesc: str) -> None:
		super().outputFormatChanged(formatDesc)
		self._updateSummaryLabels()

	def readOptionsClicked(self) -> None:
		super().readOptionsClicked()
		self._updateSummaryLabels()

	def writeOptionsClicked(self) -> None:
		super().writeOptionsClicked()
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

	def progress(self, ratio: float, text: str = "") -> None:
		if not text:
			text = "%" + str(int(ratio * 100))
		title = self.progressTitle
		if (ratio >= 1.0 or int(ratio * 100) >= 100) and title == "Converting":
			title = "Done"
		text += " - " + title
		self.pbar.updateProgress(ratio * 100, None, text)
		self.rootWin.update()
