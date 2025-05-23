# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import exc_note, log, pip
from pyglossary.html_utils import unescape_unicode
from pyglossary.io_utils import nullBinaryIO

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType
	from pyglossary.lxml_types import Element
	from pyglossary.xdxf.transform import XdxfTransformer


__all__ = ["Reader"]


class Reader:
	useByteProgress = True
	_encoding: str = "utf-8"
	_xdxf_to_html: bool = True

	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.IOBase = nullBinaryIO
		self._fileSize = 0
		self._xdxfTr: XdxfTransformer | None = None

	def xdxf_setup(self) -> XdxfTransformer:
		from pyglossary.xdxf.transform import XdxfTransformer

		self._xdxfTr = tr = XdxfTransformer(encoding="utf-8")
		return tr

	def xdxf_transform(self, text: str) -> str:
		tr = self._xdxfTr
		if tr is None:
			tr = self.xdxf_setup()
		return tr.transformByInnerString(text)

	def __len__(self) -> int:
		return 0

	def close(self) -> None:
		self._file.close()
		self._file = nullBinaryIO
		self._filename = ""
		self._fileSize = 0

	def open(self, filename: str) -> None:
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install lxml` to install")
			raise

		self._filename = filename
		cfile = compressionOpen(filename, mode="rb")

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			# self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("StarDict Textual File Reader: file is not seekable")

		context = ET.iterparse(  # type: ignore # noqa: PGH003
			cfile,
			events=("end",),
			tag="info",
		)
		for _, elem in context:
			self.setMetadata(elem)  # type: ignore
			break

		cfile.close()

	def setGlosInfo(self, key: str, value: str) -> None:
		if value is None:
			return
		self._glos.setInfo(key, unescape_unicode(value))

	def setMetadata(self, header: Element) -> None:
		if (elem := header.find("./bookname")) is not None and elem.text:
			self.setGlosInfo("name", elem.text)

		if (elem := header.find("./author")) is not None and elem.text:
			self.setGlosInfo("author", elem.text)

		if (elem := header.find("./email")) is not None and elem.text:
			self.setGlosInfo("email", elem.text)

		if (elem := header.find("./website")) is not None and elem.text:
			self.setGlosInfo("website", elem.text)

		if (elem := header.find("./description")) is not None and elem.text:
			self.setGlosInfo("description", elem.text)

		if (elem := header.find("./bookname")) is not None and elem.text:
			self.setGlosInfo("name", elem.text)

		if (elem := header.find("./bookname")) is not None and elem.text:
			self.setGlosInfo("name", elem.text)

		if (elem := header.find("./date")) is not None and elem.text:
			self.setGlosInfo("creationTime", elem.text)

		# if (elem := header.find("./dicttype")) is not None and elem.text:
		# 	self.setGlosInfo("dicttype", elem.text)

	def renderDefiList(
		self,
		defisWithFormat: list[tuple[str, str]],
	) -> tuple[str, str]:
		if not defisWithFormat:
			return "", ""
		if len(defisWithFormat) == 1:
			return defisWithFormat[0]

		defiFormatSet: set[str] = set()
		defiFormatSet.update(_type for _, _type in defisWithFormat)

		if len(defiFormatSet) == 1:
			format_ = defiFormatSet.pop()
			if format_ == "h":
				return "\n<hr>".join([defi for defi, _ in defisWithFormat]), format_
			return "\n".join([defi for defi, _ in defisWithFormat]), format_

		# convert plaintext or xdxf to html
		defis: list[str] = []
		for defi_, format_ in defisWithFormat:
			if format_ == "m":
				defis.append("<pre>" + defi_.replace("\n", "<br/>") + "</pre>")
			elif format_ == "x":
				defis.append(self.xdxf_transform(defi_))
			else:
				defis.append(defi_)
		return "\n<hr>\n".join(defis), "h"

	def __iter__(self) -> Iterator[EntryType]:
		from lxml import etree as ET

		glos = self._glos
		fileSize = self._fileSize
		self._file = file = compressionOpen(self._filename, mode="rb")
		context = ET.iterparse(  # type: ignore # noqa: PGH003
			self._file,
			events=("end",),
			tag="article",
		)
		for _, _elem in context:
			elem = cast("Element", _elem)
			words: list[str] = []
			defisWithFormat: list[tuple[str, str]] = []
			for child in elem.iterchildren():
				if not child.text:
					continue
				if child.tag in {"key", "synonym"}:
					words.append(child.text)
				elif child.tag == "definition":
					type_ = child.attrib.get("type", "")
					if type_:
						new_type = {
							"m": "m",
							"t": "m",
							"y": "m",
							"g": "h",
							"h": "h",
							"x": "x",
						}.get(type_, "")
						if not new_type:
							log.warning(f"unsupported definition type {type_}")
						type_ = new_type
					if not type_:
						type_ = "m"
					defi_ = child.text.strip()
					if type_ == "x" and self._xdxf_to_html:
						defi_ = self.xdxf_transform(defi_)
						type_ = "h"
					defisWithFormat.append((defi_, type_))
				# TODO: child.tag == "definition-r"
				else:
					log.warning(f"unknown tag {child.tag}")

			defi, defiFormat = self.renderDefiList(defisWithFormat)

			yield glos.newEntry(
				words,
				defi,
				defiFormat=defiFormat,
				byteProgress=(file.tell(), fileSize),
			)

			# clean up preceding siblings to save memory
			# this can reduce memory usage from >300 MB to ~25 MB
			while elem.getprevious() is not None:
				parent = elem.getparent()
				if parent is None:
					break
				del parent[0]
