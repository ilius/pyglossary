from __future__ import annotations

import inspect
import logging
import os
import sys
import traceback
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import TracebackType
	from typing import (
		Any,
		TypeAlias,
	)

	ExcInfoType: TypeAlias = (
		tuple[type[BaseException], BaseException, TracebackType]
		| tuple[None, None, None]
	)


__all__ = [
	"TRACE",
	"StdLogHandler",
	"format_exception",
]

TRACE = 5
logging.addLevelName(TRACE, "TRACE")


class _Formatter(logging.Formatter):
	def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
		logging.Formatter.__init__(self, *args, **kwargs)
		self.fill: Callable[[str], str] | None = None

	def formatMessage(
		self,
		record: logging.LogRecord,
	) -> str:
		msg = logging.Formatter.formatMessage(self, record)
		if self.fill is not None:
			msg = self.fill(msg)
		return msg  # noqa: RET504


class Logger(logging.Logger):
	levelsByVerbosity = (
		logging.CRITICAL,
		logging.ERROR,
		logging.WARNING,
		logging.INFO,
		logging.DEBUG,
		TRACE,
		logging.NOTSET,
	)
	levelNamesCap = (
		"Critical",
		"Error",
		"Warning",
		"Info",
		"Debug",
		"Trace",
		"All",  # "Not-Set",
	)

	def __init__(self, *args) -> None:  # noqa: ANN101, ANN002
		logging.Logger.__init__(self, *args)
		self._verbosity = 3
		self._timeEnable = False

	def setVerbosity(self, verbosity: int) -> None:
		self.setLevel(self.levelsByVerbosity[verbosity])
		self._verbosity = verbosity

	def getVerbosity(self) -> int:
		return self._verbosity

	def trace(self, msg: str) -> None:
		self.log(TRACE, msg)

	def pretty(self, data: Any, header: str = "") -> None:  # noqa: ANN401
		from pprint import pformat

		self.debug(header + pformat(data))

	def newFormatter(self) -> _Formatter:
		timeEnable = self._timeEnable
		if timeEnable:
			fmt = "%(asctime)s [%(levelname)s] %(message)s"
		else:
			fmt = "[%(levelname)s] %(message)s"
		return _Formatter(fmt)

	def setTimeEnable(self, timeEnable: bool) -> None:
		self._timeEnable = timeEnable
		formatter = self.newFormatter()
		for handler in self.handlers:
			handler.setFormatter(formatter)

	def addHandler(self, hdlr: logging.Handler) -> None:
		# if want to add separate format (new config keys and flags) for ui_gtk
		# and ui_tk, you need to remove this function and run handler.setFormatter
		# in ui_gtk and ui_tk
		logging.Logger.addHandler(self, hdlr)
		hdlr.setFormatter(self.newFormatter())


def _formatVarDict(
	dct: dict[str, Any],
	indent: int = 4,
	max_width: int = 80,
) -> str:
	lines = []
	pre = " " * indent
	for key, value in dct.items():
		line = pre + key + " = " + repr(value)
		if len(line) > max_width:
			line = line[: max_width - 3] + "..."
			try:
				value_len = len(value)
			except TypeError:
				pass
			else:
				line += f"\n{pre}len({key}) = {value_len}"
		lines.append(line)
	return "\n".join(lines)


def format_exception(
	exc_info: ExcInfoType | None = None,
	add_locals: bool = False,
	add_globals: bool = False,
) -> str:
	if exc_info is None:
		exc_info = sys.exc_info()
	type_, value, tback = exc_info
	text = "".join(traceback.format_exception(type_, value, tback))

	if tback is None:
		return text

	if add_locals or add_globals:
		try:
			frame = inspect.getinnerframes(tback, context=0)[-1][0]
		except IndexError:
			pass
		else:
			if add_locals:
				text += f"Traceback locals:\n{_formatVarDict(frame.f_locals)}\n"
			if add_globals:
				text += f"Traceback globals:\n{_formatVarDict(frame.f_globals)}\n"

	return text


class StdLogHandler(logging.Handler):
	colorsConfig = {
		"CRITICAL": ("color.cmd.critical", 196),
		"ERROR": ("color.cmd.error", 1),
		"WARNING": ("color.cmd.warning", 208),
	}
	# 1: dark red (like 31m), 196: real red, 9: light red
	# 15: white, 229: light yellow (#ffffaf), 226: real yellow (#ffff00)

	def __init__(self, noColor: bool = False) -> None:
		logging.Handler.__init__(self)
		self.set_name("std")
		self.noColor = noColor
		self.config: dict[str, Any] = {}

	@property
	def endFormat(self) -> str:
		if self.noColor:
			return ""
		return "\x1b[0;0;0m"

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		###
		if record.exc_info:
			type_, value, tback = record.exc_info
			if type_ and tback and value:  # to fix mypy error
				tback_text = format_exception(
					exc_info=(type_, value, tback),
					add_locals=(self.level <= logging.DEBUG),
					add_globals=False,
				)
				if not msg:
					msg = "unhandled exception:"
				msg += "\n"
				msg += tback_text
		###
		levelname = record.levelname

		fp = sys.stderr if levelname in {"CRITICAL", "ERROR"} else sys.stdout

		if not self.noColor and levelname in self.colorsConfig:
			key, default = self.colorsConfig[levelname]
			colorCode = self.config.get(key, default)
			startColor = f"\x1b[38;5;{colorCode}m"
			msg = startColor + msg + self.endFormat

		###
		if fp is None:
			print(f"fp=None, levelname={record.levelname}")  # noqa: T201
			print(msg)  # noqa: T201
			return
		fp.write(msg + "\n")
		fp.flush()


def setupLogging() -> Logger:
	logging.setLoggerClass(Logger)
	log = cast("Logger", logging.getLogger("pyglossary"))

	if os.sep == "\\":

		def _windows_show_exception(
			type_: type[BaseException],
			exc: BaseException,
			tback: TracebackType | None,
		) -> None:
			if not (type_ and exc and tback):
				return
			import ctypes

			msg = format_exception(
				exc_info=(type_, exc, tback),
				add_locals=(log.level <= logging.DEBUG),
				add_globals=False,
			)
			log.critical(msg)
			ctypes.windll.user32.MessageBoxW(0, msg, "PyGlossary Error", 0)  # type: ignore

		sys.excepthook = _windows_show_exception

	else:

		def _unix_show_exception(
			type_: type[BaseException],
			exc: BaseException,
			tback: TracebackType | None,
		) -> None:
			if not (type_ and exc and tback):
				return
			log.critical(
				format_exception(
					exc_info=(type_, exc, tback),
					add_locals=(log.level <= logging.DEBUG),
					add_globals=False,
				),
			)

		sys.excepthook = _unix_show_exception

	return log
