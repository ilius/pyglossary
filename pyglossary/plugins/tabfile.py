# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import (
	unescapeNTB,
	splitByBarUnescapeNTB,
)

enable = True
format = "Tabfile"
description = "Tabfile (txt, dic)"
extensions = (".txt", ".tab", ".tsv")
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
	"writeInfo": BoolOption(),
	"resources": BoolOption(),
}
depends = {}

# https://en.wikipedia.org/wiki/Tab-separated_values


class Reader(TextGlossaryReader):
	def isInfoWord(self, word: str) -> bool:
		return word.startswith("#")

	def fixInfoWord(self, word: str) -> str:
		return word.lstrip("#")

	def nextPair(self) -> Tuple[str, str]:
		if not self._file:
			raise StopIteration
		line = self._file.readline()
		if not line:
			raise StopIteration
		line = line.rstrip("\n")
		if not line:
			return
		###
		word, tab, defi = line.partition("\t")
		if not tab:
			log.error(
				f"Warning: line starting with {line[:10]!r} has no tab!"
			)
			return
		###
		if self._glos.getPref("enable_alts", True):
			word = splitByBarUnescapeNTB(word)
			if len(word) == 1:
				word = word[0]
		else:
			word = unescapeNTB(word, bar=False)
		###
		defi = unescapeNTB(defi)
		###
		return word, defi


class Writer(object):
	_encoding: str = "utf-8"
	_writeInfo: bool = True
	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def write(
		self,
		filename: str,
		fileObj: Optional["file"] = None,
	) -> Generator[None, "BaseEntry", None]:
		yield from self._glos.writeTabfile(
			filename,
			fileObj=fileObj,
			encoding=self._encoding,
			writeInfo=self._writeInfo,
			resources=self._resources,
		)
