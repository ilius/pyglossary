"""
Slint-based graphical user interface for PyGlossary (`--ui=slint`).

Threading model: slint's pyclasses are pyo3 `unsendable` (bound to the
event-loop thread) and slint is built with `panic = "abort"`, so every slint
access happens on the event-loop thread. Blocking work (conversion, native
file-dialog subprocess) runs on worker threads that only hand plain data back
through `UI._post` (`slint.native.invoke_from_event_loop`). `Glossary(ui=self)`
is safe: during conversion it only calls `progressInit/progress/progressEnd`,
which only `_post`. Slint's event loop can't nest, so secondary windows are
non-modal `show()`n dialogs. The GC hazard behind `utils.load_slint`'s cache
and `UI._shutdown` is documented on `load_slint`.
"""

from __future__ import annotations

import gc
import logging
import os
import sys
import threading
from os.path import dirname, splitext
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.core import homePage
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.ui.base import UIBase, aboutText, authors, licenseText
from pyglossary.utils.os_utils import abspath2
from pyglossary.utils.text_utils import urlToPath

from .alert_dialog import AlertDialog
from .format_picker import FormatPicker
from .general_options import GeneralOptionsDialog
from .info_dialog import InfoDialog
from .log_handler import SlintLogHandler
from .options_dialog import FormatOptionsDialog
from .theme_dialog import ThemeDialog
from .utils import (
	SLINT_STYLES,
	clearSlintCache,
	load_slint,
	loadFcdDir,
	pickFile,
	saveFcdDir,
	setSlintStyle,
	weakCallback,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.stubs.config_types import ConfigType

__all__ = ["UI"]

log = logging.getLogger("pyglossary")

_CONSOLE_CAP = 2000


class UI(UIBase):
	"""Slint front-end for PyGlossary."""

	def __init__(self, progressbar: bool = True) -> None:
		UIBase.__init__(self)
		try:
			self.loadConfig()
		except Exception:  # noqa: BLE001 standalone without a config file
			log.exception("could not load config; using defaults")

		# before the first load_slint(), which bakes the style in
		setSlintStyle(self.config.get("slint.theme", ""))

		if not Glossary.readFormats:  # standalone run (mainPrepare not called)
			Glossary.init()

		plugins = Glossary.plugins.values()
		self.pluginByDesc = {p.description: p for p in plugins}
		self.readDesc = [p.description for p in plugins if p.canRead]
		self.writeDesc = [p.description for p in plugins if p.canWrite]

		self.progressbar = progressbar
		self.readOptions: dict[str, Any] = {}
		self.writeOptions: dict[str, Any] = {}
		self.convertOptions: dict[str, Any] = {}
		self.infoOverride: dict[str, Any] = {}
		self._glossarySetAttrs: dict[str, Any] = {}

		self.pathI = ""
		self.pathO = ""
		self._inFormat = ""
		self._outFormat = ""
		self.fcd_dir = loadFcdDir()

		self._uiThreadId = threading.get_ident()  # the event-loop thread
		self._dialogs: set[Any] = set()  # keeps non-modal windows alive
		self._convertThread: threading.Thread | None = None
		self._progressTitle = ""

		levels = [f"{i} - {name}" for i, name in enumerate(log.levelNamesCap)]
		self.console_lines = slint.ListModel([])
		self.win = load_slint("main_window.slint").MainWindow()
		self.win.console_lines = self.console_lines
		self.win.verbosity_levels = slint.ListModel(levels)
		self.win.verbosity = levels[log.getVerbosity()]
		self.win.about_text = self._aboutText()

		self._logHandler = SlintLogHandler(self)
		log.addHandler(self._logHandler)

		w = self.win
		w.browse_input_file = weakCallback(self._browseInput)
		w.browse_output_file = weakCallback(self._browseOutput)
		w.choose_input_format = weakCallback(self._chooseInputFormat)
		w.choose_output_format = weakCallback(self._chooseOutputFormat)
		w.options_selected = weakCallback(self._onOptionsSelected)
		w.start_convert = weakCallback(self.convert)
		w.clear_console = weakCallback(self._clearConsole)
		w.verbosity_changed = weakCallback(self._verbosityChanged)
		w.input_file_edited = weakCallback(self._applyInputPath)
		w.output_file_edited = weakCallback(self._applyOutputPath)

		log.info("Slint UI initialized")

	@staticmethod
	def _aboutText() -> str:
		try:
			import importlib.metadata as md

			slintVersion = md.version("slint")
		except Exception:  # noqa: BLE001
			slintVersion = ""
		from pyglossary.ui.version import getAboutHeader

		authorsText = "\n".join(authors).replace("⚫︎", "-").replace("\t", "    ")
		return "\n\n".join(
			[
				getAboutHeader("Slint", slintVersion),
				f"{aboutText}\nHome page: {homePage}",
				f"Authors:\n{authorsText}",
				f"License:\n{licenseText}",
			],
		)

	def _post(self, fn: Callable[[], None]) -> None:
		"""
		Run `fn` (which may touch slint) on the event-loop thread: directly if
		already there, else via `invoke_from_event_loop`. Exceptions of posted
		calls are logged, since slint would only `eprintln!` them.
		"""
		if threading.get_ident() == self._uiThreadId:
			fn()
			return

		def run() -> None:
			try:
				fn()
			except Exception:  # noqa: BLE001
				log.exception("UI update failed")

		try:
			slint.native.invoke_from_event_loop(run)
		except Exception:  # noqa: BLE001 loop not running / already quit
			pass

	# --- event-loop-thread mutators -------------------------------------
	def _appendLog(self, msg: str, colorHex: str) -> None:
		model = self.console_lines
		model.append({"text": msg, "text_color": slint.Color(colorHex)})
		if len(model) > _CONSOLE_CAP:
			del model[: len(model) - _CONSOLE_CAP]

	def _setProgress(self, ratio: float, text: str) -> None:
		self.win.progress = ratio
		self.win.status_text = text

	def _conversionDone(self, ok: bool) -> None:
		self._convertThread = None
		self.win.converting = False
		self.win.status_text = "Done" if ok else "Failed (see console)"

	def _clearConsole(self) -> None:
		del self.console_lines[:]

	def _verbosityChanged(self, value: str) -> None:  # noqa: PLR6301
		log.setVerbosity(int(value.split(" ", 1)[0]))

	# --- UIBase progress callbacks (worker thread; no slint access) ------
	def progressInit(self, title: str) -> None:
		self._progressTitle = title

	def progress(self, ratio: float, text: str = "") -> None:
		text = (text or f"%{int(ratio * 100)}") + " - " + self._progressTitle
		ratio = float(ratio)
		self._post(lambda: self._setProgress(ratio, text))

	def progressEnd(self) -> None:
		text = "%100 - " + self._progressTitle
		self._post(lambda: self._setProgress(1.0, text))

	# --- file browsing ---------------------------------------------------
	# `pickFile` runs an out-of-process dialog (see utils) and blocks, so it
	# runs on a short-lived worker thread.
	def _browseInput(self) -> None:
		self._browse(save=False)

	def _browseOutput(self) -> None:
		self._browse(save=True)

	def _browse(self, save: bool) -> None:
		initialdir = self.fcd_dir

		def worker() -> None:
			path = pickFile(save, initialdir)
			if path:
				self._post(lambda: self._applyBrowsed(save, path))

		threading.Thread(target=worker, daemon=True).start()

	def _applyBrowsed(self, save: bool, path: str) -> None:
		self.fcd_dir = dirname(path)
		saveFcdDir(path)
		if save:
			self.win.output_file_path = path
			self._applyOutputPath(path)
		else:
			self.win.input_file_path = path
			self._applyInputPath(path)

	# --- path edits + auto-format detection -----------------------------
	# A detected format always replaces the current one; when nothing is
	# detected the current format stays.
	def _applyInputPath(self, path: str) -> None:
		if path.startswith("file://"):
			path = urlToPath(path)
			self.win.input_file_path = path
		if self.pathI == path:
			return
		if self.config.get("ui_autoSetFormat"):
			try:
				inputArgs = Glossary.detectInputFormat(path)
			except Error:
				pass
			except Exception:  # noqa: BLE001
				log.exception("")
			else:
				plugin = Glossary.plugins.get(inputArgs.formatName)
				if plugin:
					self._setInputFormat(plugin.description)
		self.pathI = path

	def _applyOutputPath(self, path: str) -> None:
		if path.startswith("file://"):
			path = urlToPath(path)
			self.win.output_file_path = path
		if self.pathO == path:
			return
		if self.config.get("ui_autoSetFormat"):
			try:
				outputArgs = Glossary.detectOutputFormat(
					filename=path,
					inputFilename=self.win.input_file_path or "",
				)
			except Error:
				pass
			except Exception:  # noqa: BLE001
				log.exception("")
			else:
				plugin = Glossary.plugins.get(outputArgs.formatName)
				if plugin:
					self._setOutputFormat(plugin.description)
		self.pathO = path

	# --- format selection -------------------------------------------------
	def _setInputFormat(self, desc: str) -> None:
		self._inFormat = desc
		self.win.input_format = desc
		self.readOptions.clear()  # reset in place, never re-bind (matches tk)

	def _setOutputFormat(self, desc: str) -> None:
		self._outFormat = desc
		self.win.output_format = desc
		self.writeOptions.clear()

		ext = self.pluginByDesc[desc].extensionCreate
		pathI = self.win.input_file_path
		if pathI and ext and not self.win.output_file_path:
			self.win.output_file_path = self.pathO = splitext(pathI)[0] + ext

	def _open(self, cls: Callable[..., Any], **kwargs: Any) -> None:
		self._dialogs.add(cls(onClose=self._dialogs.discard, **kwargs))

	def _chooseInputFormat(self) -> None:
		self._open(
			FormatPicker,
			descList=self.readDesc,
			activeDesc=self._inFormat,
			onSelect=self._setInputFormat,
		)

	def _chooseOutputFormat(self) -> None:
		self._open(
			FormatPicker,
			descList=self.writeDesc,
			activeDesc=self._outFormat,
			onSelect=self._setOutputFormat,
		)

	# --- options dropdown + sub-dialogs ------------------------------------
	def _onOptionsSelected(self, value: str) -> None:
		# keys must match the UpComboBox model in main_window.slint
		if value == "Read Options":
			self._openFormatOptions("Read", self._inFormat, self.readOptions)
		elif value == "Write Options":
			self._openFormatOptions("Write", self._outFormat, self.writeOptions)
		elif value == "General Options":
			self._open(GeneralOptionsDialog, ui=self)
		elif value == "Info / Metadata":
			self._open(InfoDialog, info=self.infoOverride)
		elif value == "Theme":
			self._open(
				ThemeDialog,
				currentStyle=self.config.get("slint.theme", ""),
				onOk=self._onThemeChosen,
			)
		else:
			log.error(f"unknown Options entry {value!r}")

	def _openFormatOptions(
		self,
		kind: str,
		formatDesc: str,
		values: dict[str, Any],
	) -> None:
		if not formatDesc:
			log.error(
				f"Choose {'an input' if kind == 'Read' else 'an output'} format first"
			)
			return
		self._open(
			FormatOptionsDialog,
			plugin=self.pluginByDesc[formatDesc],
			kind=kind,
			values=values,
		)

	def _onThemeChosen(self, style: str) -> None:
		if style == self.config.get("slint.theme", ""):
			return
		self.config["slint.theme"] = style
		self.saveConfig()
		label = next(label for label, value in SLINT_STYLES if value == style)
		log.info(f"Theme changed to {label!r}; restart the app for it to take effect")
		self._open(
			AlertDialog,
			message=f"Theme changed to “{label}”.\n"
			"Restart PyGlossary for it to take effect.",
		)

	# --- conversion ---------------------------------------------------------
	def convert(self) -> None:
		if self._convertThread is not None:
			log.warning("Conversion already in progress")
			return

		inPath = self.win.input_file_path
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormat = self.pluginByDesc[self._inFormat].name if self._inFormat else ""

		outPath = self.win.output_file_path
		if not outPath:
			log.critical("Output file path is empty!")
			return
		if not self._outFormat:
			log.critical("Output format is empty!")
			return
		outFormat = self.pluginByDesc[self._outFormat].name

		if self.infoOverride:
			log.info(f"infoOverride = {self.infoOverride}")
		if self.convertOptions:
			log.info(f"convertOptions: {self.convertOptions}")

		glos = Glossary(ui=self)
		glos.config = dict(self.config)
		glos.progressbar = self.progressbar
		for attr, value in self._glossarySetAttrs.items():
			setattr(glos, attr, value)

		convertArgs = ConvertArgs(
			inPath,
			inputFormat=inFormat,
			outputFilename=outPath,
			outputFormat=outFormat,
			readOptions=dict(self.readOptions),
			writeOptions=dict(self.writeOptions),
			infoOverride=dict(self.infoOverride) if self.infoOverride else None,
			**self.convertOptions,
		)

		def work() -> None:  # worker thread: no slint access
			ok = False
			try:
				ok = bool(glos.convert(convertArgs))
			except Error as e:
				log.critical(str(e))
				try:
					glos.cleanup()
				except Exception:  # noqa: BLE001
					log.exception("")
			except Exception:  # noqa: BLE001
				log.exception("Conversion failed")
			finally:
				self._post(lambda: self._conversionDone(ok))

		self.win.converting = True
		self.win.progress = 0.0
		self.win.status_text = "Starting…"
		self._convertThread = threading.Thread(target=work, daemon=True)
		self._convertThread.start()

	# --- entry point (called by runner.py, same signature as ui_tk) -----------
	def run(  # noqa: PLR0913
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		config: ConfigType | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> None:
		# keep the config loaded in __init__ on standalone runs (config=None)
		if config:
			self.config = config

		if inputFilename:
			self.win.input_file_path = abspath2(inputFilename)
			self._applyInputPath(self.win.input_file_path)
		if outputFilename:
			self.win.output_file_path = abspath2(outputFilename)
			self._applyOutputPath(self.win.output_file_path)

		if inputFormat and inputFormat not in Glossary.readFormats:
			log.error(f"invalid {inputFormat=}")
			inputFormat = ""
		if outputFormat and outputFormat not in Glossary.writeFormats:
			log.error(f"invalid {outputFormat=}")
			outputFormat = ""

		if inputFormat:
			self._setInputFormat(Glossary.plugins[inputFormat].description)
		if outputFormat:
			self._setOutputFormat(Glossary.plugins[outputFormat].description)

		if readOptions:
			self.readOptions = readOptions
		if writeOptions:
			self.writeOptions = writeOptions

		if convertOptions:
			log.info(f"Using {convertOptions=}")
			self.infoOverride = convertOptions.pop("infoOverride", None) or {}
		self.convertOptions = convertOptions or {}

		self._glossarySetAttrs = glossarySetAttrs or {}

		self.win.run()  # blocks until the main window is closed
		self._shutdown()

	def _shutdown(self) -> None:
		"""
		Leave no slint object for a GC on another thread to clear (see
		`utils.load_slint`). A conversion still running cannot be cancelled and
		keeps allocating, so then exit at once (output is incomplete); else drop
		every slint reference and collect the garbage here, with automatic GC
		paused so no other thread collects it first.
		"""
		log.removeHandler(self._logHandler)

		thread = self._convertThread
		if thread is not None and thread.is_alive():
			log.warning("Window closed during conversion; output is incomplete")
			logging.shutdown()
			for stream in (sys.stdout, sys.stderr):
				if stream is not None:
					stream.flush()
			os._exit(1)

		gcWasEnabled = gc.isenabled()
		gc.disable()
		try:
			self._dialogs.clear()
			self.win = None
			self.console_lines = None
			clearSlintCache()
			gc.collect()
		finally:
			if gcWasEnabled:
				gc.enable()


if __name__ == "__main__":  # standalone launch for development/testing
	log.addHandler(logging.StreamHandler(sys.stderr))
	log.setVerbosity(3)
	UI().run()
