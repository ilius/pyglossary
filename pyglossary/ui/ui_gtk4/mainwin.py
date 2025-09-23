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
from os.path import abspath, isfile
from typing import TYPE_CHECKING, Any

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

from pyglossary.core import homePage
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import (
	aboutText,
	authors,
	licenseText,
	logo,
)
from pyglossary.ui.version import getVersion

from .about import AboutWidget
from .console import ConvertConsole
from .file_widgets import InputFileBox, OutputFileBox
from .format_widgets import InputFormatBox, OutputFormatBox
from .general_options import GeneralOptionsButton
from .utils import (
	HBox,
	VBox,
	getWorkAreaSize,
	gtk_event_iteration_loop,
	hasLightTheme,
	pack,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.config_type import ConfigType
	from pyglossary.ui_type import UIType

__all__ = ["MainWindow"]


log = logging.getLogger("pyglossary")

_ = str  # later replace with translator function


# GTK 4 has removed the GtkContainer::border-width property
# (together with the rest of GtkContainer).
# Use other means to influence the spacing of your containers,
# such as the CSS margin and padding properties on child widgets,
# or the CSS border-spacing property on containers.


class ConvertStatusBox(gtk.Box):
	def __init__(
		self,
		clearClicked: Callable,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		self.statusNewId = 0
		# https://gitlab.gnome.org/GNOME/gtk/-/issues/4205
		clearButton = gtk.Button(
			label=_("Clear"),
			# icon_name="gtk-clear",
		)
		clearButton.show()
		clearButton.connect("clicked", clearClicked)
		clearButton.set_tooltip_text("Clear Console")
		pack(self, clearButton)
		####
		# pack(hbox, gtk.Label(), 1, 1)
		######
		self.verbosityLabel = gtk.Label(label=_("Verbosity:"))
		pack(self, self.verbosityLabel)
		##
		self.verbosityCombo = combo = gtk.ComboBoxText()
		for level, levelName in enumerate(log.levelNamesCap):
			combo.append_text(f"{level} - {_(levelName)}")
		combo.set_active(log.getVerbosity())
		combo.connect("changed", self.verbosityComboChanged)
		pack(self, combo)
		####
		# pack(hbox, gtk.Label(), 1, 1)
		####
		self.statusBar = gtk.Statusbar()
		pack(self, self.statusBar, 1, 1)
		####
		# ResizeButton does not work in Gtk 4.0

	def status(self, msg: str) -> None:
		self.statusBar.push(self.statusNewId % 4294967295, msg)
		self.statusNewId += 1

	def verbosityComboChanged(self, _widget: gtk.Widget | None = None) -> None:
		verbosity = self.verbosityCombo.get_active()
		# or int(self.verbosityCombo.get_active_text())
		log.setVerbosity(verbosity)


class MainWindow(gtk.ApplicationWindow):
	# @property
	# def config(self):
	# 	return self.ui.config

	css = """
check {
	min-width: 1.25em;
	min-height: 1.25em;
}

progressbar progress, trough {min-height: 0.6em;}

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
		self.statusBox.status(msg)

	def __init__(
		self,
		ui: UIType,
		app: gtk.Application,
		progressBar: gtk.ProgressBar | None,
		**kwargs: Any,
	) -> None:
		self.app = app
		self.ui = ui
		#####
		gtk.ApplicationWindow.__init__(self, application=app, **kwargs)
		#####
		self.lightTheme = hasLightTheme(self)
		# this may not be needed in most themes,
		# but just to be sure the colors are not messed up
		if self.lightTheme:
			self.css += "textview.console text {background-color: rgb(255, 255, 255);}"
		else:
			self.css += "textview.console text {background-color: rgb(0, 0, 0);}"
		#####
		self.set_title("PyGlossary (Gtk4)")
		self.progressBar = progressBar
		#####
		self.vbox = VBox()
		self.set_child(self.vbox)
		#####
		screenW, screenH = getWorkAreaSize(self)
		winSize = min(800, screenW - 50, screenH - 50)
		self.set_default_size(winSize, winSize)
		#####
		ckey = gtk.EventControllerKey()
		ckey.connect("key-pressed", self.onKeyPress)
		self.add_controller(ckey)
		####
		self.connect("close-request", self.onCloseRequest)
		####
		self.pages = []
		self.convertOptions = {}
		#####
		self.styleProvider = gtk.CssProvider()
		gtk.StyleContext.add_provider_for_display(
			gdk.Display.get_default(),
			self.styleProvider,
			gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		self.styleProvider.load_from_data(self.css)
		#####
		self.assert_quit = False  # FIXME: not used
		# ____________________ Tab 1 - Convert ____________________ #
		labelSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		buttonSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		self.inOutBoxes: list[gtk.Box] = []
		####
		page = VBox(spacing=5)
		page.label = _("Convert")
		page.icon = ""  # "*.png"
		self.pages.append(page)
		######
		self.inputFileBox = InputFileBox(
			entryChanged=self.inputFileEntryChanged,
			labelSizeGroup=labelSizeGroup,
			buttonSizeGroup=buttonSizeGroup,
		)
		self.inOutBoxes.append(self.inputFileBox)
		pack(page, self.inputFileBox)
		###
		self.inputFormatBox = InputFormatBox(
			self.app,
			parent=self,
			labelSizeGroup=labelSizeGroup,
			buttonSizeGroup=buttonSizeGroup,
		)
		self.inOutBoxes.append(self.inputFormatBox)
		pack(page, self.inputFormatBox)
		#####
		hbox = HBox()
		hbox.get_style_context().add_class("margin_03")
		pack(page, hbox)
		#####
		self.outputFileBox = OutputFileBox(
			entryChanged=self.outputFileEntryChanged,
			labelSizeGroup=labelSizeGroup,
			buttonSizeGroup=buttonSizeGroup,
		)
		self.inOutBoxes.append(self.outputFileBox)
		pack(page, self.outputFileBox)
		###
		self.outputFormatBox = OutputFormatBox(
			self.app,
			parent=self,
			labelSizeGroup=labelSizeGroup,
			buttonSizeGroup=buttonSizeGroup,
		)
		self.inOutBoxes.append(self.outputFormatBox)
		pack(page, self.outputFormatBox)
		#####
		hbox = HBox(spacing=10)
		hbox.get_style_context().add_class("margin_03")
		pack(hbox, gtk.Label(), expand=True)
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
		self.inOutBoxes.append(hbox)
		pack(page, hbox)
		#####
		self.convertConsole = ConvertConsole(
			self,
			lightTheme=self.lightTheme,
		)
		log.addHandler(self.convertConsole.handler)
		pack(page, self.convertConsole, expand=True)
		######
		self.progressTitle = ""
		if progressBar:
			pack(page, progressBar)
		######
		self.statusBox = ConvertStatusBox(
			clearClicked=self.consoleClearButtonClicked,
		)
		pack(page, self.statusBox)
		# ____________________________________ ____________________ #
		self.pages.append(self.makeAboutWidget())
		pack(self.vbox, self.setupNotebook(self.pages), 1, 1)
		######
		self.vbox.show()
		self.status("Select input file")

	def makeAboutWidget(self) -> gtk.Widget:
		about = AboutWidget(
			logo=logo,
			header=f"PyGlossary\nVersion {getVersion()}",
			# about=summary,
			about=f'{aboutText}\n<a href="{homePage}">{homePage}</a>',
			authors="\n".join(authors),
			license_text=licenseText,
		)
		about.label = _("About")
		about.icon = ""  # "dialog-information-22.png"
		return about

	def setupNotebook(self, pages: list[gtk.Widget]) -> gtk.Notebook:
		notebook = gtk.Notebook()
		####
		for page in pages:
			tabWidget = gtk.Label(label=page.label, use_underline=True)
			# if vbox.icon:
			# 	tabWidget = VBox(spacing=3)
			# 	pack(tabWidget, imageFromFile(vbox.icon))
			# 	pack(tabWidget, label)
			# 	tabWidget.show()
			notebook.append_page(page, tabWidget)
			try:
				notebook.set_tab_reorderable(page, True)
			except AttributeError:
				pass
		return notebook

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
		self.config = config or {}

		if inputFilename:
			self.inputFileBox.set_text(abspath(inputFilename))
		if outputFilename:
			self.outputFileBox.set_text(abspath(outputFilename))

		if inputFormat:
			self.inputFormatBox.setActive(inputFormat)
		if outputFormat:
			self.outputFormatBox.setActive(outputFormat)

		if reverse:
			log.error("Gtk interface does not support Reverse feature")

		if readOptions:
			self.inputFormatBox.setOptionsValues(readOptions)
		if writeOptions:
			self.outputFormatBox.setOptionsValues(writeOptions)

		self.convertOptions = convertOptions
		if convertOptions:
			log.debug(f"Using {convertOptions=}")

		self._glossarySetAttrs = glossarySetAttrs or {}
		self.present()

	def exitApp(self) -> None:
		self.destroy()
		# unlike Gtk3, no need for sys.exit or gtk.main_quit (which does not exist)

	def onCloseRequest(self, _widget: gtk.Widget) -> None:
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
		_n_press: int,
		_x: int,
		_y: int,
	) -> None:
		print(f"MainWindow.onButtonPress: {gesture}")

	def consoleClearButtonClicked(self, _widget: gtk.Widget = None) -> None:
		self.convertConsole.set_text("")

	def setInOutBoxesSensivive(self, sensitive: bool) -> None:
		for hbox in self.inOutBoxes:
			hbox.set_sensitive(sensitive)

	def convertClicked(self, _widget: gtk.Widget | None = None) -> None:
		inPath = self.inputFileBox.get_text()
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormat = self.inputFormatBox.getActive()

		outPath = self.outputFileBox.get_text()
		if not outPath:
			log.critical("Output file path is empty!")
			return
		outFormat = self.outputFormatBox.getActive()

		self.status("Converting...")
		self.setInOutBoxesSensivive(False)
		gtk_event_iteration_loop()

		self.progressTitle = "Converting"
		readOptions = self.inputFormatBox.optionsValues
		writeOptions = self.outputFormatBox.optionsValues
		glos = Glossary(ui=self.ui)
		glos.config = self.config
		glos.progressbar = self.progressBar is not None

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
			self.setInOutBoxesSensivive(True)
			self.assert_quit = False
			self.progressTitle = ""

	def inputFileEntryChanged(self, entry: gtk.Entry) -> None:
		inPath = entry.get_text()
		inFormat = self.inputFormatBox.getActive()
		if inPath.startswith("file://"):
			inPath = urlToPath(inPath)
			entry.set_text(inPath)

		if self.config["ui_autoSetFormat"] and not inFormat:
			try:
				inputArgs = Glossary.detectInputFormat(inPath)
			except Error:
				pass
			else:
				self.inputFormatBox.setActive(inputArgs.formatName)

		if not isfile(inPath):
			return

		self.status("Select output file")

	def outputFileEntryChanged(self, entry: gtk.Entry) -> None:
		outPath = entry.get_text()
		outFormat = self.outputFormatBox.getActive()
		if not outPath:
			return
		if outPath.startswith("file://"):
			outPath = urlToPath(outPath)
			entry.set_text(outPath)

		if self.config["ui_autoSetFormat"] and not outFormat:
			try:
				outputArgs = Glossary.detectOutputFormat(
					filename=outPath,
					inputFilename=self.inputFileBox.get_text(),
				)
			except Error:
				pass
			else:
				outFormat = outputArgs.formatName
				self.outputFormatBox.setActive(outFormat)

		if outFormat:
			self.status('Press "Convert"')
		else:
			self.status("Select output format")
