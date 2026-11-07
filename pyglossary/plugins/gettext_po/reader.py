"""
Read Gettext ``.po`` translation catalog files.

Parses GNU gettext PO message catalogs into glossary entries keyed by ``msgid``.
Uses ``msgstr`` text as definitions and preserves translator comments and
context markers where present.
"""

from __future__ import annotations

from os.path import isdir, join
from typing import TYPE_CHECKING

from pyglossary.core import exc_note, log, pip
from pyglossary.utils.io_utils import nullTextIO
from pyglossary.utils.os_utils import countFilesRecursive, listFilesRecursiveRelPath
from pyglossary.utils.text_utils import splitByBar

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	"""Read Gettext Po glossary files."""

	useByteProgress = False
	depends = {
		"polib": "polib",
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._alts = glos.alts
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._entryCount: int | None = None
		self._resDir = ""
		self._resCount = 0

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = open(filename, encoding="utf-8")
		self._resDir = filename + "_res"
		resCount = 0
		if not isdir(self._resDir):
			self._resDir = ""
		elif self._glos.progressbar:
			log.info("Counting resource files...")
			resCount = countFilesRecursive(self._resDir)
			log.info(f"Found {resCount} resource files")
		self._resCount = resCount

	def close(self) -> None:
		self._file.close()
		self._file = nullTextIO
		self.clear()

	def __len__(self) -> int:
		from pyglossary.utils.file_utils import fileCountLines

		if self._entryCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._entryCount = fileCountLines(
				self._filename,
				newline=b"\nmsgid",
			)
		return self._entryCount

	def countResourceFiles(self) -> int:
		return self._resCount

	def makeEntry(self, word: str, defi: str) -> EntryType:
		if self._alts:
			return self._glos.newEntry(splitByBar(word), defi)
		return self._glos.newEntry(word, defi)

	@staticmethod
	def _unquote(value: str) -> str:
		if not value.startswith('"'):
			return value
		if len(value) < 2 or value[-1] != '"':
			raise ValueError("invalid po line: line")
		return value[1:-1]

	def _iterPoEntries(self) -> Iterator[EntryType]:
		try:
			from polib import unescape as po_unescape
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install polib` to install")
			raise

		term = ""
		defi = ""
		msgstr = False
		for line_ in self._file:
			line = line_.strip()  # noqa: PLW2901
			if not line or line.startswith("#"):
				continue
			if line.startswith("msgid "):
				if term:
					yield self.makeEntry(term, defi)
					term = ""
					defi = ""
				# TODO: parse defi and set glos info?
				# but this should be done in self.open
				term = self._unquote(po_unescape(line[6:]))
				msgstr = False
				continue
			if line.startswith("msgstr "):
				if msgstr:
					log.error("msgid omitted!")
				defi = self._unquote(po_unescape(line[7:]))
				msgstr = True
				continue

			line = self._unquote(po_unescape(line))
			if msgstr:
				defi += line
			else:
				term += line
		if term:
			yield self.makeEntry(term, defi)

	def _iterResourceEntries(self) -> Iterator[EntryType]:
		resDir = self._resDir
		for fname in listFilesRecursiveRelPath(resDir):
			with open(join(resDir, fname), "rb") as file:
				yield self._glos.newDataEntry(fname, file.read())

	def __iter__(self) -> Iterator[EntryType]:
		entryCount = 0
		for entry in self._iterPoEntries():
			entryCount += 1
			yield entry
		for entry in self._iterResourceEntries():
			entryCount += 1
			yield entry
		self._entryCount = entryCount
