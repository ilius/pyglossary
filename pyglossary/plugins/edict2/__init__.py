from collections.abc import Iterator
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.io_utils import nullTextIO
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)

from . import conv

if TYPE_CHECKING:
	import io

	from pyglossary.glossary_types import EntryType, GlossaryType


__all__ = [
	"Reader",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"format",
	"kind",
	"lname",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "edict2"
format = "EDICT2"
description = "EDICT2 (CEDICT) (.u8)"
extensions = (".u8",)
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/CEDICT"
website = None

# Websites / info for different uses of format:

# CC-CEDICT: Chinese-English (122k entries)
# "https://cc-cedict.org/editor/editor.php", "CC-CEDICT Editor"

# HanDeDict: Chinese-German (144k entries)
# "https://handedict.zydeo.net/de/download",
# "Herunterladen - HanDeDict @ Zydeo Wörterbuch Chinesisch-Deutsch"

# CFDICT: Chinese-French (56k entries)
# "https://chine.in/mandarin/dictionnaire/CFDICT/",
# "Dictionnaire chinois français _ 汉法词典 — Chine Informations"

# CC-Canto is Pleco Software's addition of Cantonese language readings
# in Jyutping transcription to CC-CEDICT
# "https://cantonese.org/download.html",

optionsProp: "dict[str, Option]" = {
	"encoding": EncodingOption(),
	"traditional_title": BoolOption(
		comment="Use traditional Chinese for entry titles/keys",
	),
	"colorize_tones": BoolOption(
		comment="Set to false to disable tones coloring",
	),
}


class Reader:
	depends = {
		"lxml": "lxml",
	}

	_encoding: str = "utf-8"
	_traditional_title: bool = False
	_colorize_tones: bool = True

	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self.file: "io.TextIOBase" = nullTextIO
		self._fileSize = 0

	def open(self, filename: str) -> None:
		# self._glos.sourceLangName = "Chinese"
		# self._glos.targetLangName = "English"

		cfile = self.file = open(filename, encoding=self._encoding)

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			# self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("EDICT2 Reader: file is not seekable")

	def close(self) -> None:
		self.file.close()
		self.file = nullTextIO

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> "Iterator[EntryType]":
		_file = self.file
		_fileSize = self._fileSize
		while True:
			line = _file.readline()
			if not line:
				break
			line = line.rstrip("\n")
			if not line:
				continue
			if line.startswith("#"):
				continue
			parts = conv.parse_line(line)
			if parts is None:
				log.warning(f"bad line: {line!r}")
				continue
			names, article = conv.make_entry(
				*parts,
				traditional_title=self._traditional_title,
				colorize_tones=self._colorize_tones
			)
			entry = self._glos.newEntry(
				names,
				article,
				defiFormat="h",
				byteProgress=(_file.tell(), _fileSize) if self._fileSize else None,
			)
			yield entry
