import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Union

from pyglossary import core

if TYPE_CHECKING:
	import types

log = logging.getLogger("pyglossary")


class indir:

	"""
	mkdir + chdir shortcut to use with `with` statement.

	>>> print(os.getcwd())  # -> "~/projects"
	>>> with indir('my_directory', create=True):
	>>>     print(os.getcwd())  # -> "~/projects/my_directory"
	>>>     # do some work inside new 'my_directory'...
	>>> print(os.getcwd())  # -> "~/projects"
	>>> # automatically return to previous directory.
	"""

	def __init__(
		self,
		directory: str,
		create: bool = False,
		clear: bool = False,
	) -> None:
		self.oldpwd: "str | None" = None
		self.dir = directory
		self.create = create
		self.clear = clear

	def __enter__(self) -> None:
		self.oldpwd = os.getcwd()
		if os.path.exists(self.dir):
			if self.clear:
				shutil.rmtree(self.dir)
				os.makedirs(self.dir)
		elif self.create:
			os.makedirs(self.dir)
		os.chdir(self.dir)

	def __exit__(
		self,
		exc_type: "type",
		exc_val: "Exception",
		exc_tb: "types.TracebackType",
	) -> None:
		if self.oldpwd:
			os.chdir(self.oldpwd)
		self.oldpwd = None


def _idzip(filename: Union[str, Path]) -> bool:
	try:
		import idzip
	except ModuleNotFoundError:
		return False
	filename = Path(filename)
	destination = filename.parent/(filename.name + ".dz")
	try:
		with open(filename, "rb") as inp_file, open(destination, "wb") as out_file:
			inputinfo = os.fstat(inp_file.fileno())
			log.debug("compressing %s to %s with idzip", filename, destination)
			idzip.compressor.compress(
				inp_file,
				inputinfo.st_size,
				out_file,
				filename.name,
				int(inputinfo.st_mtime))
		filename.unlink()
	except OSError as error:
		log.error(str(error))
	return True


def _dictzip(filename: str) -> bool:
	import subprocess
	dictzipCmd = shutil.which("dictzip")
	if not dictzipCmd:
		return False
	b_out, b_err = subprocess.Popen(
		[dictzipCmd, filename],
		stdout=subprocess.PIPE).communicate()
	log.debug(f"dictzip command: {dictzipCmd!r}")
	if b_err:
		err = b_err.decode("utf-8").replace('\n', ' ')
		log.error(f"dictzip error: {err}")
	if b_out:
		out = b_out.decode("utf-8").replace('\n', ' ')
		log.error(f"dictzip error: {out}")
	return True

def _nozip(filename: str) -> bool:
	log.warning(
		"Dictzip compression requires idzip module or dictzip utility,"
		f" run `{core.pip} install python-idzip` to install or make sure"
		" dictzip is in your $PATH")
	return False


def runDictzip(filename: str) -> None:
	"""Compress file into dictzip format."""
	for fun in (_idzip, _dictzip, _nozip):
		if fun(filename):
			return


def _rmtreeError(
	func: "Callable",
	direc: str,
	exc_info: "tuple[type, Exception, types.TracebackType] | None",
) -> None:
	if exc_info is None:
		return
	_, exc_val, _ = exc_info
	log.error(exc_val)


def rmtree(direc: str) -> None:
	from os.path import isdir
	try:
		for _ in range(2):
			if isdir(direc):
				shutil.rmtree(
					direc,
					onerror=_rmtreeError,
				)
	except Exception:
		log.exception(f"error removing directory: {direc}")


def showMemoryUsage() -> None:
	if log.level > core.TRACE:
		return
	try:
		import psutil
	except ModuleNotFoundError:
		return
	usage = psutil.Process(os.getpid()).memory_info().rss // 1024
	core.trace(log, f"Memory Usage: {usage:,} kB")


def my_url_show(link: str) -> None:
	import subprocess
	for path in (
		'/usr/bin/gnome-www-browser',
		'/usr/bin/firefox',
		'/usr/bin/iceweasel',
		'/usr/bin/konqueror',
	):
		if os.path.isfile(path):
			subprocess.call([path, link])
			break


# try:
# 	from gnome import url_show
# except:
# 	try:
# 		from gnomevfs import url_show
# 	except:
# 		url_show = my_url_show


def click_website(widget: "Any", link: str) -> None:
	my_url_show(link)
