# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.core import log
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import (
	splitByBarUnescapeNTB,
	unescapeNTB,
)

__all__ = ["Reader"]


class Reader(TextGlossaryReader):
	useByteProgress = True

	@classmethod
	def isInfoWord(cls, word: str) -> bool:
		return word.startswith("#")

	@classmethod
	def fixInfoWord(cls, word: str) -> str:
		return word.lstrip("#")

	def nextBlock(self) -> tuple[str | list[str], str, None] | None:
		if not self._file:
			raise StopIteration
		line = self.readline()
		if not line:
			raise StopIteration
		line = line.rstrip("\n")
		if not line:
			return None
		###
		word: str | list[str]
		word, tab, defi = line.partition("\t")
		if not tab:
			log.warning(
				f"Warning: line starting with {line[:10]!r} has no tab!",
			)
			return None
		###
		if self._glos.alts:
			word = splitByBarUnescapeNTB(word)
			if len(word) == 1:
				word = word[0]
		else:
			word = unescapeNTB(word, bar=False)
		###
		defi = unescapeNTB(defi)
		###
		return word, defi, None
