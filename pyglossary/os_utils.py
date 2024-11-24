from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pyglossary import core

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import TracebackType

__all__ = ["indir", "rmtree", "runDictzip", "showMemoryUsage"]

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
		self.old_pwd: str | None = None
		self.dir = directory
		self.create = create
		self.clear = clear

	def __enter__(self) -> None:
		self.old_pwd = os.getcwd()
		if os.path.exists(self.dir):
			if self.clear:
				shutil.rmtree(self.dir)
				os.makedirs(self.dir)
		elif self.create:
			os.makedirs(self.dir)
		os.chdir(self.dir)

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_val: BaseException | None,
		exc_tb: TracebackType | None,
	) -> None:
		if self.old_pwd:
			os.chdir(self.old_pwd)
		self.old_pwd = None


def _idzip(filename: str | Path) -> bool:
	try:
		from idzip import compressor
	except ModuleNotFoundError:
		return False
	filename = Path(filename)
	destination = filename.parent / (filename.name + ".dz")
	try:
		with open(filename, "rb") as inp_file, open(destination, "wb") as out_file:
			inputInfo = os.fstat(inp_file.fileno())
			log.debug("compressing %s to %s with idzip", filename, destination)
			compressor.compress(
				inp_file,
				inputInfo.st_size,
				out_file,
				filename.name,
				int(inputInfo.st_mtime),
			)
		filename.unlink()
	except OSError as error:
		log.error(str(error))
	return True


def _dictzip(filename: str | Path) -> bool:
	import subprocess

	dictzipCmd = shutil.which("dictzip")
	if not dictzipCmd:
		return False
	log.debug(f"dictzip command: {dictzipCmd!r}")
	try:
		subprocess.run(
			[dictzipCmd, filename],
			check=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
		)
	except subprocess.CalledProcessError as proc_err:
		err_msg = proc_err.output.decode("utf-8").replace("\n", ";")
		retcode = proc_err.returncode
		log.error(f"dictzip exit {retcode}: {err_msg}")
	return True


def runDictzip(filename: str | Path, method: str = "") -> None:
	"""Compress file into dictzip format."""
	res = None
	if method in {"", "idzip"}:
		res = _idzip(filename)
	if not res and method in {"", "dictzip"}:
		res = _dictzip(filename)
	if not res:
		log.warning(
			"Dictzip compression requires idzip module or dictzip utility,"
			f" run `{core.pip} install python-idzip` to install or make sure"
			" dictzip is in your $PATH",
		)


def _rmtreeError(
	_func: Callable,
	_direc: str,
	exc_info: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
	if exc_info is None:
		return
	_, exc_val, _ = exc_info
	log.error(exc_val)


def _rmtreeException(
	_func: Callable,
	_direc: str,
	exc_val: BaseException,
) -> None:
	log.error(exc_val)


def _rmtree(direc: str) -> None:
	# in Python 3.12, onexc is added and onerror is deprecated
	# https://github.com/python/cpython/blob/main/Lib/shutil.py
	if sys.version_info < (3, 12):
		shutil.rmtree(direc, onerror=_rmtreeError)
		return
	shutil.rmtree(direc, onexc=_rmtreeException)


def rmtree(direc: str) -> None:
	from os.path import isdir

	try:
		for _ in range(2):
			if not isdir(direc):
				break
			_rmtree(direc)
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
