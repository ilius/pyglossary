# -*- coding: utf-8 -*-

from formats_common import *
import subprocess
from os.path import dirname

enable = True
format = "Treedict"
description = "TreeDict"
extensions = (".tree", ".treedict")
optionsProp = {
	"encoding": EncodingOption(),
	"archive": StrOption(
		customValue=False,
		values=[
			"tar.bz2",
			"tar.gz",
			"zip",
		],
	),
	"sep": StrOption(
		customValue=True,
		values=[
			"/",
			"\\",
		],
	),
	"length": IntOption(),
}


def chunkString(string, length):
    return (
    	string[0 + i:length + i]
    	for i in range(0, len(string), length)
	)


class Writer(object):
	_encoding: str = "utf-8"
	_sep: str = os.sep
	_length: int = 2

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def finish(self):
		self._filename = None

	def open(self, filename: str) -> None:
		self._filename = filename
		if os.path.exists(filename):
			if os.path.isdir(filename):
				if os.listdir(filename):
					log.warning(f"Warning: directory {filename!r} is not empty.")
			else:
				raise IOError(f"{filename!r} is not a directory")

	def write(self) -> "Generator[None, BaseEntry, None]":
		glos = self._glos
		filename = self._filename
		encoding = self._encoding
		sep = self._sep
		length = self._length

		maxDepth = 0
		while True:
			entry = yield
			if entry is None:
				break
			defi = entry.defi
			word = entry.s_word
			if not word:
				log.error("empty word")
				continue
			parts = list(chunkString(word, length))
			entryFname = join(filename, sep.join(parts)) + ".m"
			if len(parts) > maxDepth:
				maxDepth = len(parts)
				log.info(f"depth={maxDepth}, {entryFname}")
			entryDir = dirname(entryFname)
			if not isdir(entryDir):
				os.makedirs(entryDir)
			try:
				with open(entryFname, "a", encoding=encoding) as entryFp:
					entryFp.write(defi)
			except:
				log.exception("")
