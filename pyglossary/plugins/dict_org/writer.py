# -*- coding: utf-8 -*-

from __future__ import annotations

from os.path import splitext
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.plugin_lib.dictdlib import DictDB

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


def _installToDictd(filename: str, dictzip: bool) -> None:
	"""Filename is without extension (neither .index or .dict or .dict.dz)."""
	import shutil
	import subprocess
	from os.path import isdir, isfile

	targetDir = "/usr/share/dictd/"
	if filename.startswith(targetDir):
		return

	if not isdir(targetDir):
		log.warning(f"Directory {targetDir!r} does not exist, skipping install")
		return

	log.info(f"Installing {filename!r} to DICTD server directory: {targetDir}")

	if dictzip and isfile(filename + ".dict.dz"):
		dictExt = ".dict.dz"
	elif isfile(filename + ".dict"):
		dictExt = ".dict"
	else:
		log.error(f"No .dict file, could not install dictd file {filename!r}")
		return

	if not filename.startswith(targetDir):
		shutil.copy(filename + ".index", targetDir)
		shutil.copy(filename + dictExt, targetDir)

	# update /var/lib/dictd/db.list
	if subprocess.call(["/usr/sbin/dictdconfig", "-w"]) != 0:
		log.error(
			"failed to update /var/lib/dictd/db.list file"
			", try manually running: sudo /usr/sbin/dictdconfig -w",
		)

	log.info("don't forget to restart dictd server")


class Writer:
	_dictzip: bool = False
	_install: bool = True

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dictdb: DictDB | None = None

	def finish(self) -> None:
		from pyglossary.os_utils import runDictzip

		if self._dictdb is None:
			raise RuntimeError("self._dictdb is None")

		self._dictdb.finish(dosort=True)
		if self._dictzip:
			runDictzip(f"{self._filename}.dict")
		if self._install:
			_installToDictd(
				self._filename,
				self._dictzip,
			)
		self._filename = ""

	def open(self, filename: str) -> None:
		filename_nox, ext = splitext(filename)
		if ext.lower() == ".index":
			filename = filename_nox
		self._dictdb = DictDB(filename, "write", 1)
		self._filename = filename

	def write(self) -> Generator[None, EntryType, None]:
		dictdb = self._dictdb
		if dictdb is None:
			raise RuntimeError("self._dictdb is None")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# does dictd support resources? and how? FIXME
				continue
			dictdb.addEntry(entry.defi, entry.l_word)
