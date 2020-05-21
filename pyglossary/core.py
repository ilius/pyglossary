import logging
import traceback
import inspect
from pprint import pformat
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

from typing import (
	Dict,
	Tuple,
	Any,
	Optional,
	Type,
)

from types import TracebackType

VERSION = "3.3.0"

class MyLogger(logging.Logger):
	levelsByVerbosity = (
		logging.CRITICAL,
		logging.ERROR,
		logging.WARNING,
		logging.INFO,
		logging.DEBUG,
		logging.NOTSET,
	)
	levelNamesCap = [
		"Critical",
		"Error",
		"Warning",
		"Info",
		"Debug",
		"All",  # "Not-Set",
	]

	def setVerbosity(self, verbosity: int) -> None:
		self.setLevel(self.levelsByVerbosity[verbosity])
		self._verbosity = verbosity

	def getVerbosity(self) -> int:
		return getattr(self, "_verbosity", 3)  # FIXME

	def pretty(self, data: Any, header: str = "") -> None:
		self.debug(header + pformat(data))

	def isDebug(self) -> bool:
		return self.getVerbosity() >= 4

def format_var_dict(dct: Dict[str, Any], indent: int = 4, max_width: int = 80) -> str:
	lines = []
	pre = " " * indent
	for key, value in dct.items():
		line = pre + key + " = " + repr(value)
		if len(line) > max_width:
			line = line[:max_width-3] + "..."
			try:
				value_len = len(value)
			except:
				pass
			else:
				line += "\n" + pre + "len(%s) = %s"%(key, value_len)
		lines.append(line)
	return "\n".join(lines)


def format_exception(
	exc_info: Optional[Tuple[Type, Exception, TracebackType]] = None,
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
				text += "Traceback locals:\n%s\n" % format_var_dict(
					frame.f_locals,
				)
			if add_globals:
				text += "Traceback globals:\n%s\n" % format_var_dict(
					frame.f_globals,
				)

	return text


class StdLogHandler(logging.Handler):
	startRed = "\x1b[31m"
	endFormat = "\x1b[0;0;0m"  # len=8

	def __init__(self, noColor: bool = False):
		logging.Handler.__init__(self)
		self.noColor = noColor

	def emit(self, record: logging.LogRecord) -> None:
		msg = record.getMessage()
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
			if not self.noColor:
				msg = self.startRed + msg + self.endFormat
			fp = sys.stderr
		else:
			fp = sys.stdout
		###
		fp.write(msg + "\n")
		fp.flush()

#	def exception(self, msg: str) -> None:
#		if not self.noColor:
#			msg = self.startRed + msg + self.endFormat
#		sys.stderr.write(msg + "\n")
#		sys.stderr.flush()


def checkCreateConfDir() -> None:
	if not isdir(confDir):
		if exists(confDir):  # file, or anything other than directory
			os.rename(confDir, confDir + ".bak")  # we do not import old config
		os.mkdir(confDir)
	if not exists(userPluginsDir):
		os.mkdir(userPluginsDir)
	if not isfile(confJsonFile):
		with open(rootConfJsonFile) as srcFp, \
		  open(confJsonFile, "w") as userFp:
			userFp.write(srcFp.read())


# __________________________________________________________________________ #

logging.setLoggerClass(MyLogger)
log = logging.getLogger("root")

sys.excepthook = lambda *exc_info: log.critical(
	format_exception(
		exc_info=exc_info,
		add_locals=(log.level <= logging.DEBUG),  # FIXME
		add_globals=False,
	)
)

sysName = platform.system()

# can set env var WARNINGS to: "error", "ignore", "always", "default", "module", "once"
if os.getenv("WARNINGS"):
	import warnings
	warnings.filterwarnings(os.getenv("WARNINGS"))


if hasattr(sys, "frozen"):
	rootDir = dirname(sys.executable)
	uiDir = join(rootDir, "ui")
else:
	uiDir = dirname(realpath(__file__))
	rootDir = dirname(uiDir)

dataDir = rootDir
if dataDir.endswith("dist-packages") or dataDir.endswith("site-packages"):
	dataDir = dirname(sys.argv[0])

appResDir = join(dataDir, "res")

if os.sep == "/":  # Operating system is Unix-Like
	homeDir = os.getenv("HOME")
	user = os.getenv("USER")
	tmpDir = "/tmp"
	# os.name == "posix" # FIXME
	if sysName == "Darwin":  # MacOS X
		confDir = homeDir + "/Library/Preferences/PyGlossary"
		# or maybe: homeDir + "/Library/PyGlossary"
		# os.environ["OSTYPE"] == "darwin10.0"
		# os.environ["MACHTYPE"] == "x86_64-apple-darwin10.0"
		# platform.dist() == ("", "", "")
		# platform.release() == "10.3.0"
	else:  # GNU/Linux, ...
		confDir = homeDir + "/.pyglossary"
elif os.sep == "\\":  # Operating system is Windows
	homeDir = os.getenv("HOMEDRIVE") + os.getenv("HOMEPATH")
	user = os.getenv("USERNAME")
	tmpDir = os.getenv("TEMP")
	confDir = os.getenv("APPDATA") + "\\" + "PyGlossary"
else:
	raise RuntimeError(
		"Unknown path seperator(os.sep==%r)" % os.sep +
		", unknown operating system!"
	)

confJsonFile = join(confDir, "config.json")
rootConfJsonFile = join(dataDir, "config.json")
userPluginsDir = join(confDir, "plugins")
