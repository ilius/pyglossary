from __future__ import annotations

from pyglossary.core import log
from pyglossary.option import EncodingOption, Option, StrOption
from pyglossary.text_reader import TextGlossaryReader

__all__ = [
	"Reader",
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
lname = "dictunformat"
name = "Dictunformat"
description = "dictunformat output file"
extensions = (".dictunformat",)
extensionCreate = ".dictunformat"
singleFile = True
kind = "text"
wiki = "https://directory.fsf.org/wiki/Dictd"
website = (
	"https://github.com/cheusov/dictd/blob/master/dictunformat.1.in",
	"dictd/dictunformat.1.in - @cheusov/dictd",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"headword_separator": StrOption(
		comment="separator for headword and alternates",
	),
}


def unescapeDefi(defi: str) -> str:
	return defi


class Reader(TextGlossaryReader):
	_headword_separator = ";   "
	# https://github.com/cheusov/dictd/blob/master/dictfmt/dictunformat.in#L14

	@classmethod
	def isInfoWord(cls, word: str) -> bool:
		return word.startswith("00-database-")

	@classmethod
	def fixInfoWord(cls, word: str) -> str:
		return word

	def setInfo(self, word: str, defi: str) -> None:
		if word == "00-database-short":
			self._glos.setInfo("name", defi)
			return

		if word != "00-database-info":
			return

		glos = self._glos

		lastKey = ""
		for line in defi.split("\n"):
			if not line.startswith("##:"):
				if lastKey:
					glos.setInfo(word, f"{glos.getInfo(lastKey)}\n{line}")
				continue

			parts = line[3:].split(":")
			if len(parts) < 2:
				log.error(f"unexpected line: {line}")
			key = lastKey = parts[0]
			value = ":".join(parts[1:])
			glos.setInfo(key, value)

	def nextBlock(self) -> tuple[str | list[str], str, None] | None:
		if not self._file:
			raise StopIteration
		word = ""
		defiLines: list[str] = []

		while True:
			line = self.readline()
			if not line:
				break
			line = line.rstrip("\n\r")
			if not line:
				continue

			if not line.strip("_"):
				if not word:
					continue
				if not defiLines:
					log.warning(f"no definition/value for {word!r}")
				defi = unescapeDefi("\n".join(defiLines))
				words = word.split(self._headword_separator)
				return words, defi, None

			if not word:
				word = line
				continue

			if line == word:
				continue
			if line.lower() == word:
				word = line
				continue

			defiLines.append(line)

		if word:
			defi = unescapeDefi("\n".join(defiLines))
			if word.startswith("00-database-") and defi == "unknown":
				log.info(f"ignoring {word} -> {defi}")
				return None
			words = word.split(self._headword_separator)
			return words, defi, None

		raise StopIteration
