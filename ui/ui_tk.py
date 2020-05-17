# -*- coding: utf-8 -*-
# ui_tk.py
#
# Copyright © 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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


from pyglossary.core import homeDir
from pyglossary.glossary import *
from pyglossary.text_utils import urlToPath
from .base import *
from os.path import join
import logging
import traceback

from typing import Union, Dict

import tkinter as tk
from tkinter import filedialog
from tkinter import tix
from tkinter import ttk
from tkinter import font as tkFont

log = logging.getLogger("root")

# startBold = "\x1b[1m"  # Start Bold #len=4
# startUnderline = "\x1b[4m"  # Start Underline #len=4
endFormat = "\x1b[0;0;0m"  # End Format #len=8
# redOnGray = "\x1b[0;1;31;47m"
startRed = "\x1b[31m"


bitmapLogo = join(dataDir, "res", "pyglossary.ico") if "nt" == os.name \
	else "@" + join(dataDir, "res", "pyglossary.xbm")


def set_window_icon(window):
	# window.wm_iconbitmap(bitmap=bitmapLogo)
	window.iconphoto(
		True,
		tk.PhotoImage(file=join(dataDir, "res", "pyglossary.png")),
	)

def decodeGeometry(gs):
	"""
		example for gs: "253x252+30+684"
		returns (x, y, w, h)
	"""
	p = gs.split("+")
	w, h = p[0].split("x")
	return (int(p[1]), int(p[2]), int(w), int(h))

def encodeGeometry(x, y, w, h):
	return "%sx%s+%s+%s" % (w, h, x, y)

def encodeLocation(x, y):
	return "+%s+%s" % (x, y)


def centerWindow(win):
	"""
	centers a tkinter window
	:param win: the root or Toplevel window to center
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


class TkTextLogHandler(logging.Handler):
	def __init__(self, tktext):
		logging.Handler.__init__(self)
		#####
		tktext.tag_config("CRITICAL", foreground="#ff0000")
		tktext.tag_config("ERROR", foreground="#ff0000")
		tktext.tag_config("WARNING", foreground="#ffff00")
		tktext.tag_config("INFO", foreground="#00ff00")
		tktext.tag_config("DEBUG", foreground="#ffffff")
		###
		self.tktext = tktext

	def emit(self, record):
		msg = record.getMessage()
		###
		if record.exc_info:
			_type, value, tback = record.exc_info
			tback_text = "".join(
				traceback.format_exception(_type, value, tback)
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
	"""
		Apply first function SUBST to arguments, than FUNC.
	"""
	if self.subst:
		args = self.subst(*args)
	try:
		return self.func(*args)
	except:
		log.exception("Exception in Tkinter callback:")
tk.CallWrapper.__call__ = CallWrapper__call__


class ProgressBar(tix.Frame):
	"""
	This comes from John Grayson's book "Python and Tkinter programming"
	Edited by Saeed Rasooli
	"""
	def __init__(
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
		bd=2,
	):
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
		tix.Frame.__init__(self, rootWin, relief=appearance, bd=bd)
		self.canvas = tix.Canvas(
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
			width/2,
			height/2,
			text="",
			anchor="c",
			fill=labelColor,
			font=self.labelFont,
		)
		self.update()
		self.bind("<Configure>", self.update)
		self.canvas.pack(side="top", fill="x", expand="no")

	def updateProgress(self, newVal, newMax=None, text=""):
		if newMax:
			self.max = newMax
		self.value = newVal
		self.update(None, text)

	def update(self, event=None, labelText=""):
		# Trim the values to be between min and max
		value = self.value
		if value > self.max:
			value = self.max
		if value < self.min:
			value = self.min
		# Adjust the rectangle
		width = int(self.winfo_width())
		# width = self.width
		ratio = float(value)/self.max
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
		# FIXME:
		# self.canvas.move(self.label, width/2, self.height/2)
		# self.canvas.scale(self.label, 0, 0, float(width)/self.width, 1)
		self.canvas.update_idletasks()



class FormatOptionsButton(ttk.Button):
	def __init__(
		self,
		kind: Union["Read", "Write"],
		values: Dict,
		formatVar: tk.StringVar,
		master=None,
	):
		ttk.Button.__init__(
			self,
			master=master,
			text="Options",
			command=self.buttonClicked,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		self.kind = kind
		self.kindFormatsOptions = {
			"Read": Glossary.formatsReadOptions,
			"Write": Glossary.formatsWriteOptions,
		}
		self.values = values
		self.formatVar = formatVar
		self.menu = None

	def valueMenuItemCustomSelected(self, treev, format, optName, menu=None):
		if menu:
			menu.destroy()
			self.menu = None

		value = treev.set(optName, self.valueCol)

		dialog = tix.Toplevel(master=treev) # bg="#0f0" does not work
		dialog.resizable(width=True, height=True)
		dialog.title(optName)
		set_window_icon(dialog)
		dialog.bind('<Escape>', lambda e: dialog.destroy())

		px, py, pw, ph = decodeGeometry(treev.winfo_toplevel().geometry())
		w = 300
		h = 100
		dialog.geometry(encodeGeometry(
			px + pw//2 - w//2,
			py + ph//2 - h//2,
			w,
			h,
		))
		
		frame = tix.Frame(master=dialog)

		label = ttk.Label(master=frame, text="Value for " + optName)
		label.pack()

		entry = ttk.Entry(master=frame)
		entry.insert(0, value)
		entry.pack(fill="x")

		prop = Glossary.formatsOptionsProp[format][optName]

		def okClicked(event=None):
			rawValue = entry.get()
			if not prop.validateRaw(rawValue):
				log.error(f"invalid {prop.typ} value: {optName} = {rawValue!r}")
				return
			treev.set(optName, self.valueCol, rawValue)
			treev.set(optName, "#1", "1") # enable it
			col_w = tkFont.Font().measure(rawValue)
			if treev.column("Value", width=None) < col_w:
				treev.column("Value", width=col_w)
			dialog.destroy()

		entry.bind("<Return>", okClicked)

		label = ttk.Label(master=frame)
		label.pack(fill="x")

		button = ttk.Button(
			frame,
			text="Ok",
			command=okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		button.pack(side="right")
		###
		frame.pack(fill="x")
		dialog.focus()

	def buttonClicked(self):
		formatD = self.formatVar.get()
		if not formatD:
			return
		format = Glossary.descFormat[formatD]
		options = self.kindFormatsOptions[self.kind][format]
		optionsProp = Glossary.formatsOptionsProp[format]

		dialog = tix.Toplevel()  # bg="#0f0" does not work
		dialog.resizable(width=True, height=True)
		dialog.title(self.kind + " Options")
		set_window_icon(dialog)
		dialog.bind('<Escape>', lambda e: dialog.destroy())
		###
		self.valueCol = "#3"
		cols = [
			"Enable", # bool
			"Name", # str
			"Value", # str
			"Comment", # str
		]
		treev = ttk.Treeview(
			master=dialog,
			columns=cols,
			show="headings",
		)
		for col in cols:
			treev.heading(
				col,
				text=col,
				#command=lambda c=col: sortby(treev, c, 0),
			)
			# adjust the column's width to the header string
			treev.column(
				col,
				width=tkFont.Font().measure(col.title()),
			)
		###
		def valueMenuItemSelected(optName, menu, value):
			treev.set(optName, self.valueCol, value)
			treev.set(optName, "#1", "1") # enable it
			col_w = tkFont.Font().measure(value)
			if treev.column("Value", width=None) < col_w:
				treev.column("Value", width=col_w)
			menu.destroy()
			self.menu = None
		def valueCellClicked(event, optName):
			if not optName:
				return
			prop = optionsProp[optName]
			propValues = prop.values
			if not propValues:
				if prop.customValue:
					self.valueMenuItemCustomSelected(treev, format, optName, None)
				else:
					log.error("invalid option %s, values=%s, customValue=%s" % (propValues, prop.customValue))
				return
			if prop.typ == "bool":
				rawValue = treev.set(optName, self.valueCol)
				if rawValue == "":
					value = False
				else:
					value, isValid = prop.evaluate(rawValue)
					if not isValid:
						log.error("invalid %s = %r" % (optName, rawValue))
						value = False
				treev.set(optName, self.valueCol, str(not value))
				treev.set(optName, "#1", "1") # enable it
				return
			menu = tk.Menu(
				master=treev,
				title=optName,
				tearoff=False,
			)
			self.menu = menu # to destroy it later
			if prop.customValue:
				menu.add_command(
					label="[Custom Value]",
					command=lambda: self.valueMenuItemCustomSelected(treev, format, optName, menu),
				)
			groupedValues = None
			if len(propValues) > 10:
				groupedValues = prop.groupValues()
			maxItemW = 0
			if groupedValues:
				for groupName, subValues in groupedValues.items():
					if subValues is None:
						menu.add_command(
							label=str(value),
							command=lambda value=value: valueMenuItemSelected(optName, menu, value),
						)
						maxItemW = max(maxItemW, tkFont.Font().measure(str(value)))
					else:
						subMenu = tk.Menu(tearoff=False)
						for subValue in subValues:
							subMenu.add_command(
								label=str(subValue),
								command=lambda value=subValue: valueMenuItemSelected(optName, menu, value),
							)
						menu.add_cascade(label=groupName, menu=subMenu)
						maxItemW = max(maxItemW, tkFont.Font().measure(groupName))
			else:
				for value in propValues:
					value = str(value)
					menu.add_command(
						label=value,
						command=lambda value=value: valueMenuItemSelected(optName, menu, value),
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
				# apears where the pointer is on its top-left corner
			finally:
				# make sure to release the grab (Tk 8.0a1 only)
				menu.grab_release()
		def treeClicked(event):
			if self.menu:
				self.menu.destroy()
				self.menu = None
				return
			optName = treev.identify_row(event.y) # optName is rowId
			if not optName:
				return
			col = treev.identify_column(event.x) # "#1" to self.valueCol
			if col == "#1":
				value = treev.set(optName, col)
				treev.set(optName, col, 1-int(value))
				return
			if col == self.valueCol:
				valueCellClicked(event, optName)
		treev.bind(
			"<Button-1>",
			# "<<TreeviewSelect>>", # event.x and event.y are zero
			treeClicked,
		)
		treev.pack(fill="x", expand=True)
		###
		for optName in options:
			prop = optionsProp[optName]
			comment = prop.typ
			if prop.comment:
				comment += ", " + prop.comment
			row = [
				int(optName in self.values),
				optName,
				str(self.values.get(optName, "")),
				comment,
			]
			treev.insert("", "end", values=row, iid=optName) # iid should be rowId
			# adjust column's width if necessary to fit each value
			for col_i, value in enumerate(row):
				value = str(value)
				if col_i == 3:
					value = value.zfill(20) # to reserve window width, because it's hard to resize it later
				col_w = tkFont.Font().measure(value)
				if treev.column(cols[col_i], width=None) < col_w:
					treev.column(cols[col_i], width=col_w)
		###########
		frame = tix.Frame(dialog)
		###
		def okClicked():
			for optName in options:
				enable = bool(int(treev.set(optName, "#1")))
				if not enable:
					if optName in self.values:
						del self.values[optName]
					continue
				rawValue = treev.set(optName, self.valueCol)
				prop = optionsProp[optName]
				value, isValid = prop.evaluate(rawValue)
				if not isValid:
					log.error("invalid option value %s = %s" % (optName, rawValue))
					continue
				self.values[optName] = value
			dialog.destroy()
		button = ttk.Button(
			frame,
			text="OK",
			command=okClicked,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		button.pack(side="right")
		###
		frame.pack(fill="x")
		###
		# x, y, w, h = decodeGeometry(dialog.geometry())
		w, h = 380, 250
		# w and h are rough estimated width and height of `dialog`
		px, py, pw, ph = decodeGeometry(self.winfo_toplevel().geometry())
		# move dialog without changing the size
		dialog.geometry(encodeLocation(
			px + pw//2 - w//2,
			py + ph//2 - h//2,
		))
		dialog.focus()


class UI(tix.Frame, UIBase):
	def __init__(self, path="", **options):
		self.glos = Glossary(ui=self)
		self.pref = {}
		self.pref_load(**options)
		#############################################
		rootWin = self.rootWin = tix.Tk()
		# a hack that hides the window until we move it to the center of screen
		if os.sep == "\\": # Windows
			rootWin.attributes('-alpha', 0.0)
		else: # Linux
			rootWin.withdraw()
		tix.Frame.__init__(self, rootWin)
		rootWin.title("PyGlossary (Tkinter)")
		rootWin.resizable(True, False)
		########
		set_window_icon(rootWin)
		rootWin.bind('<Escape>', lambda e: rootWin.quit())
		########
		self.pack(fill="x")
		# rootWin.bind("<Configure>", self.resized)
		######################
		self.glos = Glossary(ui=self)
		self.pref = {}
		self.pref_load()
		self.pathI = ""
		self.pathO = ""
		self.fcd_dir = join(homeDir, "Desktop")
		######################
		vpaned = ttk.PanedWindow(self, orient=tk.VERTICAL)
		notebook = tix.NoteBook(vpaned)
		notebook.add("tab1", label="Convert", underline=0)
		notebook.add("tab2", label="Reverse", underline=0)
		convertFrame = tix.Frame(notebook.tab1)
		######################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="Read from format")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			frame,
			comboVar,
			None, # default
			*Glossary.readDesc,
		)
		combo.pack(side="left")
		comboVar.trace("w", self.inputComboChanged)
		self.combobox_i = comboVar
		##
		self.readOptions = {} # type: Dict[str, Any]
		self.writeOptions = {} # type: Dict[str, Any]
		##
		self.readOptionsButton = FormatOptionsButton(
			"Read",
			self.readOptions,
			self.combobox_i,
			master=frame,
		)
		##
		frame.pack(fill="x")
		###################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="  Path:")
		label.pack(side="left")
		##
		entry = tix.Entry(frame)
		entry.pack(side="left", fill="x", expand=True)
		entry.bind_all("<KeyPress>", self.entry_changed)
		self.entry_i = entry
		##
		button = ttk.Button(
			frame,
			text="Browse",
			command=self.browse_i,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.pack(side="left")
		##
		frame.pack(fill="x")
		######################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="Write to format    ")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			frame,
			comboVar,
			None, # default
			*Glossary.writeDesc,
		)
		combo.pack(side="left")
		comboVar.trace("w", self.outputComboChanged)
		self.combobox_o = comboVar
		##
		self.writeOptionsButton = FormatOptionsButton(
			"Write",
			self.writeOptions,
			self.combobox_o,
			master=frame,
		)
		##
		frame.pack(fill="x")
		###################
		frame = tix.Frame(convertFrame)
		##
		label = ttk.Label(frame, text="  Path:")
		label.pack(side="left")
		##
		entry = tix.Entry(frame)
		entry.pack(side="left", fill="x", expand=True)
		# entry.bind_all("<KeyPress>", self.entry_changed)
		self.entry_o = entry
		##
		button = ttk.Button(
			frame,
			text="Browse",
			command=self.browse_o,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.pack(side="left")
		##
		frame.pack(fill="x")
		#######
		frame = tix.Frame(convertFrame)
		label = ttk.Label(frame, text=" "*15)
		label.pack(
			side="left",
			fill="x",
			expand=True,
		)
		button = ttk.Button(
			frame,
			text="Convert",
			command=self.convert,
			# bg="#00e000",
			# activebackground="#22f022",
		)
		button.pack(
			side="left",
			fill="x",
			expand=True,
		)
		###
		frame.pack(fill="x")
		######
		convertFrame.pack(fill="x")
		vpaned.add(notebook)
		#################
		console = tix.Text(vpaned, height=15, background="#000000")
		# self.consoleH = 15
		# sbar = Tix.Scrollbar(
		#	vpaned,
		#	orien=Tix.VERTICAL,
		#	command=console.yview
		# )
		# sbar.grid ( row=0, column=1)
		# console["yscrollcommand"] = sbar.set
		# console.grid()
		console.pack(fill="both", expand=True)
		log.addHandler(
			TkTextLogHandler(console),
		)
		console.insert("end", "Console:\n")
		####
		vpaned.add(console)
		vpaned.pack(fill="both", expand=True)
		self.console = console
		##################
		frame2 = tix.Frame(self)
		clearB = ttk.Button(
			frame2,
			text="Clear",
			command=self.console_clear,
			# bg="black",
			# fg="#ffff00",
			# activebackground="#333333",
			# activeforeground="#ffff00",
		)
		clearB.pack(side="left")
		####
		label = ttk.Label(frame2, text="Verbosity")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			frame2,
			comboVar,
			log.getVerbosity(), # default
			0, 1, 2, 3, 4,
		)
		comboVar.trace("w", self.verbosityChanged)
		combo.pack(side="left")
		self.verbosityCombo = comboVar
		#####
		pbar = ProgressBar(frame2, width=400)
		pbar.pack(side="left", fill="x", expand=True)
		self.pbar = pbar
		frame2.pack(fill="x")
		self.progressTitle = ""
		#############
		# vpaned.grid()
		# bottomFrame.grid()
		# self.grid()
		#####################
		# lbox = Tix.Listbox(convertFrame)
		# lbox.insert(0, "aaaaaaaa", "bbbbbbbbbbbbbbbbbbbb")
		# lbox.pack(fill="x")
		##############
		frame3 = tix.Frame(self)
		aboutB = ttk.Button(
			frame3,
			text="About",
			command=self.about_clicked,
			# bg="#e000e0",
			# activebackground="#f030f0",
		)
		aboutB.pack(side="right")
		closeB = ttk.Button(
			frame3,
			text="Close",
			command=rootWin.quit,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		closeB.pack(side="right")
		frame3.pack(fill="x")
		# __________________________ Reverse Tab __________________________ #
		revFrame = tix.Frame(notebook.tab2)
		revFrame.pack(fill="x")
		######################
		frame = tix.Frame(revFrame)
		##
		label = ttk.Label(frame, text="Read from format")
		label.pack(side="left")
		##
		comboVar = tk.StringVar()
		combo = ttk.OptionMenu(
			frame,
			comboVar,
			None, # default
			*Glossary.readDesc,
		)
		combo.pack(side="left")
		self.combobox_r_i = comboVar
		##
		frame.pack(fill="x")
		###################
		frame = tix.Frame(revFrame)
		##
		label = ttk.Label(frame, text="  Path:")
		label.pack(side="left")
		##
		entry = tix.Entry(frame)
		entry.pack(side="left", fill="x", expand=True)
		# entry.bind_all("<KeyPress>", self.entry_r_i_changed)
		self.entry_r_i = entry
		##
		button = ttk.Button(
			frame,
			text="Browse",
			command=self.r_browse_i,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.pack(side="left")
		##
		button = ttk.Button(
			frame,
			text="Load",
			command=self.r_load,
			# bg="#7777ff",
		)
		button.pack(side="left")
		###
		frame.pack(fill="x")
		###################
		frame = tix.Frame(revFrame)
		##
		label = ttk.Label(frame, text="Output Tabfile")
		label.pack(side="left")
		###
		entry = tix.Entry(frame)
		entry.pack(side="left", fill="x", expand=True)
		# entry.bind_all("<KeyPress>", self.entry_r_i_changed)
		self.entry_r_o = entry
		##
		button = ttk.Button(
			frame,
			text="Browse",
			command=self.r_browse_o,
			# bg="#f0f000",
			# activebackground="#f6f622",
		)
		button.pack(side="left")
		##
		frame.pack(fill="x")
		#############
		centerWindow(rootWin)
		# show the window again
		if os.sep == "\\": # Windows
			rootWin.attributes('-alpha', 1.0)
		else: # Linux
			rootWin.deiconify()
		##############################
		if path:
			self.entry_i.insert(0, path)
			self.entry_changed()
			self.load()

	def verbosityChanged(self, index, value, op):
		log.setVerbosity(
			int(self.verbosityCombo.get())
		)

	def about_clicked(self):
		about = tix.Toplevel(width=600)  # bg="#0f0" does not work
		about.title("About PyGlossary")
		about.resizable(width=False, height=False)
		set_window_icon(about)
		about.bind('<Escape>', lambda e: about.destroy())
		###
		msg1 = tix.Message(
			about,
			width=350,
			text="PyGlossary %s (Tkinter)" % VERSION,
			font=("DejaVu Sans", 13, "bold"),
		)
		msg1.pack(fill="x", expand=True)
		###
		msg2 = tix.Message(
			about,
			width=350,
			text=aboutText,
			font=("DejaVu Sans", 9, "bold"),
			justify=tix.CENTER,
		)
		msg2.pack(fill="x", expand=True)
		###
		msg3 = tix.Message(
			about,
			width=350,
			text=homePage,
			font=("DejaVu Sans", 8, "bold"),
			fg="#3333ff",
		)
		msg3.pack(fill="x", expand=True)
		###
		msg4 = tix.Message(
			about,
			width=350,
			text="Install Gtk3+PyGI to have a better interface!",
			font=("DejaVu Sans", 8, "bold"),
			fg="#00aa00",
		)
		msg4.pack(fill="x", expand=True)
		###########
		frame = tix.Frame(about)
		###
		button = ttk.Button(
			frame,
			text="Close",
			command=about.destroy,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		button.pack(side="right")
		###
		button = ttk.Button(
			frame,
			text="License",
			command=self.about_license_clicked,
			# bg="#00e000",
			# activebackground="#22f022",
		)
		button.pack(side="right")
		###
		button = ttk.Button(
			frame,
			text="Credits",
			command=self.about_credits_clicked,
			# bg="#0000ff",
			# activebackground="#5050ff",
		)
		button.pack(side="right")
		###
		frame.pack(fill="x")

	def about_credits_clicked(self):
		about = tix.Toplevel()  # bg="#0f0" does not work
		about.title("Credits")
		about.resizable(width=False, height=False)
		set_window_icon(about)
		about.bind('<Escape>', lambda e: about.destroy())
		###
		msg1 = tix.Message(
			about,
			width=500,
			text="\n".join(authors),
			font=("DejaVu Sans", 9, "bold"),
		)
		msg1.pack(fill="x", expand=True)
		###########
		frame = tix.Frame(about)
		closeB = ttk.Button(
			frame,
			text="Close",
			command=about.destroy,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		closeB.pack(side="right")
		frame.pack(fill="x")

	def about_license_clicked(self):
		about = tix.Toplevel()  # bg="#0f0" does not work
		about.title("License")
		about.resizable(width=False, height=False)
		set_window_icon(about)
		about.bind('<Escape>', lambda e: about.destroy())
		###
		msg1 = tix.Message(
			about,
			width=420,
			text=licenseText,
			font=("DejaVu Sans", 9, "bold"),
		)
		msg1.pack(fill="x", expand=True)
		###########
		frame = tix.Frame(about)
		closeB = ttk.Button(
			frame,
			text="Close",
			command=about.destroy,
			# bg="#ff0000",
			# activebackground="#ff5050",
		)
		closeB.pack(side="right")
		frame.pack(fill="x")

	def resized(self, event):
		dh = self.rootWin.winfo_height() - self.winfo_height()
		# log.debug(dh, self.consoleH)
		# if dh > 20:
		#	self.consoleH += 1
		#	self.console["height"] = self.consoleH
		#	self.console["width"] = int(self.console["width"]) + 1
		#	self.console.grid()
		# for x in dir(self):
		#	if "info" in x:
		#		log.debug(x)

	def inputComboChanged(self, *args):
		formatD = self.combobox_i.get()
		if not formatD:
			return
		self.readOptions.clear() # reset the options, DO NOT re-assign
		format = Glossary.descFormat[formatD]
		options = Glossary.formatsReadOptions[format]
		if options:
			self.readOptionsButton.pack(side="right")
		else:
			self.readOptionsButton.pack_forget()

	def outputComboChanged(self, *args):
		# log.debug(self.combobox_o.get())
		formatD = self.combobox_o.get()
		if not formatD:
			return
		self.writeOptions.clear() # reset the options, DO NOT re-assign
		format = Glossary.descFormat[formatD]
		options = Glossary.formatsWriteOptions[format]
		if options:
			self.writeOptionsButton.pack(side="right")
		else:
			self.writeOptionsButton.pack_forget()

		if not self.pref["ui_autoSetOutputFileName"]:  # and format is None:
			return

		pathI = self.entry_i.get()
		pathO = self.entry_o.get()
		formatOD = self.combobox_o.get()

		if formatOD is None:
			return
		if pathO:
			return
		if "." not in pathI:
			return

		extO = Glossary.descExt[formatOD]
		pathO = "".join(os.path.splitext(pathI)[:-1])+extO
		# self.entry_o.delete(0, "end")
		self.entry_o.insert(0, pathO)

	def entry_changed(self, event=None):
		# log.debug("entry_changed")
		# char = event.keysym
		pathI = self.entry_i.get()
		if self.pathI != pathI:
			formatD = self.combobox_i.get()
			if pathI.startswith("file://"):
				pathI = urlToPath(pathI)
				self.entry_i.delete(0, "end")
				self.entry_i.insert(0, pathI)
			if self.pref["ui_autoSetFormat"]:
				ext = os.path.splitext(pathI)[-1].lower()
				if ext in (".gz", ".bz2", ".zip"):
					ext = os.path.splitext(pathI[:-len(ext)])[-1].lower()
				for i in range(len(Glossary.readExt)):
					if ext in Glossary.readExt[i]:
						self.combobox_i.set(Glossary.readDesc[i])
						break
			if self.pref["ui_autoSetOutputFileName"]:
				# pathI = self.entry_i.get()
				formatOD = self.combobox_o.get()
				pathO = self.entry_o.get()
				if formatOD and not pathO and "." in pathI:
					extO = Glossary.descExt[formatOD]
					pathO = "".join(os.path.splitext(pathI)[:-1]) + extO
					self.entry_o.delete(0, "end")
					self.entry_o.insert(0, pathO)
			self.pathI = pathI
		##############################################
		pathO = self.entry_o.get()
		if self.pathO != pathO:
			formatD = self.combobox_o.get()
			if pathO.startswith("file://"):
				pathO = urlToPath(pathO)
				self.entry_o.delete(0, "end")
				self.entry_o.insert(0, pathO)
			if self.pref["ui_autoSetFormat"]:
				ext = os.path.splitext(pathO)[-1].lower()
				if ext in (".gz", ".bz2", ".zip"):
					ext = os.path.splitext(pathO[:-len(ext)])[-1].lower()
				for i in range(len(Glossary.writeExt)):
					if ext in Glossary.writeExt[i]:
						self.combobox_o.set(Glossary.writeDesc[i])
						break
			self.pathO = pathO

	def browse_i(self):
		path = filedialog.askopenfilename(initialdir=self.fcd_dir)
		if path:
			self.entry_i.delete(0, "end")
			self.entry_i.insert(0, path)
			self.entry_changed()
			self.fcd_dir = os.path.dirname(path)  # FIXME

	def browse_o(self):
		path = filedialog.asksaveasfilename()
		if path:
			self.entry_o.delete(0, "end")
			self.entry_o.insert(0, path)
			self.entry_changed()
			self.fcd_dir = os.path.dirname(path)  # FIXME

	def convert(self):
		inPath = self.entry_i.get()
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormatDesc = self.combobox_i.get()
		if not inFormatDesc:
			# log.critical("Input format is empty!");return
			inFormat = ""
		else:
			inFormat = Glossary.descFormat[inFormatDesc]

		outPath = self.entry_o.get()
		if not outPath:
			log.critical("Output file path is empty!")
			return
		outFormatDesc = self.combobox_o.get()
		if not outFormatDesc:
			log.critical("Output format is empty!")
			return
		outFormat = Glossary.descFormat[outFormatDesc]

		finalOutputFile = self.glos.convert(
			inPath,
			inputFormat=inFormat,
			outputFilename=outPath,
			outputFormat=outFormat,
			readOptions=self.readOptions,
			writeOptions=self.writeOptions,
		)
		# if finalOutputFile:
			# self.status("Convert finished")
		# else:
			# self.status("Convert failed")
		return bool(finalOutputFile)

	def run(self, editPath=None, readOptions=None):
		if readOptions is None:
			readOptions = {}
		# editPath and readOptions are for DB Editor
		# which is not implemented
		self.mainloop()

	def progressInit(self, title):
		self.progressTitle = title

	def progress(self, rat, text=""):
		if not text:
			text = "%%%d" % (rat*100)
		text += " - %s" % self.progressTitle
		self.pbar.updateProgress(rat*100, None, text)
		# self.pbar.value = rat*100
		# self.pbar.update()
		self.rootWin.update()

	def console_clear(self, event=None):
		self.console.delete("1.0", "end")
		self.console.insert("end", "Console:\n")

	def r_browse_i(self):
		pass

	def r_browse_o(self):
		pass

	def r_load(self):
		pass


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		path = sys.argv[1]
	else:
		path = ""
	ui = UI(path)
	ui.run()
