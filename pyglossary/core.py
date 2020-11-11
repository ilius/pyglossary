import logging
import traceback
import inspect
import sys
import os
from os.path import (
	join,
	isfile,
	isdir,
	exists,
	realpath,
	dirname,
)
import platform

VERSION = "4.0.7"


TRACE = 5
logging.addLevelName(TRACE, "TRACE")


class Formatter(logging.Formatter):
	def __init__(self, *args, **kwargs):
		logging.Formatter.__init__(self, *args, **kwargs)
		self.fill = None  # type: Optional[Callable[[str], str]]

	def formatMessage(self, record):
		msg = logging.Formatter.formatMessage(self, record)
		if self.fill is not None:
			msg = self.fill(msg)
		return msg


class MyLogger(logging.Logger):
	levelsByVerbosity = (
		logging.CRITICAL,
		logging.ERROR,
		logging.WARNING,
		logging.INFO,
		logging.DEBUG,
		TRACE,
		logging.NOTSET,
	)
	levelNamesCap = [
		"Critical",
		"Error",
		"Warning",
		"Info",
		"Debug",
		"Trace",
		"All",  # "Not-Set",
	]

	def __init__(self, *args):
		logging.Logger.__init__(self, *args)
		self._verbosity = 3
		self._timeEnable = False

	def setVerbosity(self, verbosity: int) -> None:
		self.setLevel(self.levelsByVerbosity[verbosity])
		self._verbosity = verbosity

	def getVerbosity(self) -> int:
		return self._verbosity

	def trace(self, msg: str):
		self.log(TRACE, msg)

	def pretty(self, data: "Any", header: str = "") -> None:
		from pprint import pformat
		self.debug(header + pformat(data))

	def isDebug(self) -> bool:
		return self.getVerbosity() >= 4

	def newFormatter(self):
		timeEnable = self._timeEnable
		if timeEnable:
			fmt = "%(asctime)s [%(levelname)s] %(message)s"
		else:
			fmt = "[%(levelname)s] %(message)s"
		return Formatter(fmt)

	def setTimeEnable(self, timeEnable: bool):
		self._timeEnable = timeEnable
		formatter = self.newFormatter()
		for handler in self.handlers:
			handler.setFormatter(formatter)

	def addHandler(self, handler: "logging.Handler"):
		# if want to add separate format (new config keys and flags) for ui_gtk
		# and ui_tk, you need to remove this function and run handler.setFormatter
		# in ui_gtk and ui_tk
		logging.Logger.addHandler(self, handler)
		handler.setFormatter(self.newFormatter())


def formatVarDict(
	dct: "Dict[str, Any]",
	indent: int = 4,
	max_width: int = 80,
) -> str:
	lines = []
	pre = " " * indent
	for key, value in dct.items():
		line = pre + key + " = " + repr(value)
		if len(line) > max_width:
			line = line[:max_width - 3] + "..."
			try:
				value_len = len(value)
			except TypeError:
				pass
			else:
				line += f"\n{pre}len({key}) = {value_len}"
		lines.append(line)
	return "\n".join(lines)


def format_exception(
	exc_info: "Optional[Tuple[Type, Exception, types.TracebackType]]" = None,
	add_locals: bool = False,
	add_globals: bool = False,
) -> str:
	if not exc_info:
		exc_info = sys.exc_info()
	_type, value, tback = exc_info
	text = "".join(traceback.format_exception(_type, value, tback))

	if add_locals or add_globals:
		try:
			frame = inspect.getinnerframes(tback, context=0)[-1][0]
		except IndexError:
			pass
		else:
			if add_locals:
				text += f"Traceback locals:\n{formatVarDict(frame.f_locals)}\n"
			if add_globals:
				text += f"Traceback globals:\n{formatVarDict(frame.f_globals)}\n"

	return text


class StdLogHandler(logging.Handler):
	def __init__(self, noColor: bool = False):
		logging.Handler.__init__(self)
		self.set_name("std")
		self.noColor = noColor

	@property
	def startRed(self):
		if self.noColor:
			return ""
		return "\x1b[31m"

	@property
	def endFormat(self):
		if self.noColor:
			return ""
		return "\x1b[0;0;0m"

	def emit(self, record: logging.LogRecord) -> None:
		msg = ""
		if record.getMessage():
			msg = self.format(record)
		###
		if record.exc_info:
			_type, value, tback = record.exc_info
			tback_text = format_exception(
				exc_info=record.exc_info,
				add_locals=(log.level <= logging.DEBUG),  # FIXME
				add_globals=False,
			)

			if not msg:
				msg = "unhandled exception:"
			msg += "\n"
			msg += tback_text
		###
		if record.levelname in ("CRITICAL", "ERROR"):
			if msg and not self.noColor:
				msg = self.startRed + msg + self.endFormat
			fp = sys.stderr
		else:
			fp = sys.stdout
		###
		fp.write(msg + "\n")
		fp.flush()


def checkCreateConfDir() -> None:
	if not isdir(confDir):
		if exists(confDir):  # file, or anything other than directory
			os.rename(confDir, confDir + ".bak")  # we do not import old config
		os.mkdir(confDir)
	if not exists(userPluginsDir):
		os.mkdir(userPluginsDir)
	if not isfile(confJsonFile):
		with open(rootConfJsonFile) as srcF, open(confJsonFile, "w") as usrF:
			usrF.write(srcF.read())


# __________________________________________________________________________ #

logging.setLoggerClass(MyLogger)
log = logging.getLogger("pyglossary")

sys.excepthook = lambda *exc_info: log.critical(
	format_exception(
		exc_info=exc_info,
		add_locals=(log.level <= logging.DEBUG),  # FIXME
		add_globals=False,
	)
)

sysName = platform.system().lower()
# platform.system() is in	["Linux", "Windows", "Darwin", "FreeBSD"]
# sysName is in				["linux", "windows", "darwin', "freebsd"]


# can set env var WARNINGS to:
# "error", "ignore", "always", "default", "module", "once"
if os.getenv("WARNINGS"):
	import warnings
	warnings.filterwarnings(os.getenv("WARNINGS"))


if hasattr(sys, "frozen"):
	# FIXME: was this for py2exe?
	log.info(f"sys.frozen = {sys.frozen}")
	rootDir = dirname(sys.executable)
	uiDir = join(rootDir, "pyglossary", "ui")
else:
	_srcDir = dirname(realpath(__file__))
	uiDir = join(_srcDir, "ui")
	rootDir = dirname(_srcDir)

dataDir = rootDir
if dataDir.endswith("dist-packages") or dataDir.endswith("site-packages"):
	parent3 = dirname(dirname(dirname(rootDir)))
	if os.sep == "\\":
		dataDir = join(parent3, "Python", "share", "pyglossary")
	else:
		dataDir = join(parent3, "share", "pyglossary")

appResDir = join(dataDir, "res")

if os.sep == "/":  # Operating system is Unix-Like
	homeDir = os.getenv("HOME")
	user = os.getenv("USER")
	tmpDir = "/tmp"
	# os.name == "posix" # FIXME
	if sysName == "darwin":  # MacOS X
		_libDir = join(homeDir, "Library")
		confDir = join(_libDir, "Preferences", "PyGlossary")
		# or maybe: join(_libDir, "PyGlossary")
		# os.environ["OSTYPE"] == "darwin10.0"
		# os.environ["MACHTYPE"] == "x86_64-apple-darwin10.0"
		# platform.dist() == ("", "", "")
		# platform.release() == "10.3.0"
		cacheDir = join(_libDir, "Caches", "PyGlossary")
		pip = "pip3"
	else:  # GNU/Linux, ...
		confDir = join(homeDir, ".pyglossary")
		cacheDir = join(homeDir, ".cache", "pyglossary")
		pip = "sudo pip3"
elif os.sep == "\\":  # Operating system is Windows
	homeDir = join(os.getenv("HOMEDRIVE"), os.getenv("HOMEPATH"))
	user = os.getenv("USERNAME")
	tmpDir = os.getenv("TEMP")
	confDir = join(os.getenv("APPDATA"), "PyGlossary")
	cacheDir = join(confDir, "Cache")  # FIXME: right directory?
	pip = "pip3"
else:
	raise RuntimeError(
		f"Unknown path seperator(os.sep=={os.sep!r})"
		f", unknown operating system!"
	)

confJsonFile = join(confDir, "config.json")
rootConfJsonFile = join(dataDir, "config.json")
userPluginsDir = join(confDir, "plugins")
