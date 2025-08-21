# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.compression import stdCompressions
from pyglossary.core import log
from pyglossary.file_utils import fileCountLines
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import splitByBar

if TYPE_CHECKING:
	from pyglossary.text_reader import nextBlockResultType

__all__ = ["Reader"]


class Reader(TextGlossaryReader):
	useByteProgress = True
	compressions = stdCompressions

	def __len__(self) -> int:
		if self._entryCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._entryCount = (
				fileCountLines(
					self._filename,
					newline=b"\n\n",
				)
				- self._leadingLinesCount
			)
		return self._entryCount

	@classmethod
	def isInfoWord(cls, word: str) -> bool:
		if isinstance(word, str):
			return word.startswith("#")

		return False

	@classmethod
	def fixInfoWord(cls, word: str) -> str:
		if isinstance(word, str):
			return word.lstrip("#").lower()

		return word

	def nextBlock(self) -> nextBlockResultType:
		if not self._file:
			raise StopIteration
		entryLines: list[str] = []
		while True:
			line = self.readline()
			if not line:
				raise StopIteration
			line = line.rstrip("\n\r")
			if line.startswith("###"):
				parts = line.split(":")
				key = parts[0].strip()
				value = ":".join(parts[1:]).strip()
				return key, value, None

			if line:
				entryLines.append(line)
				continue

			# now `line` is empty, process `entryLines`
			if not entryLines:
				return None
			if len(entryLines) < 2:
				log.error(
					f"invalid block near pos {self._file.tell()}"
					f" in file {self._filename}",
				)
				return None
			term = entryLines[0]
			defi = "\n".join(entryLines[1:])
			defi = (
				defi.replace("<br/>", "\n")
				.replace("<BR/>", "\n")
				.replace("<br>", "\n")
				.replace("<BR>", "\n")
			)

			terms = splitByBar(term)

			return terms, defi, None
