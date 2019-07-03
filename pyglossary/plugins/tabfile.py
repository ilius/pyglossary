# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import escapeNTB, unescapeNTB, splitByBarUnescapeNTB

enable = True
format = "Tabfile"
description = "Tabfile (txt, dic)"
extensions = [".txt", ".tab", ".dic"]
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
		line = line.strip()  # This also removes tailing newline
		if not line:
			return
		###
		word, tab, defi = line.partition("\t")
		if not tab:
			log.error(
				"Warning: line starting with \"%s\" has no tab!" % line[:10]
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


def write(
	glos: GlossaryType,
	filename: str,
	encoding: str = "utf-8",
	writeInfo: bool = True,
	resources: bool = True,
) -> bool:
	return glos.writeTabfile(
		filename,
		encoding=encoding,
		writeInfo=writeInfo,
		resources=resources,
	)
