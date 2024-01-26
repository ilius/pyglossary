# -*- coding: utf-8 -*-

import re
from io import BytesIO, IOBase
from os.path import dirname, isfile, join
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from collections.abc import Iterator
	from typing import Any, Callable

	from pyglossary.lxml_types import Element, T_htmlfile


from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log, pip
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.html_utils import unescape_unicode
from pyglossary.io_utils import nullBinaryIO
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText
from pyglossary.option import (
	BoolOption,
	IntOption,
	Option,
	StrOption,
)

enable = True
lname = "freedict"
format = "FreeDict"
description = "FreeDict (.tei)"
extensions = (".tei",)
extensionCreate = ".tei"
singleFile = True
kind = "text"
wiki = "https://github.com/freedict/fd-dictionaries/wiki"
website = (
	"https://freedict.org/",
	"FreeDict.org",
)
optionsProp: "dict[str, Option]" = {
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"discover": BoolOption(
		comment="Find and show unsupported tags",
	),
	"auto_rtl": BoolOption(
		allowNone=True,
		comment="Auto-detect and mark Right-to-Left text",
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
	"pron_color": StrOption(
		comment="Pronunciation color",
	),
	"gram_color": StrOption(
		comment="Grammar color",
	),
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
	),
}

tei = "{http://www.tei-c.org/ns/1.0}"
ENTRY = f"{tei}entry"
INCLUDE = "{http://www.w3.org/2001/XInclude}include"


class Reader:
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_discover: bool = False
	_auto_rtl: "bool | None" = None
	_word_title: bool = False
	_pron_color: str = "gray"
	_gram_color: str = "green"

	_example_padding: int = 10

	ns = {
		None: "http://www.tei-c.org/ns/1.0",
	}
	xmlLang = "{http://www.w3.org/XML/1998/namespace}lang"

	supportedTags = {
		f"{tei}{tag}" for tag in (
			"entry",
			"form",  # entry.form
			"orth",  # entry.form.orth
			"pron",  # entry.form.pron
			"sense",  # entry.sense
			"cit",  # entry.sense.cit
			"quote",  # entry.sense.cit.quote
			"gramGrp",  # entry.sense.cit.gramGrp
			"pos",  # entry.sense.cit.gramGrp.pos
			"gen",  # entry.sense.cit.gramGrp.gen
			"number",  # entry.sense.cit.gramGrp.number
			"num",  # entry.sense.cit.gramGrp.num
		)
	}
	posMapping = {
		"n": "noun",
		"v": "verb",
		"pn": "pronoun",
		"pron": "pronoun",
		"prep": "preposition",
		"conj": "conjunction",
		"adj": "adjective",
		"adv": "adverb",
		# "numeral", "interjection", "suffix", "particle"
		# "indefinitePronoun"
	}
	genderMapping = {
		"m": "male",
		"masc": "male",
		"f": "female",
		"fem": "female",
		"n": "neutral",
		"neut": "neutral",
		# "m;f"
		"adj": "adjective",
	}
	numberMapping = {
		"pl": "plural",
		"sing": "singular",
	}
	subcMapping = {
		"t": "transitive",
		"i": "intransitive",
	}
	gramClass = "grammar"

	def makeList(
		self,
		hf: "T_htmlfile",
		input_objects: "list[Any]",
		processor: "Callable",
		single_prefix: str = "",
		skip_single: bool = True,
		ordered: bool = True,
		list_type: str = "",
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			if single_prefix:
				hf.write(single_prefix)
			processor(hf, input_objects[0])
			return

		attrib: "dict[str, str]" = {}
		if list_type:
			attrib["type"] = list_type

		with hf.element("ol" if ordered else "ul", attrib=attrib):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el)

	def getTitleTag(self, sample: str) -> str:
		ws = getWritingSystemFromText(sample)
		if ws:
			return ws.titleTag
		return "b"

	def writeRef(
		self,
		hf: "T_htmlfile",
		ref: "Element",
	) -> None:
		target = ref.get("target")
		attrib: "dict[str, str]" = {}
		if target:
			if "://" in target:
				attrib["class"] = "external"
		else:
			target = f"bword://{ref.text}"
		with hf.element("a", href=target, attrib=attrib):
			hf.write(ref.text or "")

	def writeQuote(
		self,
		hf: "T_htmlfile",
		elem: "Element",
	) -> None:
		self.writeWithDirection(hf, elem, "div")

	def writeTransCit(
		self,
		hf: "T_htmlfile",
		elem: "Element",
	) -> None:
		from lxml import etree as ET
		quotes = []
		sense = ET.Element(f"{tei}sense")
		for child in elem.xpath("child::node()"):
			if isinstance(child, str):
				child = child.strip()
				if child:
					hf.write(child)
					log.warning("text directly inside <cit>")
				continue

			if child.__class__.__name__ == "_Comment":
				continue

			if child.tag == f"{tei}quote":
				quotes.append(child)
				continue

			if child.tag in (f"{tei}gramGrp", f"{tei}usg", f"{tei}note"):
				sense.append(child)
				continue

			if child.tag == f"{tei}cit":
				# TODO
				continue

			log.warning(
				f"unknown tag {child.tag!r} inside translation <cit>"
				f": {self.tostring(child)}",
			)

		self.makeList(
			hf,
			quotes,
			self.writeQuote,
			single_prefix="",
		)
		if next(sense.iterchildren(), False) is not None:
			self.writeSense(hf, sense)

	def writeDef(
		self,
		hf: "T_htmlfile",
		elem: "Element",
	) -> None:
		sep = ", "  # TODO: self.getCommaSep(sample)
		# if self._cif_newline:
		# 	sep = ET.Element("br")
		count = 0

		def writeChild(item: "str | Element", depth: int) -> None:
			nonlocal count
			if isinstance(item, str):
				item = item.strip()
				if not item:
					return
				if count > 0:
					hf.write(sep)
				# with hf.element(self.getTitleTag(item)):
				hf.write(item)
				return

			if item.tag == f"{tei}ref":
				if count > 0:
					hf.write(sep)
				self.writeRef(hf, item)
				return

			for child in item.xpath("child::node()"):
				writeChild(child, depth + 1)
			if depth < 1:
				count += 1

		for child in elem.xpath("child::node()"):
			writeChild(child, 0)

	def writeWithDirection(
		self,
		hf: "T_htmlfile",
		child: "Element",
		tag: str,
	) -> None:
		attrib = dict(child.attrib)
		try:
			lang = attrib.pop(self.xmlLang)
		except KeyError:
			pass
		else:
			attrib["lang"] = lang
			if self._auto_rtl:
				langObj = langDict[lang]
				if langObj:
					if langObj.rtl:
						attrib["dir"] = "rtl"
					else:
						attrib["dir"] = "ltr"
		try:
			_type = attrib.pop("type")
		except KeyError:
			pass
		else:
			if _type != "trans":
				attrib["class"] = _type
		with hf.element(tag, attrib=attrib):
			self.writeRichText(hf, child)

	def writeRichText(
		self,
		hf: "T_htmlfile",
		el: "Element",
	) -> None:
		from lxml import etree as ET
		for child in el.xpath("child::node()"):
			if isinstance(child, str):
				hf.write(child)
				continue
			if child.tag == f"{tei}ref":
				self.writeRef(hf, child)
				continue
			if child.tag == f"{tei}br":
				hf.write(ET.Element("br"))
				continue
			if child.tag == f"{tei}p":
				with hf.element("p", **child.attrib):
					self.writeRichText(hf, child)
					continue
			if child.tag == f"{tei}div":
				self.writeWithDirection(hf, child, "div")
				continue
			if child.tag == f"{tei}span":
				self.writeWithDirection(hf, child, "span")
				continue

			self.writeRichText(hf, child)

	def getLangDesc(self, elem: "Element") -> "str | None":
		lang = elem.attrib.get(self.xmlLang)
		if lang:
			langObj = langDict[lang]
			if not langObj:
				log.warning(f"unknown lang {lang!r} in {self.tostring(elem)}")
				return None
			return langObj.name

		orig = elem.attrib.get("orig")
		if orig:
			return orig

		log.warning(f"unknown lang name in {self.tostring(elem)}")
		return None

	def writeLangTag(
		self,
		hf: "T_htmlfile",
		elem: "Element",
	) -> None:
		langDesc = self.getLangDesc(elem)
		if not langDesc:
			return
		# TODO: make it Italic or change font color?
		if elem.text:
			hf.write(f"{langDesc}: {elem.text}")
		else:
			hf.write(f"{langDesc}")

	def writeNote(
		self,
		hf: "T_htmlfile",
		note: "Element",
	) -> None:
		self.writeRichText(hf, note)

	def writeSenseSense(
		self,
		hf: "T_htmlfile",
		sense: "Element",
	) -> int:
		# this <sense> element can be 1st-level (directly under <entry>)
		# or 2nd-level
		transCits = []
		defList = []
		gramList = []
		noteList = []
		refList = []
		usgList = []
		xrList = []
		exampleCits = []
		for child in sense.iterchildren():
			if child.tag == f"{tei}cit":
				if child.attrib.get("type", "trans") == "trans":
					transCits.append(child)
				elif child.attrib.get("type") == "example":
					exampleCits.append(child)
				else:
					log.warning(f"unknown cit type: {self.tostring(child)}")
				continue

			if child.tag == f"{tei}def":
				defList.append(child)
				continue

			if child.tag == f"{tei}note":
				_type = child.attrib.get("type")
				if not _type:
					noteList.append(child)
				elif _type in ("pos", "gram"):
					gramList.append(child)
				elif _type in (
					"sense", "stagr", "stagk", "def", "usage", "hint",
					"status", "editor", "dom", "infl", "obj", "lbl",
				):
					noteList.append(child)
				else:
					log.warning(f"unknown note type {_type}")
					noteList.append(child)
				continue

			if child.tag == f"{tei}ref":
				refList.append(child)
				continue

			if child.tag == f"{tei}usg":
				if not child.text:
					log.warning(f"empty usg: {self.tostring(child)}")
					continue
				usgList.append(child)
				continue

			if child.tag == f"{tei}lang":
				self.writeLangTag(hf, child)
				continue

			if child.tag in (f"{tei}sense", f"{tei}gramGrp"):
				continue

			if child.tag == f"{tei}xr":
				xrList.append(child)
				continue

			log.warning(f"unknown tag {child.tag} in <sense>")

		self.makeList(
			hf,
			defList,
			self.writeDef,
			single_prefix="",
		)
		if gramList:
			color = self._gram_color
			attrib = {
				"class": self.gramClass,
			}
			if color:
				attrib["color"] = color
			with hf.element("div"):
				for i, gram in enumerate(gramList):
					text = gram.text or ""
					if i > 0:
						hf.write(self.getCommaSep(text))
					with hf.element("font", attrib=attrib):
						hf.write(text)
		self.makeList(
			hf,
			noteList,
			self.writeNote,
			single_prefix="",
		)
		self.makeList(
			hf,
			transCits,
			self.writeTransCit,
			single_prefix="",
		)
		if refList:
			with hf.element("div"):
				hf.write("Related: ")
				for i, ref in enumerate(refList):
					if i > 0:
						hf.write(" | ")
					self.writeRef(hf, ref)
		if xrList:
			for xr in xrList:
				with hf.element("div"):
					self.writeRichText(hf, xr)
		if usgList:
			with hf.element("div"):
				hf.write("Usage: ")
				for i, usg in enumerate(usgList):
					text = usg.text or ""
					if i > 0:
						hf.write(self.getCommaSep(text))
					hf.write(text)
		if exampleCits:
			for cit in exampleCits:
				with hf.element("div", attrib={
					"class": "example",
					"style": f"padding: {self._example_padding}px 0px;",
				}):
					for quote in cit.findall("quote", self.ns):
						self.writeWithDirection(hf, quote, "div")
					for cit2 in cit.findall("cit", self.ns):
						for quote in cit2.findall("quote", self.ns):
							quote.attrib.update(cit2.attrib)
							self.writeWithDirection(hf, quote, "div")

		return len(transCits) + len(exampleCits)

	def getCommaSep(self, sample: str) -> str:
		if self._auto_rtl:
			ws = getWritingSystemFromText(sample)
			if ws:
				return ws.comma + " "
		return ", "

	def writeGramGroups(
		self,
		hf: "T_htmlfile",
		gramGrpList: "list[Element]",
	) -> None:
		from lxml import etree as ET

		color = self._gram_color
		attrib = {
			"class": self.gramClass,
		}
		if color:
			attrib["color"] = color

		for gramGrp in gramGrpList:
			parts = []
			for child in gramGrp.iterchildren():
				part = self.normalizeGramGrpChild(child)
				if part:
					parts.append(part)
			if not parts:
				continue

			sep = self.getCommaSep(parts[0])
			text = sep.join(parts)

			with hf.element("font", attrib=attrib):
				hf.write(text)

			hf.write(ET.Element("br"))

	def writeSenseGrams(
		self,
		hf: "T_htmlfile",
		sense: "Element",
	) -> None:
		self.writeGramGroups(hf, sense.findall("gramGrp", self.ns))

	def writeSense(
		self,
		hf: "T_htmlfile",
		sense: "Element",
	) -> None:
		# this <sense> element is 1st-level (directly under <entry>)
		self.writeSenseGrams(hf, sense)
		self.makeList(
			hf,
			sense.findall("sense", self.ns),
			self.writeSenseSense,
			single_prefix="",
		)
		self.writeSenseSense(hf, sense)

	def getDirection(self, elem: "Element") -> str:
		lang = elem.get(self.xmlLang)
		if lang is None:
			return ""
		langObj = langDict[lang]
		if langObj is None:
			log.warning(f"unknown language {lang}")
			return ""
		if langObj.rtl:
			return "rtl"
		return ""

	def writeSenseList(
		self,
		hf: "T_htmlfile",
		senseList: "list[Element]",
	) -> None:
		# these <sense> elements are 1st-level (directly under <entry>)
		if not senseList:
			return

		if self._auto_rtl and self.getDirection(senseList[0]) == "rtl":
			with hf.element("div", dir="rtl"):
				self.makeList(
					hf, senseList,
					self.writeSense,
					ordered=(len(senseList) > 3),
				)
			return

		self.makeList(
			hf, senseList,
			self.writeSense,
			# list_type="A",
		)

	def normalizeGramGrpChild(self, elem: "Element") -> str:
		# child can be "pos" or "gen"
		tag = elem.tag
		text = elem.text
		if not text:
			return ""
		text = text.strip()
		if tag == f"{tei}pos":
			return self.posMapping.get(text.lower(), text)
		if tag == f"{tei}gen":
			return self.genderMapping.get(text.lower(), text)
		if tag in (f"{tei}num", f"{tei}number"):
			return self.numberMapping.get(text.lower(), text)
		if tag == f"{tei}subc":
			return self.subcMapping.get(text.lower(), text)
		if tag == f"{tei}gram":
			_type = elem.get("type")
			if _type:
				if _type == "pos":
					return self.posMapping.get(text.lower(), text)
				if _type == "gen":
					return self.genderMapping.get(text.lower(), text)
				if _type in ("num", "number"):
					return self.numberMapping.get(text.lower(), text)
				if _type == "subc":
					return self.subcMapping.get(text.lower(), text)
				log.warning(f"unrecognize type={_type!r}: {self.tostring(elem)}")
				return text

			log.warning(f"<gram> with no type: {self.tostring(elem)}")
			return text

		if tag == f"{tei}note":
			return text

		if tag == f"{tei}colloc":
			return ""

		log.warning(
			f"unrecognize GramGrp child tag: {elem.tag!r}"
			f": {self.tostring(elem)}",
		)
		return ""

	def getEntryByElem(
		self,
		entry:
		"Element",
	) -> "EntryType":
		from lxml import etree as ET
		glos = self._glos
		keywords = []
		f = BytesIO()
		pron_color = self._pron_color

		if self._discover:
			for elem in entry.iter():
				if elem.tag not in self.supportedTags:
					self._discoveredTags[elem.tag] = elem

		def br() -> "Element":
			return ET.Element("br")

		inflectedKeywords = []

		for form in entry.findall("form", self.ns):
			inflected = form.get("type") == "infl"
			for orth in form.findall("orth", self.ns):
				if not orth.text:
					continue
				if inflected:
					inflectedKeywords.append(orth.text)
				else:
					keywords.append(orth.text)

		keywords += inflectedKeywords

		pronList = [
			pron.text.strip('/')
			for pron in entry.findall("form/pron", self.ns)
			if pron.text
		]
		senseList = entry.findall("sense", self.ns)

		with ET.htmlfile(f, encoding="utf-8") as hf:
			with hf.element("div"):
				if self._word_title:
					for keyword in keywords:
						with hf.element(glos.titleTag(keyword)):
							hf.write(keyword)
						hf.write(br())

				# TODO: "form/usg"
				# <usg type="geo">Brit</usg>
				# <usg type="geo">US</usg>
				# <usg type="hint">...</usg>

				if pronList:
					for i, pron in enumerate(pronList):
						if i > 0:
							hf.write(self.getCommaSep(pron))
						hf.write("/")
						with hf.element("font", color=pron_color):
							hf.write(f"{pron}")
						hf.write("/")
					hf.write(br())
					hf.write("\n")

				_hf = cast("T_htmlfile", hf)
				self.writeGramGroups(_hf, entry.findall("gramGrp", self.ns))
				self.writeSenseList(_hf, senseList)

		defi = f.getvalue().decode("utf-8")
		# defi = defi.replace("\xa0", "&nbsp;")  # do we need to do this?
		_file = self._file
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="h",
			byteProgress=(_file.tell(), self._fileSize),
		)

	def setWordCount(self, header: "Element") -> None:
		extent_elem = header.find(".//extent", self.ns)
		if extent_elem is None:
			log.warning(
				"did not find 'extent' tag in metedata"
				", progress bar will not word",
			)
			return
		extent = extent_elem.text or ""
		if not extent.endswith(" headwords"):
			log.warning(f"unexpected {extent=}")
			return
		try:
			self._wordCount = int(extent.split(" ")[0].replace(",", ""))
		except Exception:
			log.exception(f"unexpected {extent=}")

	def tostring(self, elem: "Element") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def stripParag(self, elem: "Element") -> str:
		text = self.tostring(elem)
		text = self._p_pattern.sub("\\2", text)
		return text  # noqa: RET504

	def stripParagList(
		self,
		elems: "list[Element]",
	) -> str:
		lines = []
		for elem in elems:
			for line in self.stripParag(elem).split("\n"):
				line = line.strip()
				if not line:
					continue
				lines.append(line)
		return "\n".join(lines)

	def setGlosInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, unescape_unicode(value))

	def setCopyright(self, header: "Element") -> None:
		elems = header.findall(".//availability//p", self.ns)
		if not elems:
			log.warning("did not find copyright")
			return
		_copyright = self.stripParagList(elems)
		_copyright = self.replaceRefLink(_copyright)
		self.setGlosInfo("copyright", _copyright)
		log.debug(f"Copyright: {_copyright!r}")

	def setPublisher(self, header: "Element") -> None:
		elem = header.find(".//publisher", self.ns)
		if elem is None or not elem.text:
			log.warning("did not find publisher")
			return
		self.setGlosInfo("publisher", elem.text)

	def setCreationTime(self, header: "Element") -> None:
		elem = header.find(".//publicationStmt/date", self.ns)
		if elem is None or not elem.text:
			return
		self.setGlosInfo("creationTime", elem.text)

	def replaceRefLink(self, text: str) -> str:
		return self._ref_pattern.sub('<a href="\\1">\\2</a>', text)

	def setDescription(self, header: "Element") -> None:
		elems = []
		for tag in ("sourceDesc", "projectDesc"):
			elems += header.findall(f".//{tag}//p", self.ns)
		desc = self.stripParagList(elems)
		if not desc:
			return

		website_list = []
		for match in self._website_pattern.findall(desc):
			if not match[1]:
				continue
			website_list.append(match[1])
		if website_list:
			website = " | ".join(website_list)
			self.setGlosInfo("website", website)
			desc = self._website_pattern.sub("", desc).strip()
			log.debug(f"Website: {website}")

		desc = self.replaceRefLink(desc)
		self.setGlosInfo("description", desc)
		log.debug(
			"------------ Description: ------------\n"
			f"{desc}\n"
			"--------------------------------------",
		)

	def setMetadata(self, header: "Element") -> None:
		self.setWordCount(header)
		title = header.find(".//title", self.ns)
		if title is not None and title.text:
			self.setGlosInfo("name", title.text)

		edition = header.find(".//edition", self.ns)
		if edition is not None and edition.text:
			self.setGlosInfo("edition", edition.text)

		self.setCopyright(header)
		self.setPublisher(header)
		self.setCreationTime(header)
		self.setDescription(header)

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dirname = ""
		self._file: "IOBase" = nullBinaryIO
		self._fileSize = 0
		self._wordCount = 0
		self._discoveredTags: "dict[str, Element]" = {}

		self._p_pattern = re.compile(
			'<p( [^<>]*?)?>(.*?)</p>',
			re.DOTALL,
		)
		self._ref_pattern = re.compile(
			'<ref target="(.*?)">(.*?)</ref>',
		)
		self._website_pattern = re.compile(
			'Home: <(ref|ptr) target="(.*)">(.*)</\\1>',
		)

	def __len__(self) -> int:
		return self._wordCount

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
			e.msg += f", run `{pip} install lxml` to install"
			raise e

		self._filename = filename
		self._dirname = dirname(filename)
		cfile = compressionOpen(filename, mode="rb")

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("FreeDict Reader: file is not seekable")

		self._glos.setDefaultDefiFormat("h")

		if self._word_title:
			self._glos.setInfo("definition_has_headwords", "True")

		context = ET.iterparse(  # type: ignore # noqa: PGH003
			cfile,
			events=("end",),
			tag=f"{tei}teiHeader",
		)
		for _, elem in context:
			self.setMetadata(elem)  # type: ignore
			break

		cfile.close()

	def loadInclude(self, elem: "Element") -> "Reader | None":
		href = elem.attrib.get("href")
		if not href:
			log.error(f"empty href in {elem}")
			return None
		filename = join(self._dirname, href)
		if not isfile(filename):
			log.error(f"no such file {filename!r} from {elem}")
			return None
		reader = Reader(self._glos)
		for optName in optionsProp:
			attr = "_" + optName
			if hasattr(self, attr):
				setattr(reader, attr, getattr(self, attr))
		reader.open(filename)
		return reader

	def __iter__(self) -> "Iterator[EntryType]":
		from lxml import etree as ET

		if self._auto_rtl is None:
			glos = self._glos
			if (
				glos.sourceLang and glos.sourceLang.rtl or
				glos.targetLang and glos.targetLang.rtl
			):
				log.info("setting auto_rtl=True")
				self._auto_rtl = True

		self._file = compressionOpen(self._filename, mode="rb")
		context = ET.iterparse(  # type: ignore # noqa: PGH003
			self._file,
			events=("end",),
			tag=(ENTRY, INCLUDE),
		)
		for _, _elem in context:
			elem = cast("Element", _elem)

			if elem.tag == INCLUDE:
				reader = self.loadInclude(elem)
				if reader is not None:
					yield from reader
					reader.close()
				continue

			yield self.getEntryByElem(elem)
			# clean up preceding siblings to save memory
			# this can reduce memory usage from 1 GB to ~25 MB
			parent = elem.getparent()
			if parent is None:
				continue
			while elem.getprevious() is not None:
				del parent[0]

		if self._discoveredTags:
			log.info("Found unsupported tags")
			for _, elem in self._discoveredTags.items():
				log.info(f"{self.tostring(elem)}\n")
