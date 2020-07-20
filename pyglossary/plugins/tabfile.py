# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import escapeNTB, unescapeNTB, splitByBarUnescapeNTB

enable = True
format = "Tabfile"
description = "Tabfile (txt, dic)"
extensions = (".txt", ".tab", ".dic")
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
	"writeInfo": BoolOption(),
	"resources": BoolOption(),
}
depends = {}


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
			word = unescapeNTB(word, bar=True)
		###
		defi = unescapeNTB(defi)
		###
		return word, defi


class Writer(object):
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def write(
		self,
		filename: str,
		fileObj: Optional["file"] = None,
		encoding: str = "utf-8",
		writeInfo: bool = True,
		resources: bool = True,
	) -> Generator[None, "BaseEntry", None]:
		yield from self._glos.writeTabfile(
			filename,
			fileObj=fileObj,
			encoding=encoding,
			writeInfo=writeInfo,
			resources=resources,
		)
