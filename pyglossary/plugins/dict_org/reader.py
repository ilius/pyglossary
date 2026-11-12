"""
Read DICT.org ``.index`` dictionary file sets.

Opens DICT.org index files alongside companion data files and resolves offsets
to definition text. Yields headwords with definitions formatted for DICT protocol
dictionary bundles.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.plugin_lib.dictdlib import DictDB

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	"""Read DICT.org glossary files."""

	useByteProgress = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dictdb: DictDB | None = None
		self._entryCount = 0

		# regular expression patterns used to prettify definition text
		self._re_newline_in_braces = re.compile(
			r"\{(?P<left>.*?)\n(?P<right>.*?)?\}",
		)
		self._re_words_in_braces = re.compile(
			r"\{(?P<word>.+?)\}",
		)

	def open(self, filename: str) -> None:
		filename = filename.removesuffix(".index")
		self._filename = filename
		self._dictdb = DictDB(filename, "read", 1)
		self._readMetadata()

	def _readMetadata(self) -> None:
		dictdb = self._dictdb
		if dictdb is None:
			raise RuntimeError("reading metadata while the reader is not open")
		self._entryCount = 0
		infoKeys = {
			"00databaseurl": "website",
			"00databaseshort": "name",
			"00databaseinfo": "description",
		}
		for term in dictdb.getDefList():
			name = term.replace("-", "")
			if not name.startswith("00database"):
				self._entryCount += 1
				continue
			key = infoKeys.get(name)
			if key is None:
				continue
			value = b"\n\n".join(dictdb.getDef(term)).decode("utf-8", "ignore").strip()
			# dictfmt and dictdlib may repeat the special headword in the
			# definition before the actual metadata value.
			firstLine, _, rest = value.partition("\n")
			if firstLine.strip().replace("-", "") == name:
				value = rest.strip()
			if value and value != "unknown":
				self._glos.setInfo(key, value)

	def close(self) -> None:
		if self._dictdb is not None:
			self._dictdb.close()
			# self._dictdb.finish()
			self._dictdb = None
		self._entryCount = 0

	def prettifyDefinitionText(self, defi: str) -> str:
		# Handle words in {}
		# First, we remove any \n in {} pairs
		defi = self._re_newline_in_braces.sub(r"{\g<left>\g<right>}", defi)

		# Then, replace any {words} into <a href="bword://words">words</a>,
		# so it can be rendered as link correctly
		defi = self._re_words_in_braces.sub(
			r'<a href="bword://\g<word>">\g<word></a>',
			defi,
		)

		# Use <br /> so it can be rendered as newline correctly
		return defi.replace("\n", "<br />")

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		return self._entryCount

	def __iter__(self) -> Iterator[EntryType]:
		if self._dictdb is None:
			raise RuntimeError("iterating over a reader while it's not open")
		dictdb = self._dictdb
		for term in dictdb.getDefList():
			if term.replace("-", "").startswith("00database"):
				continue
			b_defi = b"\n\n<hr>\n\n".join(dictdb.getDef(term))
			try:
				defi = b_defi.decode("utf_8", "ignore")
				defi = self.prettifyDefinitionText(defi)
			except Exception:
				log.error(f"{b_defi = }")
				raise
			yield self._glos.newEntry(term, defi)
