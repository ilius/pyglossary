"""Shared helpers for the Slint UI backend."""

from __future__ import annotations

import logging
import shutil
import subprocess
import weakref
from os.path import dirname, isdir, isfile, join
from pathlib import Path
from typing import TYPE_CHECKING, Any

import slint

from pyglossary.core import confDir, homeDir, sysName

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"SLINT_STYLES",
	"clearSlintCache",
	"levelColor",
	"loadFcdDir",
	"load_slint",
	"pickFile",
	"saveFcdDir",
	"setSlintStyle",
	"weakCallback",
]

log = logging.getLogger("pyglossary")

_PKG_DIR = Path(__file__).resolve().parent

# (display name, slint style) for the built-in styles that need no extra
# native dependency ("qt") or runtime resolution ("native").
SLINT_STYLES: list[tuple[str, str]] = [
	("System default", ""),
	("Fluent", "fluent"),
	("Fluent Light", "fluent-light"),
	("Fluent Dark", "fluent-dark"),
	("Material", "material"),
	("Material Light", "material-light"),
	("Material Dark", "material-dark"),
	("Cupertino", "cupertino"),
	("Cupertino Light", "cupertino-light"),
	("Cupertino Dark", "cupertino-dark"),
	("Cosmic", "cosmic"),
	("Cosmic Light", "cosmic-light"),
	("Cosmic Dark", "cosmic-dark"),
]

_currentStyle = ""
_SLINT_CACHE: dict[tuple[str, str], Any] = {}


def setSlintStyle(style: str) -> None:
	"""
	Set the style for subsequent `load_slint()` compilations. A style is baked
	into the compiled file, so call this before the first load; a newly chosen
	theme is persisted to config and applies on the next launch.
	"""
	global _currentStyle  # noqa: PLW0603
	_currentStyle = style


def load_slint(name: str) -> Any:
	"""
	Compile the `.slint` file `name` next to this module, once per process.

	The cache is load-bearing, not an optimisation. `slint.load_file` builds
	self-referential wrapper classes whose closures capture unsendable
	`PyStruct`/`ComponentDefinition` objects; a dropped namespace is cyclic
	garbage with those as leaves. If CPython's cyclic GC then runs on a worker
	thread, pyo3 `tp_clear`s them off their owner thread -> assertion ->
	abort (slint is `panic = "abort"`). Only `clearSlintCache` (from
	`UI._shutdown`) drops them. Never call `slint.load_file` elsewhere.
	"""
	key = (name, _currentStyle)
	module = _SLINT_CACHE.get(key)
	if module is None:
		module = slint.load_file(str(_PKG_DIR / name), style=_currentStyle or None)
		_SLINT_CACHE[key] = module
	return module


def clearSlintCache() -> None:
	"""Event-loop thread only, followed by `gc.collect()` there (see load_slint)."""
	_SLINT_CACHE.clear()


def weakCallback(method: Any) -> Callable[..., Any]:
	"""
	Wrap a bound method for a slint callback slot without keeping its receiver
	alive. A component holds its slots strongly, so a plain bound method makes
	the cycle component -> callback -> controller -> component, which only a
	main-thread cyclic GC would free (keeping a closed window alive until then).
	The receiver must be a weak-referenceable Python object, not a slint one.
	"""
	ref = weakref.ref(method.__self__)
	func = method.__func__

	def wrapper(*args: Any) -> Any:
		obj = ref()
		return None if obj is None else func(obj, *args)

	return wrapper


# plain hex strings: the log handler may run on a worker thread
_LEVEL_COLORS: dict[str, str] = {
	"CRITICAL": "#ff5555",
	"ERROR": "#ff5555",
	"WARNING": "#ffb86c",
	"INFO": "#50fa7b",
	"DEBUG": "#8be9fd",
	"TRACE": "#cccccc",
}


def levelColor(levelName: str) -> str:
	return _LEVEL_COLORS.get(levelName, "#f8f8f2")


# ---------------------------------------------------------------------
# Native file dialogs, run out-of-process (osascript / PowerShell WinForms /
# zenity or kdialog): a nested modal loop in-process (e.g. tkinter's
# filedialog) inside a slint callback panics winit ("tried to handle event
# while another event is currently being handled"). Return "" on cancel or
# when no tool is available (the path can still be typed in).
# ---------------------------------------------------------------------
def _runCapture(args: list[str]) -> str:
	# CREATE_NO_WINDOW: powershell.exe would otherwise flash a console window
	# from our windowless GUI process
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
		return ""
	except Exception:
		log.exception("file dialog subprocess failed")
		return ""
	return proc.stdout.strip() if proc.returncode == 0 else ""


def pickFile(save: bool, initialdir: str) -> str:
	if not isdir(initialdir):
		initialdir = homeDir
	what = "output" if save else "input"
	if sysName == "darwin":
		verb = "choose file name" if save else "choose file"
		escaped = initialdir.replace("\\", "\\\\").replace('"', '\\"')
		return _runCapture(
			[
				"osascript",
				"-e",
				(
					f'POSIX path of ({verb} with prompt "Select {what} file"'
					f' default location (POSIX file "{escaped}"))'
				),
			],
		)
	if sysName == "windows":
		cls = "SaveFileDialog" if save else "OpenFileDialog"
		escaped = initialdir.replace("'", "''")
		return _runCapture(
			[
				"powershell.exe",
				"-NoProfile",
				"-Command",
				(
					"Add-Type -AssemblyName System.Windows.Forms;"
					f"$d = New-Object System.Windows.Forms.{cls};"
					f"$d.Title = 'Select {what} file';"
					"$d.Filter = 'All files (*.*)|*.*';"
					f"$d.InitialDirectory = '{escaped}';"
					"if ($d.ShowDialog() -eq 'OK') { $d.FileName }"
				),
			],
		)
	if shutil.which("zenity"):
		# trailing separator: start in the directory, don't pre-fill it as name
		return _runCapture(
			[
				"zenity",
				"--file-selection",
				*(["--save"] if save else []),
				f"--filename={join(initialdir, '')}",
			],
		)
	if shutil.which("kdialog"):
		flag = "--getsavefilename" if save else "--getopenfilename"
		return _runCapture(["kdialog", flag, initialdir])
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
	try:
		with open(_FCD_SAVE_PATH, mode="w", encoding="utf-8") as fp:
			fp.write(dirname(path))
	except Exception:
		log.exception("")
