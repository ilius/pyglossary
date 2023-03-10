import logging
import os
import shutil
import types
from typing import Any, Callable, Type

from pyglossary import core

log = logging.getLogger("pyglossary")


class indir(object):
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
		exc_type: "Type",
		exc_val: "Exception",
		exc_tb: "types.TracebackType",
	) -> None:
		if self.oldpwd:
			os.chdir(self.oldpwd)
		self.oldpwd = None


def runDictzip(filename: str) -> None:
	import shutil
	import subprocess
	dictzipCmd = shutil.which("dictzip")
	if not dictzipCmd:
		log.warning("dictzip command was not found. Make sure it's in your $PATH")
		return
	b_out, b_err = subprocess.Popen(
		[dictzipCmd, filename],
		stdout=subprocess.PIPE,
	).communicate()
	log.debug(f"dictzip command: {dictzipCmd!r}")
	if b_err:
		err = b_err.decode("utf-8").replace('\n', ' ')
		log.error(f"dictzip error: {err}")
	if b_out:
		out = b_out.decode("utf-8").replace('\n', ' ')
		log.error(f"dictzip error: {out}")


def _rmtreeError(
	func: "Callable",
	direc: str,
	exc_info: "tuple[Type, Exception, types.TracebackType] | None",
) -> None:
	if exc_info is None:
		return
	_, exc_val, _ = exc_info
	log.error(exc_val)


def rmtree(direc: str) -> None:
	import shutil
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
	log.trace(f"Memory Usage: {usage:,} kB")


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


"""
try:
	from gnome import url_show
except:
	try:
		from gnomevfs import url_show
	except:
		url_show = my_url_show
"""


def click_website(widget: "Any", link: str) -> None:
	my_url_show(link)
