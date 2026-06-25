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
		self._source_lang = ""
		self._target_lang = ""

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
			log.warning("TMX Reader: file is not seekable")
			self._file.close()
			self._file = compressionOpen(self._filename, mode="rb")

		try:
			context = ET.iterparse(self._file, events=("end",))
			for _, elem_ in context:
				elem = cast("Element", elem_)
				if elem.tag == "header":
					self._source_lang = elem.get("srclang", "")
					if self._source_lang:
						self._glos.sourceLangName = self._source_lang.split("-")[0]
					continue
				if elem.tag == "tu":
					break
		except ET.XMLSyntaxError as e:
			raise ValueError(f"Invalid TMX file: {e}") from e
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
				tag="tu",
			)
			for _, tu_ in context:
				tu = cast("Element", tu_)
				tuvs = tu.findall("tuv")

				if not tuvs:
					continue

				tuv_pairs: dict[str, str] = {}
				for tuv in tuvs:
					lang = tuv.get(_XMLLANG, "")
					seg = tuv.find("seg")
					if seg is not None and seg.text:
						tuv_pairs[lang] = seg.text

				if len(tuv_pairs) < 2:
					continue

				langs = list(tuv_pairs.keys())
				source_lang = langs[0]
				target_lang = langs[1]

				source_text = tuv_pairs[source_lang]
				target_text = tuv_pairs[target_lang]

				terms = [source_text]
				defi = target_text

				if self._source_lang and source_lang:
					self._glos.sourceLangName = source_lang.split("-")[0]
				if target_lang:
					self._glos.targetLangName = target_lang.split("-")[0]

				props_html = self._extract_props(tu)
				if props_html:
					defi = f"{defi}{props_html}"

				yield self._glos.newEntry(
					terms,
					defi,
					defiFormat="h",
					byteProgress=(self._file.tell(), self._fileSize),
				)

				parent = tu.getparent()
				if parent is None:
					continue
				while tu.getprevious() is not None:
					del parent[0]

		except ET.XMLSyntaxError as e:
			raise ValueError(f"Invalid TMX file: {e}") from e

	@classmethod
	def _extract_props(cls, tu: Element) -> str:
		props = tu.findall("prop")
		if not props:
			return ""

		html_parts = []
		for prop in props:
			prop_type = prop.get("type", "")
			if prop.text and prop_type:
				html_parts.append(f"<b>{prop_type}:</b> {prop.text}")

		if not html_parts:
			return ""

		return "<br/>" + "<br/>".join(html_parts)

	def close(self) -> None:
		self._file.close()
		self._file = nullBinaryIO
