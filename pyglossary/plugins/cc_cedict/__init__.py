import re
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

enable = True
lname = "cc_cedict"
format = "CC-CEDICT"
description = "CC-CEDICT"
extensions = (".u8",)
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/CEDICT"
website = (
	"https://cc-cedict.org/editor/editor.php",
	"CC-CEDICT Editor",
)
optionsProp: "dict[str, Option]" = {
	"encoding": EncodingOption(),
	"traditional_title": BoolOption(
		comment="Use traditional Chinese for entry titles/keys",
	),
}

entry_count_reg = re.compile(r"#! entries=(\d+)")


class Reader:
	depends = {
		"lxml": "lxml",
	}

	_encoding: str = "utf-8"
	_traditional_title: bool = False

	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self.file: "io.TextIOBase" = nullTextIO
		self.total_entries: "int | None" = None
		self.entries_left = 0

	def open(self, filename: str) -> None:
		self._glos.sourceLangName = "Chinese"
		self._glos.targetLangName = "English"

		self.file = open(filename, encoding=self._encoding)
		for line in self.file:
			match = entry_count_reg.match(line)
			if match is not None:
				count = match.groups()[0]
				self.total_entries = self.entries_left = int(count)
				break
		else:
			self.close()
			raise RuntimeError("CC-CEDICT: could not find entry count")

	def close(self) -> None:
		self.file.close()
		self.file = nullTextIO
		self.total_entries = None
		self.entries_left = 0

	def __len__(self) -> int:
		if self.total_entries is None:
			raise RuntimeError(
				"CC-CEDICT: len(reader) called while reader is not open",
			)
		return self.total_entries

	def __iter__(self) -> "Iterator[EntryType]":
		for line in self.file:
			if line.startswith("#"):
				continue
			if self.entries_left == 0:
				log.warning("more entries than the header claimed?!")
			self.entries_left -= 1
			parts = conv.parse_line(line)
			if parts is None:
				log.warning("bad line: %s", line)
				continue
			names, article = conv.make_entry(
				*parts,
				traditional_title=self._traditional_title,
			)
			entry = self._glos.newEntry(names, article, defiFormat="h")
			yield entry
