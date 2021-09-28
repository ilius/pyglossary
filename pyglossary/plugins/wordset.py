# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.entry import Entry
from os import listdir
from os.path import isfile
from json import load

enable = True
lname = "wordset"
format = "Wordset"
description = "Wordset.org JSON directory"
extensions = ()
extensionCreate = "-wordset/"
singleFile = False
kind = "directory"
wiki = ""
website = (
	"https://github.com/wordset/wordset-dictionary",
	"@wordset/wordset-dictionary",
)
optionsProp = {
	"encoding": EncodingOption(),
}


class Reader(object):
	_encoding: str = "utf-8"

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._clear()
		self.defiTemplate = (
			"<p>"
			'<font color="green">{speech_part}</font>'
			"<br>"
			"{def}"
			"<br>"
			"<i>{example}</i>"
			"</p>"
		)
		"""
		{
			"id": "492099d426",
			"def": "without musical accompaniment",
			"example": "they performed a cappella",
			"speech_part": "adverb"
		},
		"""

	def close(self) -> None:
		self._clear()

	def _clear(self) -> None:
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename
		name = self._glos.getInfo("name")
		if not name or name == "data":
			self._glos.setInfo("name", "Wordset.org")
		self._glos.setDefaultDefiFormat("h")

	def __len__(self) -> int:
		return 0

	def fileNameSortKey(self, fname: str) -> str:
		fname = splitext(fname)[0]
		if fname == "misc":
			return "\x80"
		return fname

	def __iter__(self) -> "Iterator[BaseEntry]":
		if not self._filename:
			raise RuntimeError("iterating over a reader while it's not open")

		direc = self._filename
		encoding = self._encoding
		glos = self._glos
		for fname in sorted(listdir(direc), key=self.fileNameSortKey):
			fpath = join(direc, fname)
			if not (fname.endswith(".json") and isfile(fpath)):
				continue
			with open(fpath, encoding=encoding) as fileObj:
				data = load(fileObj)
				words = list(data.keys())
				words.sort(key=Entry.defaultStringSortKey)
				for word in words:
					entryDict = data[word]
					defi = "".join(
						self.defiTemplate.format(**{
							"word": word,
							"def": meaning.get("def", ""),
							"example": meaning.get("example", ""),
							"speech_part": meaning.get("speech_part", ""),
						})
						for meaning in entryDict.get("meanings", [])
					)
					yield glos.newEntry(word, defi, defiFormat="h")
			log.info(f"finished reading {fname}")
