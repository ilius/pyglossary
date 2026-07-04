# Slint-based graphical interface for PyGlossary.
#   - a `UI` class subclassing `UIBase`
#   - a `run(...)` signature compatible with `pyglossary/ui/runner.py`
#   - dispatched via `--ui=slint` (registered in runner.py / argparse_main.py)
#
# Threading model:
#   Slint objects (ListModel rows, PyStructs such as slint.Color, component
#   instances) are bound to the event-loop thread; touching them from any other
#   thread trips pyo3's `unsendable` assertion and panics the interpreter.
#   Therefore, *every* slint mutation must happen on the event-loop thread.
#
#   Blocking work (`Glossary.convert()`, the native file-dialog subprocess) runs
#   on plain worker threads. Those threads never touch a slint object directly;
#   they hand results back to the UI exclusively through Slint's canonical
#   thread-safe primitive `slint.native.invoke_from_event_loop(cb)`, whose body
#   runs on the event-loop thread. `UI._post` is the single funnel used
#   everywhere (progress, log records, browse results, conversion-done).
#
#   `self` is safe to pass as `Glossary(ui=self)` because the only methods
#   `Glossary` calls on its `ui` during conversion are `progressInit` /
#   `progress` / `progressEnd`, and each of those only does plain-Python string
#   work and a single `_post` -- no slint access on the worker thread.
#
#   Slint's event loop cannot be nested, so secondary windows are non-modal
#   (`show()`) and report results through callbacks; only the main window calls
#   `.run()`.
#
#   Slint's pyclasses are `unsendable` (bound to the event-loop thread). CPython's
#   *cyclic* garbage collector is thread-agnostic: it fires on whichever thread
#   crosses the allocation threshold, and `tp_clear`s every unreachable cycle it
#   finds. If it ever clears an unreachable cycle containing a slint object on the
#   conversion worker thread, pyo3's unsendable assertion panics the interpreter.


from __future__ import annotations

import gc
import logging
import os
import threading
from os.path import dirname, splitext
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.core import homePage
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary
from pyglossary.os_utils import abspath2
from pyglossary.text_utils import urlToPath
from pyglossary.ui.base import UIBase, aboutText, authors, licenseText

from .alert_dialog import AlertDialog
from .format_picker import FormatPicker
from .general_options import GeneralOptionsDialog
from .info_dialog import InfoDialog
from .log_handler import SlintLogHandler
from .options_dialog import FormatOptionsDialog
from .theme_dialog import ThemeDialog
from .utils import (
	SLINT_STYLES,
	load_slint,
	# disableMacWindowTabbing,
	loadFcdDir,
	saveFcdDir,
	setSlintStyle,
	weakCallback,
)

if TYPE_CHECKING:
	from pyglossary.config_type import ConfigType

__all__ = ["UI"]

log = logging.getLogger("pyglossary")

# The canonical, thread-safe way to run `cb` on the Slint event-loop thread from
# any thread. Safe to call before the loop starts or after it quits (it is a
# silent no-op in both cases), so worker threads can post updates without
# worrying about the window having been closed mid-conversion.
_invokeFromEventLoop = slint.native.invoke_from_event_loop

# Nuitka injects a `__compiled__` global into every module it compiles; this
# is its own recommended way to detect a compiled/standalone build from
# within Python code (there is no such marker when running `python main.py`
# from source).
_isCompiledBuild = "__compiled__" in globals()

_CONSOLE_CAP = 2000
_NONE_INPUT_LABEL = "(choose input format)"
_NONE_OUTPUT_LABEL = "(choose output format)"


def _runConvert(
		glos: Glossary,
		convertArgs: ConvertArgs,
		done: Any,
) -> None:
	"""
	Background-thread entry point.

	It references only plain pyglossary objects (`glos`, `convertArgs`) and a
	plain callable (`done`); it never touches `self` or any slint object, so
	nothing slint-bound can be dropped or accessed on this thread. Progress and
	log updates flow back through `invoke_from_event_loop` (via the UI methods
	on `glos.ui` and the log handler), and `done` is posted on the event-loop
	thread when conversion finishes (or the loop has been quit).
	"""
	try:
		glos.convert(convertArgs)
	except Error as e:
		log.critical(str(e))
		try:
			glos.cleanup()
		except Exception:  # noqa: BLE001
			log.exception("")
	except Exception:  # noqa: BLE001
		log.exception("Conversion failed")
	finally:
		try:
			_invokeFromEventLoop(done)
		except Exception:  # noqa: BLE001 loop already quit (window closed)
			pass


class _OptionsMenuController:
	"""
	Tiny controller for the pop-up options menu.

	Its only reason to exist is lifetime hygiene: the UI keeps this plain-Python
	object alive in its dialog-retention set, while the Slint menu component
	points back only through weak callbacks. The menu is therefore never a member
	of a reference cycle and is freed by reference counting on the event-loop
	thread the moment this controller is dropped from the set.
	"""

	def __init__(self, ui: UI) -> None:
		self._ui = ui
		self.dialog = load_slint("dialogs.slint").OptionsMenuDialog()
		self.dialog.read_options = weakCallback(ui._openReadOptions)
		self.dialog.write_options = weakCallback(ui._openWriteOptions)
		self.dialog.general_options = weakCallback(ui._openGeneralOptions)
		self.dialog.info_options = weakCallback(ui._openInfo)
		self.dialog.theme_options = weakCallback(ui._openTheme)
		self.dialog.close_menu = weakCallback(self._close)
		self.dialog.show()

	def _close(self) -> None:
		self.dialog.hide()
		self._ui._unref(self)


class UI(UIBase):
	"""Slint front-end for PyGlossary."""

	def __init__(self, progressbar: bool = True) -> None:
		UIBase.__init__(self)
		try:
			self.loadConfig()
		except Exception:  # noqa: BLE001 standalone without a config file
			log.exception("could not load config; using defaults")

		# Must happen before the first load_slint() call below (which compiles
		# main_window.slint with this style baked in) -- see setSlintStyle.
		setSlintStyle(self.config.get("ui_slint_theme", ""))

		# Best-effort, macOS-only, no-op unless running from the .app bundle --
		# must run before any window (including the main one) is created. See
		# disableMacWindowTabbing.
		# disableMacWindowTabbing()

		if not Glossary.readFormats:
			# idempotent: mainPrepare already calls Glossary.init() in normal
			# flow; only init when running standalone.
			Glossary.init()

		self.pluginByDesc = {
			plugin.description: plugin for plugin in Glossary.plugins.values()
		}
		self.readDesc = [
			plugin.description for plugin in Glossary.plugins.values() if plugin.canRead
		]
		self.writeDesc = [
			plugin.description
			for plugin in Glossary.plugins.values()
			if plugin.canWrite
		]

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

		# the thread that owns all slint objects (the event-loop thread)
		self._uiThreadId = threading.get_ident()
		self._dialogs: set[Any] = set()
		self._converting = False
		self._progressTitle = ""

		self.console_lines = slint.ListModel([])
		self.win = load_slint("main_window.slint").MainWindow()
		self.win.console_lines = self.console_lines
		self.win.verbosity = self._verbosityString()
		self.win.about_text = self._aboutText()
		self.win.status_text = ""

		# route pyglossary log records into the on-screen console. The handler
		# marshals each record onto the event-loop thread via `_post`.
		log.addHandler(SlintLogHandler(self))

		self._bindCallbacks()

		log.info("Slint UI initialized")

	# -------------------------------------------------------------
	# Setup helpers
	# -------------------------------------------------------------
	def _bindCallbacks(self) -> None:
		# Bind weakly via utils.weakCallback so the main window is never part of
		# a reference cycle with the UI.
		w = self.win
		w.browse_input_file = weakCallback(self._browseInput)
		w.browse_output_file = weakCallback(self._browseOutput)
		w.choose_input_format = weakCallback(self._chooseInputFormat)
		w.choose_output_format = weakCallback(self._chooseOutputFormat)
		w.show_options = weakCallback(self._showOptionsMenu)
		w.start_convert = weakCallback(self.convert)
		w.clear_console = weakCallback(self._clearConsole)
		w.verbosity_changed = weakCallback(self._verbosityChanged)
		w.input_file_edited = weakCallback(self._inputEdited)
		w.output_file_edited = weakCallback(self._outputEdited)

	def _verbosityString(self) -> str:
		try:
			v = log.getVerbosity()
		except Exception:  # noqa: BLE001 logger may be a plain Logger standalone
			v = 3
		names = ("Critical", "Error", "Warning", "Info", "Debug", "Trace", "All")
		if v < 0 or v >= len(names):
			v = 3
		return f"{v} - {names[v]}"

	def _aboutText(self) -> str:
		try:
			import importlib.metadata as md

			slintVersion = md.version("slint")
		except Exception:  # noqa: BLE001
			slintVersion = ""
		from pyglossary.ui.version import getAboutHeader

		header = getAboutHeader("Slint", slintVersion)
		authorsText = ("\n".join(authors)
			.replace("\u26AB\uFE0E", "-")
			.replace("\t", "    ")
		)
		return "\n\n".join(
			[
				header,
				f"{aboutText}\nHome page: {homePage}",
				f"Authors:\n{authorsText}",
				f"License:\n{licenseText}",
			],
		)

	# -------------------------------------------------------------
	# The single funnel for cross-thread UI updates (the Slint way)
	# -------------------------------------------------------------
	# `fn` mutates slint state and therefore MUST run on the event-loop thread.
	# If we are already on it (e.g. a click callback, or pre-loop setup), run
	# `fn` directly; otherwise hand it to `invoke_from_event_loop`, which
	# schedules it on the event-loop thread. This is the only place that
	# crosses the thread boundary, so it is the only place that needs to be
	# correct about thread-safety.
	def _post(self, fn: Any) -> None:
		if threading.get_ident() == self._uiThreadId:
			fn()
			return
		try:
			_invokeFromEventLoop(fn)
		except Exception:  # noqa: BLE001 loop not running / already quit
			pass

	# -------------------------------------------------------------
	# Event-loop-thread mutators (called via `_post` or directly on the UI
	# thread). These are the only methods that touch slint objects.
	# -------------------------------------------------------------
	def _appendLog(self, msg: str, colorHex: str) -> None:
		# slint.Color is a thread-bound pyclass, so it is built here, on the
		# event-loop thread, never on the worker that produced the record.
		self.console_lines.append(
			{"text": msg, "text_color": slint.Color(colorHex)},
		)
		while len(self.console_lines) > _CONSOLE_CAP:
			del self.console_lines[0]

	def _setProgress(self, ratio: float, text: str) -> None:
		self.win.progress = ratio
		self.win.status_text = text

	def _conversionDone(self) -> None:
		self._converting = False
		self.win.converting = False
		self.win.status_text = "Done"

	# -------------------------------------------------------------
	# Progress callbacks (UIBase overrides). Called on the worker thread by
	# `Glossary` during conversion (and never touch slint directly).
	# -------------------------------------------------------------
	def progressInit(self, title: str) -> None:
		self._progressTitle = title

	def progress(self, ratio: float, text: str = "") -> None:
		if not text:
			text = "%" + str(int(ratio * 100))
		text += " - " + self._progressTitle
		ratio = float(ratio)
		self._post(lambda: self._setProgress(ratio, text))

	def progressEnd(self) -> None:
		title = self._progressTitle
		self._post(lambda: self._setProgress(1.0, "%100 - " + title))

	# -------------------------------------------------------------
	# Dialog reference management (keep non-modal windows alive)
	# -------------------------------------------------------------
	def _ref(self, dialog: Any) -> None:
		self._dialogs.add(dialog)

	def _unref(self, dialog: Any) -> None:
		self._dialogs.discard(dialog)

	# -------------------------------------------------------------
	# Console / verbosity
	# -------------------------------------------------------------
	def _clearConsole(self) -> None:
		self.console_lines = slint.ListModel([])
		self.win.console_lines = self.console_lines

	def _verbosityChanged(self, value: str) -> None:
		try:
			log.setVerbosity(int(value.split(" ", 1)[0]))
		except Exception:  # noqa: BLE001
			log.exception(f"invalid verbosity {value!r}")

	# -------------------------------------------------------------
	# File browsing
	# -------------------------------------------------------------
	# The native file dialog is an out-of-process subprocess (osascript on
	# macOS, zenity/kdialog on Linux, powershell + WinForms on Windows) so it
	# does NOT nest a second event loop inside Slint's winit loop (which would
	# panic: "tried to handle event while another event is currently being
	# handled"). `subprocess.run` blocks, so we run it on a short-lived worker
	# thread and post the chosen path back through `_post`; the Slint window
	# stays responsive while the native dialog is open.
	def _browseInput(self) -> None:
		self._runFilePicker("open", self._applyBrowsedInput)

	def _browseOutput(self) -> None:
		self._runFilePicker("save", self._applyBrowsedOutput)

	def _runFilePicker(self, kind: str, apply: Any) -> None:
		from .utils import pickOpenFile, pickSaveFile

		picker = pickOpenFile if kind == "open" else pickSaveFile
		initialdir = self.fcd_dir

		def worker() -> None:
			path = picker(initialdir)
			if not path:
				return
			self._post(lambda: apply(path))

		threading.Thread(target=worker, daemon=True).start()

	def _applyBrowsedInput(self, path: str) -> None:
		self.win.input_file_path = path
		self.fcd_dir = dirname(path)
		saveFcdDir(path)
		self._applyInputPath(path)

	def _applyBrowsedOutput(self, path: str) -> None:
		self.win.output_file_path = path
		self.fcd_dir = dirname(path)
		saveFcdDir(path)
		self._applyOutputPath(path)

	# -------------------------------------------------------------
	# Path entry edits + auto-format detection
	# -------------------------------------------------------------
	def _inputEdited(self, value: str) -> None:
		self._applyInputPath(value)

	def _outputEdited(self, value: str) -> None:
		self._applyOutputPath(value)

	def _applyInputPath(self, path: str) -> None:
		if path.startswith("file://"):
			path = urlToPath(path)
			self.win.input_file_path = path
		if self.pathI == path:
			return
		# No such thing as a "pinned" format: whatever is currently selected
		# stays exactly as long as detection finds nothing for the new path
		# (unrecognized/no extension); the moment a format IS detected, it
		# always wins, regardless of whether the current one was picked
		# manually or auto-detected earlier -- least surprise, and no need to
		# track *why* the current format is what it is.
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

	# -------------------------------------------------------------
	# Format selection
	# -------------------------------------------------------------
	def _setInputFormat(self, desc: str) -> None:
		self._inFormat = desc
		self.win.input_format = desc or _NONE_INPUT_LABEL
		self.readOptions.clear()  # reset options, DO NOT re-assign (matches tk)

	def _setOutputFormat(self, desc: str) -> None:
		self._outFormat = desc
		self.win.output_format = desc or _NONE_OUTPUT_LABEL
		self.writeOptions.clear()

		plugin = self.pluginByDesc.get(desc) if desc else None
		pathI = self.win.input_file_path
		if (
				pathI
				and not self.win.output_file_path
				and plugin is not None
				and plugin.extensionCreate
		):
			pathNoExt, _ext = splitext(pathI)
			self.win.output_file_path = pathNoExt + plugin.extensionCreate
			self.pathO = self.win.output_file_path

	def _chooseInputFormat(self) -> None:
		picker = FormatPicker(
			descList=self.readDesc,
			activeDesc=self._inFormat,
			onSelect=self._setInputFormat,
			onClose=self._unref,
		)
		self._ref(picker)

	def _chooseOutputFormat(self) -> None:
		picker = FormatPicker(
			descList=self.writeDesc,
			activeDesc=self._outFormat,
			onSelect=self._setOutputFormat,
			onClose=self._unref,
		)
		self._ref(picker)

	# -------------------------------------------------------------
	# Options menu + sub-dialogs
	# -------------------------------------------------------------
	def _showOptionsMenu(self) -> None:
		# Wrapped in a plain-Python controller (not driven inline) so the weak
		# reference for the close callback is taken on the controller rather than
		# on the Slint component itself (pyo3 objects are not weak-referenceable),
		# and so the menu component is never part of a reference cycle.
		self._ref(_OptionsMenuController(self))

	def _openReadOptions(self) -> None:
		if not self._inFormat:
			log.error("Choose an input format first")
			return

		def onOk(values: dict[str, Any]) -> None:
			self.readOptions.clear()
			self.readOptions.update(values)

		dialog = FormatOptionsDialog(
			formatDesc=self._inFormat,
			kind="Read",
			values=self.readOptions,
			onOk=onOk,
			onClose=self._unref,
		)
		self._ref(dialog)

	def _openWriteOptions(self) -> None:
		if not self._outFormat:
			log.error("Choose an output format first")
			return

		def onOk(values: dict[str, Any]) -> None:
			self.writeOptions.clear()
			self.writeOptions.update(values)

		dialog = FormatOptionsDialog(
			formatDesc=self._outFormat,
			kind="Write",
			values=self.writeOptions,
			onOk=onOk,
			onClose=self._unref,
		)
		self._ref(dialog)

	def _openGeneralOptions(self) -> None:
		dialog = GeneralOptionsDialog(
			ui=self,
			onOk=lambda: None,
			onClose=self._unref,
		)
		self._ref(dialog)

	def _openInfo(self) -> None:
		dialog = InfoDialog(
			info=self.infoOverride,
			onOk=lambda _info: None,
			onClose=self._unref,
		)
		self._ref(dialog)

	def _openTheme(self) -> None:
		dialog = ThemeDialog(
			currentStyle=self.config.get("ui_slint_theme", ""),
			onOk=self._onThemeChosen,
			onClose=self._unref,
		)
		self._ref(dialog)

	def _onThemeChosen(self, style: str) -> None:
		if style == self.config.get("ui_slint_theme", ""):
			return
		self.config["ui_slint_theme"] = style
		self.saveConfig()
		label = next(
			(label for label, value in SLINT_STYLES if value == style),
			style or "System default",
		)
		log.info(f"Theme changed to {label!r}; restart the app for it to take effect")
		dialog = AlertDialog(
			message=(
				f"Theme changed to “{label}”.\n"
				"Restart PyGlossary for it to take effect."
			),
			onClose=self._unref,
		)
		self._ref(dialog)

	# -------------------------------------------------------------
	# Conversion (background thread)
	# -------------------------------------------------------------
	def convert(self) -> None:
		if self._converting:
			log.warning("Conversion already in progress")
			return

		inPath = self.win.input_file_path
		if not inPath:
			log.critical("Input file path is empty!")
			return
		inFormat = (
			self.pluginByDesc[self._inFormat].name if self._inFormat else ""
		)

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

		# `self` is safe as the Glossary UI: the only methods `Glossary` calls
		# on it during conversion are progressInit/progress/progressEnd, each of
		# which only does plain-Python work + a `_post`. The worker thread never
		# touches a slint object; all UI mutation is marshalled by `_post`.
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

		self._converting = True
		self.win.converting = True
		self.win.progress = 0.0
		self.win.status_text = "Starting…"

		thread = threading.Thread(
			target=_runConvert,
			args=(glos, convertArgs, self._conversionDone),
			daemon=True,
		)
		thread.start()

	# -------------------------------------------------------------
	# run() — entry point called by runner.py (same signature as ui_tk)
	# -------------------------------------------------------------
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
		# Only replace the config loaded in __init__ when the caller (main.py)
		# actually passes one (the full, file-loaded + CLI-flag-merged config).
		# `config or {}` would wipe the already-loaded config on a standalone
		# run (config=None), losing ui_autoSetFormat / ui_slint_theme etc.
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

		if reverse:
			log.error("Slint interface does not support Reverse feature")

		if readOptions:
			self.readOptions = readOptions
		if writeOptions:
			self.writeOptions = writeOptions

		if convertOptions:
			log.info(f"Using {convertOptions=}")
			self.infoOverride = convertOptions.pop("infoOverride", None) or {}
		self.convertOptions = convertOptions or {}

		self._glossarySetAttrs = glossarySetAttrs or {}

		# blocks on the Slint event loop until the window is closed. All worker
		# updates arrive through `invoke_from_event_loop`.
		self.win.run()
		if _isCompiledBuild:
			self._teardownAndExit()

	# -------------------------------------------------------------
	# Shutdown
	# -------------------------------------------------------------
	def _teardownAndExit(self) -> None:
		"""
		Run right after `self.win.run()` returns (window closed), compiled
		builds only -- see `_isCompiledBuild`.

		Nuitka-standalone builds (unlike `python main.py` from source) have been
		observed to panic on exit with pyo3's "unsendable, but ... dropped on
		another thread" for a slint `PyStruct`/`ComponentDefinition`, even though
		no code here ever touches a slint object off the event-loop thread. The
		panic happens during normal CPython interpreter finalization (clearing
		`sys.modules` / module globals), which is not guaranteed to run on this
		thread in a nuitka-standalone build, and/or races a slint-internal
		(non-Python) thread that independently drops its own last handle to a
		wrapped Python object around the same time. Running from source has
		never reproduced this, so this workaround (which forgoes a clean
		interpreter shutdown) is scoped to compiled builds only.

		Two-part mitigation, both required:
		1. Explicitly drop every slint object this module still holds (main
			window, console list model, secondary dialog controllers) here, on
			the event-loop thread, while it's still safe to do so -- so nothing
			slint-related is left for CPython's normal finalization to clear
			later on a different/unknown thread.
		2. Bypass normal CPython interpreter finalization entirely via
			`os._exit()`, since we're quitting anyway -- this skips
			`sys.modules` clearing, GC finalization and atexit handlers, so
			nothing can run (safely or not) after this point.
		"""
		for handler in list(log.handlers):
			try:
				handler.flush()
			except Exception:  # noqa: BLE001
				pass

		self._dialogs.clear()
		self.console_lines = None
		self.win = None

		gc.collect()

		os._exit(0)


if __name__ == "__main__":  # standalone launch for development/testing
	import sys

	# minimal logger setup so standalone runs still print to stderr + console
	handler = logging.StreamHandler(sys.stderr)
	handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
	log.addHandler(handler)
	log.setLevel(logging.INFO)

	ui = UI()
	ui.run()
