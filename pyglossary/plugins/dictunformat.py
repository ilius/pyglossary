from formats_common import *
from pyglossary.text_reader import TextGlossaryReader

enable = True
format = "Dictunformat"
description = "dictunformat output file"
extensions = (".dictunformat",)
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
}

tools = [
	{
		"name": "dictunformat",
		"web": "https://linux.die.net/man/1/dictunformat",
		"platforms": ["Linux"],
		"license": "GPL",
	},
]


def unescapeDefi(defi: str) -> str:
	return defi


class Reader(TextGlossaryReader):
	def isInfoWord(self, word):
		return word.startswith("00-database-")

	def fixInfoWord(self, word):
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
					glos.setInfo(key, f"{glos.getInfo(lastKey)}\n{line}")
				continue

			parts = line[3:].split(":")
			if len(parts) < 2:
				log.error(f"unexpected line: {line}")
			key = lastKey = parts[0]
			value = ":".join(parts[1:])
			glos.setInfo(key, value)

	def nextPair(self):
		if not self._file:
			raise StopIteration
		word = ""
		defiLines = []

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
					log.warn(f"no definition/value for {word!r}")
				defi = unescapeDefi("\n".join(defiLines))
				return word, defi

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
				return
			return word, defi

		raise StopIteration
