from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType
	from pyglossary.lxml_types import Element

from lxml import etree as ET

from pyglossary.compress import compressionOpen, stdCompressions
from pyglossary.core import log
from pyglossary.io_utils import nullBinaryIO

__all__ = ["Reader"]

_XLIFF_NS = "{urn:oasis:names:tc:xliff:document:1.2}"
_XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"


class Reader:
	useByteProgress = True
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.IOBase = nullBinaryIO
		self._fileSize = 0
		self._encoding = "utf-8"

	def open(self, filename: str) -> None:
		self._filename = filename
		self._glos.setDefaultDefiFormat("h")

		self._file = cast(
			"io.IOBase",
			compressionOpen(self._filename, mode="rb"),
		)

		if self._file.seekable():
			self._file.seek(0, 2)
			self._fileSize = self._file.tell()
			self._file.seek(0)
		else:
			log.warning("XLIFF Reader: file is not seekable")
			self._file.close()
			self._file = compressionOpen(self._filename, mode="rb")

		try:
			context = ET.iterparse(self._file, events=("end",))
			for _, elem_ in context:
				elem = cast("Element", elem_)
				if elem.tag == f"{_XLIFF_NS}file":
					source_lang = elem.get("source-language", "")
					target_lang = elem.get("target-language", "")
					if source_lang:
						self._glos.sourceLangName = source_lang.split("-")[0]
					if target_lang:
						self._glos.targetLangName = target_lang.split("-")[0]
					break
		except ET.XMLSyntaxError as e:
			raise ValueError(f"Invalid XLIFF file: {e}") from e
		finally:
			if self._file.seekable():
				self._file.seek(0)
			else:
				self._file.close()
				self._file = compressionOpen(self._filename, mode="rb")

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType]:
		try:
			context = ET.iterparse(
				self._file,
				events=("end",),
			)

			for _, elem in context:
				if ET.QName(elem).localname == "trans-unit":
					source_elem = elem.xpath(".//*[local-name()='source']")
					target_elem = elem.xpath(".//*[local-name()='target']")

					if not (source_elem and target_elem):
						continue

					source_text = source_elem[0].text or ""
					target_text = target_elem[0].text or ""

					if not source_text or not target_text:
						continue

					terms = [source_text]
					defi = target_text

					note_elem = elem.find(f"{_XLIFF_NS}note")
					if note_elem is not None and note_elem.text:
						defi = f"{defi}<br/><b>Note:</b> {note_elem.text}"

					yield self._glos.newEntry(
						terms,
						defi,
						defiFormat="h",
						byteProgress=(self._file.tell(), self._fileSize),
					)

					parent = elem.getparent()
					if parent is None:
						continue
					while elem.getprevious() is not None:
						del parent[0]

						elem.clear()

		except ET.XMLSyntaxError as e:
			raise ValueError(f"Invalid XLIFF file: {e}") from e

	def close(self) -> None:
		self._file.close()
		self._file = nullBinaryIO
