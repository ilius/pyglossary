# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2008-2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from os.path import abspath, isfile
from typing import Any

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

from pyglossary import core
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import (
	UIBase,
	aboutText,
	authors,
	licenseText,
	logo,
)
from pyglossary.ui.version import getVersion

from .about import AboutWidget
from .browse import BrowseButton
from .format_widgets import InputFormatBox, OutputFormatBox
from .general_options import GeneralOptionsButton
from .log_handler import GtkSingleTextviewLogHandler
from .utils import (
	HBox,
	VBox,
	getWorkAreaSize,
	gtk_event_iteration_loop,
	imageFromFile,
	pack,
	rgba_parse,
)

# from gi.repository import GdkPixbuf

log = logging.getLogger("pyglossary")

_ = str  # later replace with translator function


# GTK 4 has removed the GtkContainer::border-width property
# (together with the rest of GtkContainer).
# Use other means to influence the spacing of your containers,
# such as the CSS margin and padding properties on child widgets,
# or the CSS border-spacing property on containers.


class MainWindow(gtk.ApplicationWindow):
	# @property
	# def config(self):
	# 	return self.ui.config

	css = """
textview.console text {
	background-color: rgb(0, 0, 0);
}

check {
	min-width: 1.25em;
	min-height: 1.25em;
}

.margin_03 {
	margin-top: 0.5em;
	margin-right: 0.5em;
	margin-bottom: 0.5em;
	margin-left: 0.5em;
}

.margin_05 {
	margin-top: 0.5em;
	margin-right: 0.5em;
	margin-bottom: 0.5em;
	margin-left: 0.5em;
}

.margin_10 {
	margin-top: 1em;
	margin-right: 1em;
	margin-bottom: 1em;
	margin-left: 1em;
}
	"""

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
		progressbar: bool = True,
		**kwargs,
	) -> None:
		self.app = app
		self.ui = ui
		#####
		gtk.ApplicationWindow.__init__(self, application=app, **kwargs)
		self.set_title("PyGlossary (Gtk3)")
		self.progressbarEnable = progressbar
		#####
		self.vbox = VBox()
		self.set_child(self.vbox)
		#####
		screenW, screenH = getWorkAreaSize(self)
		winSize = min(800, screenW - 50, screenH - 50)
		self.set_default_size(winSize, winSize)
		#####
		# gesture = gtk.GestureClick.new()
		# gesture.connect("pressed", self.onButtonPress)
		# self.add_controller(gesture)
		###
		ckey = gtk.EventControllerKey()
		ckey.connect("key-pressed", self.onKeyPress)
		self.add_controller(ckey)
		####
		self.connect("close-request", self.onCloseRequest)
		####
		self.pages = []
		# self.statusNewId = 0
		# self.statusMsgDict = {}## message -> id
		#####
		self.convertOptions = {}
		#####
		self.styleProvider = gtk.CssProvider()
		gtk.StyleContext.add_provider_for_display(
			gdk.Display.get_default(),
			self.styleProvider,
			gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		# gtk.StyleContext.add_provider_for_screen(
		# 	gdk.Screen.get_default(),
		# 	self.styleProvider,
		# 	gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		# )
		self.styleProvider.load_from_data(self.css, len(self.css.encode("utf-8")))
		#####
		self.assert_quit = False
		self.path = ""
		# ____________________ Tab 1 - Convert ____________________ #
		labelSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		buttonSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		vbox = VBox(spacing=5)
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
		self.convertInputFormatCombo = InputFormatBox(self.app, parent=self)
		buttonSizeGroup.add_widget(self.convertInputFormatCombo.optionsButton)
		pack(hbox, self.convertInputFormatCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.convertInputFormatCombo.dependsButton)
		pack(hbox, self.convertInputFormatCombo.optionsButton)
		pack(vbox, hbox)
		#####
		hbox = HBox()
		hbox.get_style_context().add_class("margin_03")
		pack(vbox, hbox)
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
		self.convertOutputFormatCombo = OutputFormatBox(self.app, parent=self)
		buttonSizeGroup.add_widget(self.convertOutputFormatCombo.optionsButton)
		pack(hbox, self.convertOutputFormatCombo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.convertOutputFormatCombo.dependsButton)
		pack(hbox, self.convertOutputFormatCombo.optionsButton)
		pack(vbox, hbox)
		#####
		hbox = HBox(spacing=10)
		hbox.get_style_context().add_class("margin_03")
		label = gtk.Label(label="")
		pack(hbox, label, expand=True)
		##
		button = GeneralOptionsButton(self)
		button.set_size_request(300, 40)
		pack(hbox, button)
		##
		self.convertButton = gtk.Button()
		self.convertButton.set_label("Convert")
		self.convertButton.connect("clicked", self.convertClicked)
		self.convertButton.set_size_request(300, 40)
		pack(hbox, self.convertButton)
		##
		pack(vbox, hbox)
		#####
		self.convertConsoleTextview = textview = gtk.TextView()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.set_child(textview)
		pack(vbox, swin, expand=True)
		######
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
		#####
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
			vb.show()
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
		##########
		textview.get_style_context().add_class("console")
		handler = GtkSingleTextviewLogHandler(self, textview)
		log.addHandler(handler)
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
		self.progressTitle = ""
		self.progressBar = pbar = gtk.ProgressBar()
		pbar.set_fraction(0)
		# pbar.set_text(_("Progress Bar"))
		# pbar.get_style_context()
		# pbar.set_property("height-request", 20)
		pack(self.vbox, pbar)
		############
		hbox = HBox(spacing=5)
		clearButton = gtk.Button(
			# always_show_image=True,
			label=_("Clear"),
			# icon_name="clear",
		)
		clearButton.show()
		# image = gtk.Image()
		# image.set_icon_name(...)
		# clearButton.add(image)
		clearButton.connect("clicked", self.consoleClearButtonClicked)
		clearButton.set_tooltip_text("Clear Console")
		pack(hbox, clearButton)
		####
		# hbox.sepLabel1 = gtk.Label(label="")
		# pack(hbox, hbox.sepLabel1, 1, 1)
		######
		hbox.verbosityLabel = gtk.Label(label=_("Verbosity:"))
		pack(hbox, hbox.verbosityLabel)
		##
		self.verbosityCombo = combo = gtk.ComboBoxText()
		for level, levelName in enumerate(log.levelNamesCap):
			combo.append_text(f"{level} - {_(levelName)}")
		combo.set_active(log.getVerbosity())
		combo.connect("changed", self.verbosityComboChanged)
		pack(hbox, combo)
		####
		# hbox.sepLabel2 = gtk.Label(label="")
		# pack(hbox, hbox.sepLabel2, 1, 1)
		####
		self.statusBar = gtk.Statusbar()
		pack(hbox, self.statusBar, 1, 1)
		####
		# ResizeButton does not work in Gtk 4.0
		# hbox.resizeButton = ResizeButton(self)
		# pack(hbox, hbox.resizeButton)
		######
		pack(self.vbox, hbox)
		# ____________________________________________________________ #
		self.vbox.show()
		notebook.set_current_page(0)  # Convert tab
		self.convertInputFormatCombo.dependsButton.hide()
		self.convertOutputFormatCombo.dependsButton.hide()
		self.convertInputFormatCombo.optionsButton.hide()
		self.convertOutputFormatCombo.optionsButton.hide()
		########
		self.status("Select input file")

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
			self.convertInputFormatCombo.setActive(inputFormat)
		if outputFormat:
			self.convertOutputFormatCombo.setActive(outputFormat)

		if reverse:
			log.error("Gtk interface does not support Reverse feature")

		if readOptions:
			self.convertInputFormatCombo.setOptionsValues(readOptions)
		if writeOptions:
			self.convertOutputFormatCombo.setOptionsValues(writeOptions)

		self.convertOptions = convertOptions
		if convertOptions:
			log.debug(f"Using {convertOptions=}")

		self._glossarySetAttrs = glossarySetAttrs or {}
		self.present()

	def exitApp(self) -> None:
		self.destroy()
		# unlike Gtk3, no need for sys.exit or gtk.main_quit (which does not exist)

	def onCloseRequest(self, _widget: Any) -> None:
		self.exitApp()

	def onKeyPress(
		self,
		_ckey: gtk.EventControllerKey,
		keyval: int,
		_keycode: int,
		_state: gdk.ModifierType,
	) -> None:
		if keyval == gdk.KEY_Escape:
			self.exitApp()

	def onButtonPress(
		self,
		gesture: gtk.GestureClick,
		_n_press: Any,
		_x: int,
		_y: int,
	) -> None:
		print(f"MainWindow.onButtonPress: {gesture}")

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
		inFormat = self.convertInputFormatCombo.getActive()

		outPath = self.convertOutputEntry.get_text()
		if not outPath:
			log.critical("Output file path is empty!")
			return
		outFormat = self.convertOutputFormatCombo.getActive()

		gtk_event_iteration_loop()

		self.convertButton.set_sensitive(False)
		self.progressTitle = "Converting"
		readOptions = self.convertInputFormatCombo.optionsValues
		writeOptions = self.convertOutputFormatCombo.optionsValues

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
		inFormat = self.convertInputFormatCombo.getActive()
		if inPath.startswith("file://"):
			inPath = urlToPath(inPath)
			self.convertInputEntry.set_text(inPath)

		if self.config["ui_autoSetFormat"] and not inFormat:
			try:
				inputArgs = Glossary.detectInputFormat(inPath)
			except Error:
				pass
			else:
				self.convertInputFormatCombo.setActive(inputArgs.formatName)

		if not isfile(inPath):
			return

		self.status("Select output file")

	def convertOutputEntryChanged(self, _widget: Any = None) -> None:
		outPath = self.convertOutputEntry.get_text()
		outFormat = self.convertOutputFormatCombo.getActive()
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
				self.convertOutputFormatCombo.setActive(outFormat)

		if outFormat:
			self.status('Press "Convert"')
		else:
			self.status("Select output format")

	def progressInit(self, title: str) -> None:
		self.progressTitle = title

	def progress(self, ratio: float, text: str = "") -> None:
		if not text:
			text = "%" + str(int(ratio * 100))
		text += " - " + self.progressTitle
		self.progressBar.set_fraction(ratio)
		# self.progressBar.set_text(text)  # not working
		self.status(text)
		gtk_event_iteration_loop()
