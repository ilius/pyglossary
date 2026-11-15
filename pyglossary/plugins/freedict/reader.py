"""
Read FreeDict TEI XML dictionaries as HTML or Markdown definitions.

Parses TEI ``<entry>`` elements (including XInclude), resolves FreeDict
translation and orthography modules, and detects source/target languages from
``xml:lang``. The ``defiFormat`` read option selects the definition format:
``h`` for HTML (default) or ``m`` for Markdown.

The TEI parsing lives in :mod:`pyglossary.plugins.freedict.parser`, the neutral
document layout in :mod:`pyglossary.plugins.freedict.layout`, and the formatting
in :mod:`pyglossary.plugins.freedict.html_formatter` and
:mod:`pyglossary.plugins.freedict.md_formatter`.
"""

from __future__ import annotations

from os.path import dirname, isfile, join, realpath
from typing import TYPE_CHECKING, cast

from pyglossary.compress import compressionOpen, stdCompressions
from pyglossary.core import exc_note, log, pip
from pyglossary.utils.html_utils import unescape_unicode
from pyglossary.utils.io_utils import nullBinaryIO
from pyglossary.utils.lxml_utils import drop_previous_siblings

from .html_formatter import HtmlFormatter
from .layout import buildDocument
from .md_formatter import MdFormatter
from .parser import ENTRY, INCLUDE, TEI, Metadata, Parser

if TYPE_CHECKING:
	from collections.abc import Iterator
	from io import IOBase

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType
	from pyglossary.stubs.lxml_types import Element

	from .formatter import Formatter


__all__ = ["Reader"]


class Reader:
	"""Read Freedict glossary files."""

	useByteProgress = True
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_defiFormat: str = "h"
	_auto_rtl: bool = True
	_auto_comma: bool = True
	_comma: str = ", "
	_word_title: bool = False
	_pron_color: str = "gray"
	_gram_color: str = "green"
	_usage_color: str = "green"
	_label_color: str = "darkblue"
	_example_padding: int = 10

	def _newFormatter(self) -> HtmlFormatter | MdFormatter:
		if self._defiFormat == "m":
			return MdFormatter(self)
		return HtmlFormatter(self)

	def _copyOptionsTo(self, other: Reader) -> None:
		other._defiFormat = self._defiFormat
		other._auto_rtl = self._auto_rtl
		other._auto_comma = self._auto_comma
		other._comma = self._comma
		other._word_title = self._word_title
		other._pron_color = self._pron_color
		other._gram_color = self._gram_color
		other._usage_color = self._usage_color
		other._label_color = self._label_color
		other._example_padding = self._example_padding

	def getEntryByElem(
		self,
		entry: Element,
	) -> EntryType:
		parsedEntry = self._p.parseEntry(entry)
		document = buildDocument(parsedEntry, self)
		defi = self._formatter.formatDocument(document)
		file = self._file
		return self._glos.newEntry(
			parsedEntry.keywords,
			defi,
			defiFormat=self._formatter.defiFormat,
			byteProgress=(file.tell(), self._fileSize) if self._progress else None,
		)

	def setGlosInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, unescape_unicode(value))

	def applyMetadata(self, metadata: Metadata) -> None:
		if metadata.entryCount is not None:
			self._entryCount = metadata.entryCount
		for key in (
			"name",
			"edition",
			"copyright",
			"publisher",
			"creationTime",
			"website",
			"description",
		):
			value = getattr(metadata, key)
			if value is not None:
				self.setGlosInfo(key, value)

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dirname = ""
		self._file: IOBase = nullBinaryIO
		self._fileSize = 0
		self._progress: bool | int = True
		self._entryCount = 0
		# real paths of the files from the top-level file down to this one
		self._includeChain: frozenset[str] = frozenset()
		self._p = Parser(self)
		self._formatter: Formatter = self._newFormatter()

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		return self._entryCount

	def close(self) -> None:
		self._file.close()
		self._file = nullBinaryIO
		self._filename = ""
		self._fileSize = 0

	def open(
		self,
		filename: str,
	) -> None:
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install lxml` to install")
			raise

		self._filename = filename
		self._dirname = dirname(filename)
		# the defiFormat option is set after construction, so pick the formatter here
		self._formatter = self._newFormatter()
		# an empty chain means this is the top-level file, not an XInclude
		isTopLevel = not self._includeChain
		self._includeChain = self._includeChain | {realpath(filename)}
		cfile = compressionOpen(filename, mode="rb")
		try:
			if cfile.seekable():
				cfile.seek(0, 2)
				self._fileSize = cfile.tell()
				cfile.seek(0)
				if isTopLevel:
					# only the top-level file defines the glossary's input size,
					# included files must not overwrite it
					self._glos.setInfo("input_file_size", str(self._fileSize))
			else:
				log.warning("FreeDict Reader: file is not seekable")

			self._progress = self._glos.progressbar and self._fileSize

			self._glos.setDefaultDefiFormat(self._formatter.defiFormat)

			if self._word_title:
				self._glos.setInfo("definition_has_headwords", "True")

			context = ET.iterparse(  # type: ignore # noqa: PGH003
				cfile,
				events=("end",),
				tag=f"{TEI}teiHeader",
			)
			for _, elem in context:
				self.applyMetadata(self._p.parseMetadata(elem))  # type: ignore
				break
		finally:
			cfile.close()

	def loadInclude(self, elem: Element) -> Reader | None:
		href = self._p.parseIncludeHref(elem)
		if href is None:
			return None
		filename = join(self._dirname, href)
		if not isfile(filename):
			log.error(f"no such file {filename!r} from {elem}")
			return None
		if realpath(filename) in self._includeChain:
			log.error(f"include cycle: {filename!r} from {elem}, skipping")
			return None
		reader = self.__class__(self._glos)
		self._copyOptionsTo(reader)
		reader._includeChain = self._includeChain
		try:
			reader.open(filename)
		except Exception:
			reader.close()
			raise
		return reader

	def __iter__(self) -> Iterator[EntryType]:
		from lxml import etree as ET

		self._file = compressionOpen(self._filename, mode="rb")
		context = ET.iterparse(  # type: ignore # noqa: PGH003
			self._file,
			events=("end",),
			tag=(ENTRY, INCLUDE),
		)
		for _, elem_ in context:
			elem = cast("Element", elem_)

			if self._p.isIncludeElement(elem):
				reader = self.loadInclude(elem)
				if reader is not None:
					yield from reader
					reader.close()
				continue

			yield self.getEntryByElem(elem)
			# clean up preceding siblings to save memory
			# this can reduce memory usage from 1 GB to ~25 MB
			drop_previous_siblings(elem)
