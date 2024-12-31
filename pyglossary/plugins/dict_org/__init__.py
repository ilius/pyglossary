# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import re
from os.path import isdir, splitext
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.flags import DEFAULT_NO
from pyglossary.option import BoolOption, Option
from pyglossary.plugin_lib.dictdlib import DictDB

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = [
	"Reader",
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "dict_org"
name = "DictOrg"
description = "DICT.org file format (.index)"
extensions = (".index",)
extensionCreate = ""
singleFile = False
optionsProp: dict[str, Option] = {
	"dictzip": BoolOption(comment="Compress .dict file to .dict.dz"),
	"install": BoolOption(comment="Install dictionary to /usr/share/dictd/"),
}
sortOnWrite = DEFAULT_NO
kind = "directory"
wiki = "https://en.wikipedia.org/wiki/DICT#DICT_file_format"
website = (
	"http://dict.org/bin/Dict",
	"The DICT Development Group",
)


def installToDictd(filename: str, dictzip: bool) -> None:
	"""Filename is without extension (neither .index or .dict or .dict.dz)."""
	import shutil
	import subprocess

	targetDir = "/usr/share/dictd/"
	if filename.startswith(targetDir):
		return

	if not isdir(targetDir):
		log.warning(f"Directory {targetDir!r} does not exist, skipping install")
		return

	log.info(f"Installing {filename!r} to DICTD server directory: {targetDir}")

	if dictzip and os.path.isfile(filename + ".dict.dz"):
		dictExt = ".dict.dz"
	elif os.path.isfile(filename + ".dict"):
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


class Reader:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dictdb: DictDB | None = None

		# regular expression patterns used to prettify definition text
		self._re_newline_in_braces = re.compile(
			r"\{(?P<left>.*?)\n(?P<right>.*?)?\}",
		)
		self._re_words_in_braces = re.compile(
			r"\{(?P<word>.+?)\}",
		)

	def open(self, filename: str) -> None:
		filename = filename.removesuffix(".index")
		self._filename = filename
		self._dictdb = DictDB(filename, "read", 1)

	def close(self) -> None:
		if self._dictdb is not None:
			self._dictdb.close()
			# self._dictdb.finish()
			self._dictdb = None

	def prettifyDefinitionText(self, defi: str) -> str:
		# Handle words in {}
		# First, we remove any \n in {} pairs
		defi = self._re_newline_in_braces.sub(r"{\g<left>\g<right>}", defi)

		# Then, replace any {words} into <a href="bword://words">words</a>,
		# so it can be rendered as link correctly
		defi = self._re_words_in_braces.sub(
			r'<a href="bword://\g<word>">\g<word></a>',
			defi,
		)

		# Use <br /> so it can be rendered as newline correctly
		return defi.replace("\n", "<br />")

	def __len__(self) -> int:
		if self._dictdb is None:
			return 0
		return len(self._dictdb)

	def __iter__(self) -> Iterator[EntryType]:
		if self._dictdb is None:
			raise RuntimeError("iterating over a reader while it's not open")
		dictdb = self._dictdb
		for word in dictdb.getDefList():
			b_defi = b"\n\n<hr>\n\n".join(dictdb.getDef(word))
			try:
				defi = b_defi.decode("utf_8", "ignore")
				defi = self.prettifyDefinitionText(defi)
			except Exception as e:
				log.error(f"{b_defi = }")
				raise e
			yield self._glos.newEntry(word, defi)


class Writer:
	_dictzip: bool = False
	_install: bool = True

	def __init__(self, glos: GlossaryType) -> None:
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
			installToDictd(
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
