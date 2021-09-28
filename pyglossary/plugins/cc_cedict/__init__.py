import re
from formats_common import *
from . import conv

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
optionsProp = {
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

	def __init__(self, glos):
		self._glos = glos
		self.file = None
		self.total_entries = self.entries_left = None

	def open(self, filename):
		if self.file is not None:
			self.file.close()

		self._glos.sourceLangName = "Chinese"
		self._glos.targetLangName = "English"

		self.file = open(filename, "r", encoding=self._encoding)
		for line in self.file:
			match = entry_count_reg.match(line)
			if match is not None:
				count = match.groups()[0]
				self.total_entries = self.entries_left = int(count)
				break
		else:
			self.close()
			raise RuntimeError("CC-CEDICT: could not find entry count")

	def close(self):
		if self.file is not None:
			self.file.close()
		self.file = None
		self.total_entries = self.entries_left = None

	def __len__(self):
		if self.total_entries is None:
			raise RuntimeError(
				"CC-CEDICT: len(reader) called while reader is not open",
			)
		return self.total_entries

	def __iter__(self):
		if self.file is None:
			raise RuntimeError(
				"CC-CEDICT: tried to iterate over entries " +
				"while reader is not open"
			)
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
