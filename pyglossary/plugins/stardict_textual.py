# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, Generator, Iterator, List, Tuple

if TYPE_CHECKING:
	from lxml import builder

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log, pip
from pyglossary.glossary_type import EntryType, GlossaryType
from pyglossary.html_utils import unescape_unicode
from pyglossary.option import (
	BoolOption,
	EncodingOption,
)

enable = True
lname = "stardict_textual"
format = "StardictTextual"
description = "StarDict Textual File (.xml)"
extensions = ()
extensionCreate = ".xml"
sortKeyName = "stardict"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/huzheng001/stardict-3"
	"/blob/master/dict/doc/TextualDictionaryFileFormat",
	"TextualDictionaryFileFormat",
)
optionsProp = {
	"encoding": EncodingOption(),
	"xdxf_to_html": BoolOption(
		comment="Convert XDXF entries to HTML",
	),
}


class Reader(object):
	_encoding: str = "utf-8"
	_xdxf_to_html: bool = True

	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self._filename = ""
		self._file = None
		self._fileSize = 0
		self._xdxfTr = None

	def xdxf_setup(self) -> None:
		from pyglossary.xdxf_transform import XdxfTransformer
		self._xdxfTr = XdxfTransformer(encoding="utf-8")

	def xdxf_transform(self, text: str) -> str:
		if self._xdxfTr is None:
			self.xdxf_setup()
		return self._xdxfTr.transformByInnerString(text)

	def __len__(self) -> int:
		return 0

	def close(self) -> None:
		if self._file:
			self._file.close()
			self._file = None
		self._filename = ""
		self._fileSize = 0

	def open(self, filename: str) -> None:
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e

		self._filename = filename
		cfile = compressionOpen(filename, mode="rb")

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			# self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("StarDict Textual File Reader: file is not seekable")

		context = ET.iterparse(
			cfile,
			events=("end",),
			tag="info",
		)
		for _, elem in context:
			self.setMetadata(elem)
			break

		cfile.close()

	def setGlosInfo(self, key: str, value: str) -> None:
		if value is None:
			return
		self._glos.setInfo(key, unescape_unicode(value))

	def setMetadata(self, header: str) -> None:
		self.setGlosInfo("name", header.find("./bookname").text)
		self.setGlosInfo("author", header.find("./author").text)
		self.setGlosInfo("email", header.find("./email").text)
		self.setGlosInfo("website", header.find("./website").text)
		self.setGlosInfo("description", header.find("./description").text)
		self.setGlosInfo("creationTime", header.find("./date").text)
		# self.setGlosInfo("dicttype", header.find("./dicttype").text)

	def renderDefiList(
		self,
		defisWithFormat: "List[Tuple[str, str]]",
	) -> "Tuple[str, str]":
		if len(defisWithFormat) == 1:
			return defisWithFormat[0]
		if len(defisWithFormat) == 0:
			return "", ""

		defiFormatSet = set()
		for _, _type in defisWithFormat:
			defiFormatSet.add(_type)

		if len(defiFormatSet) == 1:
			defis = [_defi for _defi, _ in defisWithFormat]
			_format = defiFormatSet.pop()
			if _format == "h":
				return "\n<hr>".join(defis), _format
			return "\n".join(defis), _format

		# convert plaintext or xdxf to html
		defis = []
		for _defi, _format in defisWithFormat:
			if _format == "m":
				_defi = _defi.replace("\n", "<br/>")
				_defi = f"<pre>{_defi}</pre>"
			elif _format == "x":
				_defi = self.xdxf_transform(_defi)
			defis.append(_defi)
		return "\n<hr>\n".join(defis), "h"

	def __iter__(self) -> "Iterator[EntryType]":
		from lxml import etree as ET

		glos = self._glos
		fileSize = self._fileSize
		self._file = _file = compressionOpen(self._filename, mode="rb")
		context = ET.iterparse(
			self._file,
			events=("end",),
			tag="article",
		)
		for _, elem in context:
			words = []
			defisWithFormat = []
			for child in elem.getchildren():
				if not child.text:
					continue
				if child.tag in ("key", "synonym"):
					words.append(child.text)
				elif child.tag == "definition":
					_type = child.attrib.get("type", "")
					if _type:
						new_type = {
							"m": "m",
							"t": "m",
							"y": "m",
							"g": "h",
							"h": "h",
							"x": "x",
						}.get(_type, "")
						if not new_type:
							log.warning(f"unsupported definition type {_type}")
						_type = new_type
					if not _type:
						_type = "m"
					_defi = child.text.strip()
					if _type == "x" and self._xdxf_to_html:
						_defi = self.xdxf_transform(_defi)
						_type = "h"
					defisWithFormat.append((_defi, _type))
				# TODO: child.tag == "definition-r"
				else:
					log.warning(f"unknown tag {child.tag}")

			defi, defiFormat = self.renderDefiList(defisWithFormat)

			yield glos.newEntry(
				words,
				defi,
				defiFormat=defiFormat,
				byteProgress=(_file.tell(), fileSize),
			)

			# clean up preceding siblings to save memory
			# this can reduce memory usage from >300 MB to ~25 MB
			while elem.getprevious() is not None:
				del elem.getparent()[0]


class Writer(object):
	_encoding: str = "utf-8"

	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def open(
		self,
		filename: str,
	) -> None:
		self._filename = filename
		self._file = compressionOpen(
			self._filename,
			mode="w",
			encoding=self._encoding,
		)

	def finish(self) -> None:
		self._file.close()

	def writeInfo(self, maker: "builder.ElementMaker", pretty: bool) -> None:
		from lxml import etree as ET

		glos = self._glos

		desc = glos.getInfo("description")
		copyright = glos.getInfo("copyright")
		if copyright:
			desc = f"{copyright}\n{desc}"
		publisher = glos.getInfo("publisher")
		if publisher:
			desc = f"Publisher: {publisher}\n{desc}"

		info = maker.info(
			maker.version("3.0.0"),
			maker.bookname(glos.getInfo("name")),
			maker.author(glos.getInfo("author")),
			maker.email(glos.getInfo("email")),
			maker.website(glos.getInfo("website")),
			maker.description(desc),
			maker.date(glos.getInfo("creationTime")),
			maker.dicttype(""),
		)
		self._file.write(ET.tostring(
			info,
			encoding=self._encoding,
			pretty_print=pretty,
		).decode(self._encoding) + "\n")

	def writeDataEntry(self, maker: "builder.ElementMaker", entry: "EntryType") -> None:
		pass
		# TODO: create article tag with "definition-r" in it?
		# or just save the file to res/ directory? or both?
		# article = maker.article(
		# 	maker.key(entry.s_word),
		# 	maker.definition_r(
		# 		ET.CDATA(entry.defi),
		# 		**{"type": ext})
		# 	)
		# )

	def write(self) -> "Generator[None, EntryType, None]":
		from lxml import builder
		from lxml import etree as ET

		_file = self._file
		encoding = self._encoding
		maker = builder.ElementMaker()

		_file.write("""<?xml version="1.0" encoding="UTF-8" ?>
<stardict xmlns:xi="http://www.w3.org/2003/XInclude">
""")

		self.writeInfo(maker, pretty=True)

		pretty = True
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				self.writeDataEntry(maker, entry)
				continue
			entry.detectDefiFormat()
			article = maker.article(
				maker.key(entry.l_word[0]),
			)
			for alt in entry.l_word[1:]:
				article.append(maker.synonym(alt))
			article.append(maker.definition(
				ET.CDATA(entry.defi),
				type=entry.defiFormat,
			))
			ET.indent(article, space="")
			articleStr = ET.tostring(
				article,
				pretty_print=pretty,
				encoding=encoding,
			).decode(encoding)
			# for some reason, "´k" becomes " ́k" (for example)
			# stardict-text2bin tool also does this.
			# https://en.wiktionary.org/wiki/%CB%88#Translingual
			self._file.write(articleStr + "\n")

		_file.write("</stardict>")
