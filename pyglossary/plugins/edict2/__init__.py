from __future__ import annotations

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
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType


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
lname = "edict2"
name = "EDICT2"
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

optionsProp: dict[str, Option] = {
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

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self.file: io.TextIOBase = nullTextIO
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

	def __iter__(self) -> Iterator[EntryType]:
		file = self.file
		fileSize = self._fileSize
		glos = self._glos

		render_syllables = (
			conv.render_syllables_color
			if self._colorize_tones
			else conv.render_syllables_no_color
		)
		parse_line = (
			conv.parse_line_trad if self._traditional_title else conv.parse_line_simp
		)

		while True:
			line = file.readline()
			if not line:
				break
			line = line.rstrip("\n")
			if not line:
				continue
			if line.startswith("#"):
				continue
			parts = parse_line(line)
			if parts is None:
				log.warning(f"bad line: {line!r}")
				continue
			names, article_text = conv.render_article(
				render_syllables,
				conv.Article(*parts),
			)
			entry = glos.newEntry(
				names,
				article_text,
				defiFormat="h",
				byteProgress=(file.tell(), fileSize) if fileSize else None,
			)
			yield entry
