"""
Write XDXF ``.xdxf`` dictionary files.

Serializes glossary entries whose definition format is XDXF (``x``) to the XML
Dictionary Exchange Format. Entries in other definition formats are skipped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from pyglossary.core import log
from pyglossary.utils.io_utils import nullTextIO

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.stubs.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	"""Write glossary files in XDXF format."""

	_encoding: str = "utf-8"

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = file = open(  # noqa: SIM115
			filename,
			mode="w",
			encoding=self._encoding,
		)
		file.write(
			f'<?xml version="1.0" encoding="{self._encoding.upper()}"?>\n'
			'<xdxf revision="34">\n'
			"\t<meta_info>\n",
		)
		self._writeMetaInfo(file)
		file.write("\t</meta_info>\n\t<lexicon>\n")

	def _writeMetaInfo(self, file: io.TextIOBase) -> None:
		glos = self._glos
		name = glos.getInfo("name")
		if name:
			file.write(f"\t\t<full_title>{escape(name)}</full_title>\n")

		for key, tag in (
			("publisher", "publisher"),
			("description", "description"),
		):
			value = glos.getInfo(key)
			if value:
				file.write(f"\t\t<{tag}>{escape(value)}</{tag}>\n")

		author = glos.getInfo("author")
		if author:
			file.write(
				f"\t\t<authors>\n\t\t\t<author>{escape(author)}</author>\n"
				"\t\t</authors>\n",
			)

		sourceLang = glos.sourceLang
		targetLang = glos.targetLang
		if sourceLang or targetLang:
			file.write("\t\t<languages>\n")
			if sourceLang:
				file.write(f'\t\t\t<from xml:lang="{escape(sourceLang.code)}"/>\n')
			if targetLang:
				file.write(f'\t\t\t<to xml:lang="{escape(targetLang.code)}"/>\n')
			file.write("\t\t</languages>\n")

	def finish(self) -> None:
		self._file.write("\t</lexicon>\n</xdxf>\n")
		self._file.close()
		self._file = nullTextIO
		self._filename = ""

	def write(self) -> Generator[None, EntryType, None]:
		file = self._file
		skippedEntries = 0
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				continue
			if entry.defiFormat != "x":
				skippedEntries += 1
				continue

			defi = entry.defi.strip()
			file.write("\t\t<ar>\n")

			if defi.startswith("<k"):
				# Definition already contains XDXF article markup.
				file.write(f"\t\t\t{defi}\n")
			else:
				for term in entry.l_term:
					file.write(f"\t\t\t<k>{escape(term)}</k>\n")
				file.write(f"\t\t\t<def>{defi}</def>\n")

			file.write("\t\t</ar>\n")
		if skippedEntries > 0:
			log.warning(f"Skipped {skippedEntries} entries that are not XDXF")
