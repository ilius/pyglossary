from __future__ import annotations

import logging
import weakref
from os.path import dirname, isfile, join
from pathlib import Path
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.core import confDir, homeDir, sysName

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"SLINT_STYLES",
	"levelColor",
	"loadFcdDir",
	# "disableMacWindowTabbing",
	"load_slint",
	"pickOpenFile",
	"pickSaveFile",
	"saveFcdDir",
	"setSlintStyle",
	"weakCallback",
]

log = logging.getLogger("pyglossary")

_PKG_DIR = Path(__file__).resolve().parent

# Cache of compiled `.slint` namespaces, keyed by (file name, style). See
# load_slint. Keying on style too (not just file name) is required now that
# the style is user-selectable: each distinct (file, style) pair must stay
# permanently reachable once compiled, for the same reason a single style
# had to be cached before (see the long comment on load_slint below).
_SLINT_CACHE: dict[tuple[str, str], Any] = {}

# Built-in Slint widget styles that need no extra native dependency (unlike
# "qt", which requires Qt installed on the system) and no runtime OS-specific
# resolution (unlike "native"). See:
# https://docs.slint.dev/latest/docs/slint/reference/std-widgets/style/
# Each entry is (display name, slint style identifier).
SLINT_STYLES: list[tuple[str, str]] = [
	("System default", ""),
	("Fluent", "fluent"),
	("Material", "material"),
	("Cupertino", "cupertino"),
	("Cosmic", "cosmic"),
]

# The style every subsequent load_slint() call compiles with, until changed
# via setSlintStyle(). Must be set (from the loaded config) before the first
# load_slint() call -- see UI.__init__ in ui.py.
_currentStyle = ""


def setSlintStyle(style: str) -> None:
	"""
	Set the style used by subsequent (uncached) `load_slint()` calls.

	Must be called before the first `load_slint()` call to have any effect on
	the main window; changing it afterwards only affects `.slint` files not
	loaded yet (e.g. a fresh cache after a restart), since an already-loaded
	style is baked into its compiled `ComponentDefinition` and cannot be
	changed on a live component -- see the "Theme" option in the UI, which
	persists the choice to config.json and applies it on next launch.
	"""
	global _currentStyle  # noqa: PLW0603
	_currentStyle = style


# def _readMacBundleIdentifier() -> str | None:
# 	"""
# 	Read `CFBundleIdentifier` from the running `.app` bundle's Info.plist.
#
# 	Returns None when not running from a proper `.app` bundle (e.g. from
# 	source), based on where `sys.executable` sits relative to the bundle:
# 	`X.app/Contents/MacOS/X` -> `X.app/Contents/Info.plist`. Nuitka standalone
# 	builds point `sys.executable` at the compiled binary itself, so this holds
# 	for our nuitka-built `.app` without hardcoding a path depth relative to
# 	this package (which would break if `pyglossary`'s nesting ever changes).
# 	"""
# 	import plistlib
# 	import sys
#
# 	infoPlist = Path(sys.executable).resolve().parent.parent / "Info.plist"
# 	if not infoPlist.is_file():
# 		return None
# 	try:
# 		with infoPlist.open("rb") as fp:
# 			data = plistlib.load(fp)
# 	except Exception:  # noqa: BLE001
# 		return None
# 	bundleId = data.get("CFBundleIdentifier")
# 	return bundleId if isinstance(bundleId, str) else None
#
#
# def disableMacWindowTabbing() -> None:
# 	"""
# 	Best-effort: stop macOS from auto-grouping our separate top-level Slint
# 	windows (main window, Options menu, format picker, alerts, etc.) into one
# 	tabbed window.
#
# 	Since macOS 10.12, AppKit auto-groups an app's plain windows into a single
# 	tabbed window ("Prefer tabs when opening documents") unless the app opts
# 	out; Slint's winit backend does not appear to opt out of this itself, so
# 	every non-modal secondary window here (each a separate top-level `Window`)
# 	gets merged into the main window's tab strip -- which also resizes the
# 	dialog to match whatever the biggest tab in the group is, breaking its
# 	`preferred-width`/`preferred-height` layout.
#
# 	Sets the per-app `NSWindowAllowsAutomaticWindowTabbing` user default --
# 	the same mechanism non-native-Cocoa toolkits (e.g. Electron) commonly use
# 	to disable native window tabbing without writing Objective-C. No-op on
# 	non-macOS or when not running from a `.app` bundle (see
# 	`_readMacBundleIdentifier`); best-effort otherwise -- failures are
# 	silently ignored, since this is cosmetic, not a correctness issue.
# 	"""
# 	if sysName != "darwin":
# 		return
# 	bundleId = _readMacBundleIdentifier()
# 	if not bundleId:
# 		return
# 	import subprocess
#
# 	try:
# 		subprocess.run(  # noqa: S603
# 			[
# 				"defaults", "write", bundleId,
# 				"NSWindowAllowsAutomaticWindowTabbing", "-bool", "NO",
# 			],
# 			check=False,
# 			capture_output=True,
# 			timeout=5,
# 		)
# 	except Exception:  # noqa: BLE001
# 		pass


def weakCallback(method: Any) -> Callable[..., Any]:
	"""
	Wrap a bound method so a Slint callback slot can invoke it WITHOUT keeping
	its receiver alive.

	A Slint component holds every callback slot strongly. If the callback
	strongly referenced the Python controller that owns the component, we would
	form a reference cycle *through an unsendable Slint object*
	(``component -> callback -> controller -> component``). Such a cycle can only
	be reclaimed by CPython's cyclic collector, which may fire on a background
	(conversion) thread and then panic when it clears the Slint object off its
	event-loop thread ("object cannot be sent to a thread").

	Binding callbacks weakly keeps Slint objects out of every reference cycle, so
	they are always freed deterministically by reference counting on the
	event-loop thread. The receiver stays alive via the UI's dialog-retention set
	for as long as its window is shown; once closed and dropped from the set, the
	call becomes a silent no-op.

	Only ever pass a bound method of a plain-Python controller here -- never a
	Slint object (pyo3 classes are not weak-referenceable).
	"""
	ref = weakref.ref(method.__self__)
	func = method.__func__

	def wrapper(*args: Any) -> Any:
		obj = ref()
		if obj is not None:
			return func(obj, *args)
		return None

	return wrapper

# Map pyglossary log levels to console text colors.
#
# NOTE: these are plain hex strings (not slint.Color) on purpose. The log
# handler's `emit` may run on the conversion worker thread, and slint.Color is
# a thread-bound pyclass that panics if it is built or used off the event-loop
# thread. So we pass a plain string across the thread boundary and let
# `UI._appendLog` construct the slint.Color on the event-loop thread (via
# `invoke_from_event_loop`) when the console line is appended.
_LEVEL_COLORS: dict[str, str] = {
	"CRITICAL": "#ff5555",
	"ERROR": "#ff5555",
	"WARNING": "#ffb86c",
	"INFO": "#50fa7b",
	"DEBUG": "#8be9fd",
	"TRACE": "#cccccc",
}
DEFAULT_COLOR = "#f8f8f2"


def levelColor(levelName: str) -> str:
	return _LEVEL_COLORS.get(levelName, DEFAULT_COLOR)


def load_slint(name: str) -> Any:
	"""
	Load a `.slint` file located next to this package, returning the compiled
	module (whose attributes are the `export component`s). Falls back to the
	macOS `Resources/` directory for app-bundle builds, mirroring the lookup
	in the original `app.py` scaffold.

	The result is cached per file name, so each `.slint` file is compiled
	*exactly once* per process (on whichever thread first requests it -- always
	the event-loop/main thread here, since every caller runs on it). This is not
	a mere optimisation: it is load-bearing for correctness.

	`slint.load_file` (via `_build_class`) generates a graph of mutually
	referencing Python wrapper classes, closures and `property` descriptors that
	captures the unsendable native `ComponentDefinition`/`PyStruct` objects. That
	graph is a *reference cycle*, so it can only ever be reclaimed by CPython's
	cyclic garbage collector -- not by reference counting. If we recompiled on
	every dialog open, each closed dialog would drop one such cycle as
	unreachable garbage, to be swept whenever GC next fires -- possibly on the
	conversion worker thread, where clearing an unsendable slint object panics
	the interpreter ("PyStruct/ComponentDefinition is unsendable, but sent to
	another thread"). `weakCallback` cannot prevent this cycle because it lives
	inside slint's generated classes, not in any callback slot we assign.

	Caching keeps every compiled namespace permanently *reachable*, so the cyclic
	collector only ever traverses it (which is safe) and never `tp_clear`s it, on
	any thread. Component instances are still created fresh per dialog by calling
	the (cached) wrapper class; those instances contain no cycles (thanks to
	`weakCallback`) and are freed deterministically by reference counting on the
	event-loop thread when the dialog closes.

	Compiled with the style set via `setSlintStyle()` (empty string = slint's
	own system default). The cache key includes the style so switching styles
	across restarts never returns a stale, differently-styled cached instance.
	"""
	cacheKey = (name, _currentStyle)
	cached = _SLINT_CACHE.get(cacheKey)
	if cached is not None:
		return cached
	slintFile = _PKG_DIR / name
	if not slintFile.exists():
		# inside a .app bundle, step out of MacOS/ into Resources/
		slintFile = _PKG_DIR.parent / "Resources" / name
	module = slint.load_file(str(slintFile), style=_currentStyle or None)
	_SLINT_CACHE[cacheKey] = module
	return module


# ---------------------------------------------------------------------
# Native file dialogs
# ---------------------------------------------------------------------
# Slint has no built-in file picker. We must NOT use tkinter's
# `filedialog` here: `askopenfilename`/`asksaveasfilename` run their own
# blocking modal event loop, which re-enters the native event loop while
# the Slint (winit) event loop is running -> winit panics with
# "tried to handle event while another event is currently being handled".
#
# Instead we use a *subprocess*-based native picker that runs out-of-process
# (no nested event loop in our process): on macOS via `osascript` (AppleScript
# `choose file` / `choose file name`); on Linux via `zenity`/`kdialog` when
# available. If none is available we return "" (the user can still type the
# path into the LineEdit).


def _runCapture(args: list[str]) -> str:
	import subprocess

	# On Windows, args[0] (powershell.exe) is a console-subsystem executable:
	# spawning it from our windowless GUI process (nuitka
	# --windows-console-mode=disable) makes Windows allocate it a brand new
	# console window, which flashes on screen for the subprocess's lifetime.
	# CREATE_NO_WINDOW tells CreateProcess not to allocate a console for the
	# child at all, so it never appears -- capture_output=True still works
	# fine since it pipes stdout/stderr rather than relying on a console.
	kwargs: dict[str, Any] = {}
	if sysName == "windows":
		kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

	try:
		proc = subprocess.run(  # noqa: S603
			args,
			check=False,
			capture_output=True,
			text=True,
			**kwargs,
		)
	except FileNotFoundError:
		return ""  # tool not installed
	except Exception:
		log.exception("file dialog subprocess failed")
		return ""
	if proc.returncode != 0:
		return ""  # user cancelled
	return proc.stdout.strip()


def pickOpenFile(initialdir: str | None = None) -> str:
	if sysName == "darwin":
		return _pickOpenMac(initialdir)
	if sysName == "windows":
		return _pickOpenWin(initialdir)
	return _pickOpenX11(initialdir)


def pickSaveFile(initialdir: str | None = None) -> str:
	if sysName == "darwin":
		return _pickSaveMac(initialdir)
	if sysName == "windows":
		return _pickSaveWin(initialdir)
	return _pickSaveX11(initialdir)


def _macDefaultLocation(initialdir: str | None) -> str:
	"""
	AppleScript `default location (POSIX file "...")` clause for `choose file`
	/ `choose file name`, or "" when no usable directory is given. The path is
	embedded in AppleScript source, so its string metacharacters (backslash,
	double quote) must be escaped.
	"""
	from os.path import isdir

	if not initialdir or not isdir(initialdir):
		return ""
	escaped = initialdir.replace("\\", "\\\\").replace('"', '\\"')
	return f' default location (POSIX file "{escaped}")'


def _pickOpenMac(initialdir: str | None) -> str:
	script = (
		'POSIX path of (choose file with prompt "Select input file"'
		f"{_macDefaultLocation(initialdir)})"
	)
	return _runCapture(["osascript", "-e", script])


def _pickSaveMac(initialdir: str | None) -> str:
	script = (
		'POSIX path of (choose file name with prompt "Select output file"'
		f"{_macDefaultLocation(initialdir)})"
	)
	return _runCapture(["osascript", "-e", script])


def _psDialog(psScript: str) -> str:
	"""
	Run a Windows PowerShell snippet that shows a native OpenFileDialog /
	SaveFileDialog and prints the chosen path. Run out-of-process
	(powershell.exe owns its own message pump) so it does not nest inside the
	Slint event loop. Returns "" on cancel / failure / missing powershell.
	"""
	# -NoProfile: skip loading the user profile for speed and determinism.
	return _runCapture(["powershell.exe", "-NoProfile", "-Command", psScript])


def _psInitialDir(initialdir: str | None) -> str:
	"""
	`$d.InitialDirectory = '...';` assignment for the PowerShell dialog
	snippets, or "" when no usable directory is given. The path is embedded in
	a single-quoted PowerShell string, where the only metacharacter is the
	single quote itself (escaped by doubling).
	"""
	from os.path import isdir

	if not initialdir or not isdir(initialdir):
		return ""
	escaped = initialdir.replace("'", "''")
	return f"$d.InitialDirectory = '{escaped}';"


def _pickOpenWin(initialdir: str | None) -> str:
	ps = (
		"Add-Type -AssemblyName System.Windows.Forms;"
		"$d = New-Object System.Windows.Forms.OpenFileDialog;"
		"$d.Title = 'Select input file';"
		"$d.Filter = 'All files (*.*)|*.*';"
		f"{_psInitialDir(initialdir)}"
		"if ($d.ShowDialog() -eq 'OK') { $d.FileName }"
	)
	return _psDialog(ps)


def _pickSaveWin(initialdir: str | None) -> str:
	ps = (
		"Add-Type -AssemblyName System.Windows.Forms;"
		"$d = New-Object System.Windows.Forms.SaveFileDialog;"
		"$d.Title = 'Select output file';"
		"$d.Filter = 'All files (*.*)|*.*';"
		f"{_psInitialDir(initialdir)}"
		"if ($d.ShowDialog() -eq 'OK') { $d.FileName }"
	)
	return _psDialog(ps)


def _x11StartDir(initialdir: str | None) -> str:
	from os.path import isdir

	if initialdir and isdir(initialdir):
		return initialdir
	return homeDir


def _pickOpenX11(initialdir: str | None) -> str:
	import shutil

	startDir = _x11StartDir(initialdir)
	if shutil.which("zenity"):
		# trailing separator: a bare directory path would pre-fill it as the
		# selected *file* name; with the separator zenity just starts there
		return _runCapture([
			"zenity", "--file-selection",
			f"--filename={join(startDir, '')}",
		])
	if shutil.which("kdialog"):
		return _runCapture(["kdialog", "--getopenfilename", startDir])
	log.error("no file dialog tool found (need zenity or kdialog)")
	return ""


def _pickSaveX11(initialdir: str | None) -> str:
	import shutil

	startDir = _x11StartDir(initialdir)
	if shutil.which("zenity"):
		return _runCapture([
			"zenity", "--file-selection", "--save",
			f"--filename={join(startDir, '')}",
		])
	if shutil.which("kdialog"):
		return _runCapture(["kdialog", "--getsavefilename", startDir])
	log.error("no file dialog tool found (need zenity or kdialog)")
	return ""


# ---------------------------------------------------------------------
# Last-used browse directory
# ---------------------------------------------------------------------
_FCD_SAVE_PATH = join(confDir, "ui-slint-fcd-dir")


def loadFcdDir() -> str:
	default = join(homeDir, "Desktop")
	if isfile(_FCD_SAVE_PATH):
		try:
			with open(_FCD_SAVE_PATH, encoding="utf-8") as fp:
				return fp.read().strip("\n") or default
		except Exception:
			log.exception("")
	return default


def saveFcdDir(path: str) -> None:
	if not path:
		return
	try:
		with open(_FCD_SAVE_PATH, mode="w", encoding="utf-8") as fp:
			fp.write(dirname(path))
	except Exception:
		log.exception("")
