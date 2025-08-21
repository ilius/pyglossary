from __future__ import annotations

from pyglossary.core import log
from pyglossary.text_reader import TextGlossaryReader


def unescapeDefi(defi: str) -> str:
	return defi


__all__ = ["Reader"]


class Reader(TextGlossaryReader):
	useByteProgress = True
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
		term = ""
		defiLines: list[str] = []

		while True:
			line = self.readline()
			if not line:
				break
			line = line.rstrip("\n\r")
			if not line:
				continue

			if not line.strip("_"):
				if not term:
					continue
				if not defiLines:
					log.warning(f"no definition/value for {term!r}")
				defi = unescapeDefi("\n".join(defiLines))
				terms = term.split(self._headword_separator)
				return terms, defi, None

			if not term:
				term = line
				continue

			if line == term:
				continue
			if line.lower() == term:
				term = line
				continue

			defiLines.append(line)

		if term:
			defi = unescapeDefi("\n".join(defiLines))
			if term.startswith("00-database-") and defi == "unknown":
				log.info(f"ignoring {term} -> {defi}")
				return None
			terms = term.split(self._headword_separator)
			return terms, defi, None

		raise StopIteration
