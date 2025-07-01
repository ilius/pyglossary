from __future__ import annotations

import os
import platform
import sys
from os.path import (
	abspath,
	dirname,
	exists,
	isdir,
	isfile,
	join,
)

from . import logger
from .logger import TRACE, trace


def exc_note(e: Exception, note: str) -> Exception:
	try:
		e.add_note(note)  # pyright: ignore[reportAttributeAccessIssue]
	except AttributeError:
		if hasattr(e, "msg"):
			e.msg += "\n" + note  # pyright: ignore[reportAttributeAccessIssue]
	return e


__all__ = [
	"TRACE",
	"VERSION",
	"appResDir",
	"cacheDir",
	"checkCreateConfDir",
	"confDir",
	"confJsonFile",
	"dataDir",
	"getDataDir",
	"homeDir",
	"homePage",
	"isDebug",
	"log",
	"noColor",
	"pip",
	"pluginsDir",
	"rootConfJsonFile",
	"rootDir",
	"sysName",
	"tmpDir",
	"trace",
	"uiDir",
	"userPluginsDir",
]


VERSION = "5.1.0"

homePage = "https://github.com/ilius/pyglossary"

noColor = False


def checkCreateConfDir() -> None:
	if not isdir(confDir):
		if exists(confDir):  # file, or anything other than directory
			os.rename(confDir, confDir + ".bak")  # we do not import old config
		os.mkdir(confDir)
	if not exists(userPluginsDir):
		try:
			os.mkdir(userPluginsDir)
		except Exception as e:
			log.warning(f"failed to create user plugins directory: {e}")
	if not isfile(confJsonFile):
		with (
			open(rootConfJsonFile, encoding="utf-8") as srcF,
			open(confJsonFile, "w", encoding="utf-8") as usrF,
		):
			usrF.write(srcF.read())


def _in_virtualenv() -> bool:
	if hasattr(sys, "real_prefix"):
		return True
	return hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix


def getDataDir() -> str:
	if _in_virtualenv():
		pass  # TODO
		# print(f"prefix={sys.prefix}, base_prefix={sys.base_prefix}")
		# return join(
		# 	dirname(dirname(dirname(rootDir))),
		# 	os.getenv("VIRTUAL_ENV"), "share", "pyglossary",
		# )

	if not rootDir.endswith(("dist-packages", "site-packages")):
		return rootDir

	parent3 = dirname(dirname(dirname(rootDir)))
	if os.sep == "/":
		return join(parent3, "share", "pyglossary")

	direc = join(
		parent3,
		f"Python{sys.version_info.major}{sys.version_info.minor}",
		"share",
		"pyglossary",
	)
	if isdir(direc):
		return direc

	direc = join(parent3, "Python3", "share", "pyglossary")
	if isdir(direc):
		return direc

	direc = join(parent3, "Python", "share", "pyglossary")
	if isdir(direc):
		return direc

	direc = join(sys.prefix, "share", "pyglossary")
	if isdir(direc):
		return direc

	if CONDA_PREFIX := os.getenv("CONDA_PREFIX"):
		direc = join(CONDA_PREFIX, "share", "pyglossary")
		if isdir(direc):
			return direc

	raise OSError("failed to detect dataDir")


# __________________________________________________________________________ #

log = logger.setupLogging()


def isDebug() -> bool:
	return log.getVerbosity() >= 4  # noqa: PLR2004


sysName = platform.system().lower()
# platform.system() is in	["Linux", "Windows", "Darwin", "FreeBSD"]
# sysName is in				["linux", "windows", "darwin', "freebsd"]


# can set env var WARNINGS to:
# "error", "ignore", "always", "default", "module", "once"
if WARNINGS := os.getenv("WARNINGS"):
	if WARNINGS in {"default", "error", "ignore", "always", "module", "once"}:
		import warnings

		warnings.filterwarnings(WARNINGS)  # type: ignore # noqa: PGH003
	else:
		log.error(f"invalid env var {WARNINGS = }")


if getattr(sys, "frozen", False):
	# PyInstaller frozen executable
	log.info(f"sys.frozen = {getattr(sys, 'frozen', False)}")
	rootDir = dirname(sys.executable)
	uiDir = join(rootDir, "pyglossary", "ui")
else:
	_srcDir = dirname(abspath(__file__))
	uiDir = join(_srcDir, "ui")
	rootDir = dirname(_srcDir)

dataDir = getDataDir()
appResDir = join(dataDir, "res")

if os.sep == "/":  # Operating system is Unix-Like
	homeDir = os.getenv("HOME", "/")
	tmpDir = os.getenv("TMPDIR", "/tmp")  # noqa: S108
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
	else:  # GNU/Linux, Termux, FreeBSD, etc
		# should switch to "$XDG_CONFIG_HOME/pyglossary" in version 6.0.0
		# which generally means ~/.config/pyglossary
		confDir = join(homeDir, ".pyglossary")
		cacheDir = join(homeDir, ".cache", "pyglossary")
		pip = "pip3" if "/com.termux/" in homeDir else "sudo pip3"
elif os.sep == "\\":  # Operating system is Windows
	# FIXME: default values
	_homeDrive = os.getenv("HOMEDRIVE", "")
	_homePath = os.getenv("HOMEPATH", "")
	homeDir = join(_homeDrive, _homePath)
	tmpDir = os.getenv("TEMP", "")
	_appData = os.getenv("APPDATA", "")
	confDir = join(_appData, "PyGlossary")
	# Windows Vista or older do not have LOCALAPPDATA
	_localAppData = os.getenv("LOCALAPPDATA") or abspath(join(_appData, "..", "Local"))
	cacheDir = join(_localAppData, "PyGlossary", "Cache")
	pip = "pip3"
else:
	raise RuntimeError(
		f"Unknown path separator(os.sep=={os.sep!r}), unknown operating system!",
	)

pluginsDir = join(rootDir, "pyglossary", "plugins")
confJsonFile = join(confDir, "config.json")
rootConfJsonFile = join(dataDir, "config.json")
userPluginsDir = join(confDir, "plugins")
