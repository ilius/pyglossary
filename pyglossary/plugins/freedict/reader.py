# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO, IOBase
from os.path import dirname, isfile, join
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.lxml_types import Element, T_htmlfile


from pyglossary.compression import compressionOpen, stdCompressions
from pyglossary.core import exc_note, log, pip
from pyglossary.html_utils import unescape_unicode
from pyglossary.io_utils import nullBinaryIO
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText

from .options import optionsProp
from .utils import XMLLANG, ReaderUtils

__all__ = ["Reader"]


TEI = "{http://www.tei-c.org/ns/1.0}"
ENTRY = f"{TEI}entry"
INCLUDE = "{http://www.w3.org/2001/XInclude}include"
NAMESPACE = {None: "http://www.tei-c.org/ns/1.0"}


@dataclass(slots=True)
class ParsedSense:
	transCits: list[Element]
	defs: list[Element]
	grams: list[Element]
	notes: list[Element]
	refs: list[Element]
	usages: list[Element]
	xrList: list[Element]
	exampleCits: list[Element]
	langs: list[Element]


class Reader(ReaderUtils):
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_discover: bool = False
	_auto_rtl: bool | None = None
	_auto_comma: bool = True
	_comma: str = ", "
	_word_title: bool = False
	_pron_color: str = "gray"
	_gram_color: str = "green"

	_example_padding: int = 10

	gramClass = "grammar"

	supportedTags: set[str] = {
		f"{TEI}{tag}"
		for tag in (
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
	posMapping: dict[str, str] = {
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
	genderMapping: dict[str, str] = {
		"m": "male",
		"masc": "male",
		"f": "female",
		"fem": "female",
		"n": "neutral",
		"neut": "neutral",
		# "m;f"
		"adj": "adjective",
	}
	numberMapping: dict[str, str] = {
		"pl": "plural",
		"sing": "singular",
	}
	subcMapping: dict[str, str] = {
		"t": "transitive",
		"i": "intransitive",
	}
	noteTypes: set[str] = {
		"sense",
		"stagr",
		"stagk",
		"def",
		"usage",
		"hint",
		"status",
		"editor",
		"dom",
		"infl",
		"obj",
		"lbl",
	}

	def writeRef(  # noqa: PLR6301
		self,
		hf: T_htmlfile,
		ref: Element,
	) -> None:
		target = ref.get("target")
		attrib: dict[str, str] = {}
		if target:
			if "://" in target:
				attrib["class"] = "external"
		else:
			target = f"bword://{ref.text}"
		with hf.element("a", href=target, attrib=attrib):
			hf.write(ref.text or "")

	def writeQuote(
		self,
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		self.writeWithDirection(hf, elem, "div")

	def writeTransCit(
		self,
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		from lxml import etree as ET

		children = elem.xpath("child::node()")
		if not children:
			return
		assert isinstance(children, list)

		quotes: list[Element] = []
		sense = ET.Element(f"{TEI}sense")
		for child in children:
			if isinstance(child, str):
				child = child.strip()  # noqa: PLW2901
				if child:
					hf.write(child)
					log.warning(f"text directly inside <cit>: {child}")
				continue

			if child.__class__.__name__ == "_Comment":
				continue

			if child.tag == f"{TEI}quote":
				quotes.append(child)
				continue

			if child.tag in {f"{TEI}gramGrp", f"{TEI}usg", f"{TEI}note"}:
				sense.append(child)
				continue

			if child.tag == f"{TEI}cit":
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
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		# sep = None
		# if self._cif_newline:
		# 	sep = ET.Element("br")
		count = 0

		def writeChild(item: str | Element, depth: int) -> None:
			nonlocal count
			if isinstance(item, str):
				item = item.strip()
				if not item:
					return
				if count > 0:
					hf.write(self.getCommaSep(item))
				# with hf.element(self.getTitleTag(item)):
				hf.write(item)
				return

			if item.tag == f"{TEI}ref":
				if item.text:
					if count > 0:
						hf.write(self.getCommaSep(item.text))
					self.writeRef(hf, item)
				else:
					log.warning(f"ref without text: {self.tostring(item)}")
				return

			for child in item.xpath("child::node()"):
				writeChild(child, depth + 1)
			if depth < 1:
				count += 1

		for child in elem.xpath("child::node()"):
			writeChild(child, 0)

	def setAttribLangDir(
		self,
		attrib: dict[str, str],
	) -> None:
		try:
			lang = attrib.pop(XMLLANG)
		except KeyError:
			return

		attrib["lang"] = lang

		if self._auto_rtl:
			langObj = langDict[lang]
			if langObj:
				attrib["dir"] = "rtl" if langObj.rtl else "ltr"

	def writeWithDirection(
		self,
		hf: T_htmlfile,
		child: Element,
		tag: str,
	) -> None:
		attrib: dict[str, str] = dict(child.attrib)

		self.setAttribLangDir(attrib)

		try:
			type_ = attrib.pop("type")
		except KeyError:
			pass
		else:
			if type_ != "trans":
				attrib["class"] = type_

		with hf.element(tag, attrib=attrib):
			self.writeRichText(hf, child)

	def writeRichText(
		self,
		hf: T_htmlfile,
		el: Element,
	) -> None:
		from lxml import etree as ET

		for child in el.xpath("child::node()"):
			if isinstance(child, str):
				hf.write(child)
				continue
			if child.tag == f"{TEI}ref":
				self.writeRef(hf, child)
				continue
			if child.tag == f"{TEI}br":
				hf.write(ET.Element("br"))
				continue
			if child.tag == f"{TEI}p":
				with hf.element("p", **child.attrib):
					self.writeRichText(hf, child)
					continue
			if child.tag == f"{TEI}div":
				self.writeWithDirection(hf, child, "div")
				continue
			if child.tag == f"{TEI}span":
				self.writeWithDirection(hf, child, "span")
				continue

			self.writeRichText(hf, child)

	def writeNote(
		self,
		hf: T_htmlfile,
		note: Element,
	) -> None:
		self.writeRichText(hf, note)

	def parseSenseSense(  # noqa: PLR0912
		self,
		sense: Element,
	) -> ParsedSense:
		# this <sense> element can be 1st-level (directly under <entry>)
		# or 2nd-level
		transCits: list[Element] = []
		defs: list[Element] = []
		grams: list[Element] = []
		notes: list[Element] = []
		refs: list[Element] = []
		usages: list[Element] = []
		xrList: list[Element] = []
		exampleCits: list[Element] = []
		langs: list[Element] = []
		for child in sense.iterchildren():
			if child.tag == f"{TEI}cit":
				if child.attrib.get("type", "trans") == "trans":
					transCits.append(child)
				elif child.attrib.get("type") == "example":
					exampleCits.append(child)
				else:
					log.warning(f"unknown cit type: {self.tostring(child)}")
				continue

			if child.tag == f"{TEI}def":
				defs.append(child)
				continue

			if child.tag == f"{TEI}note":
				type_ = child.attrib.get("type")
				if not type_:
					notes.append(child)
				elif type_ in {"pos", "gram"}:
					grams.append(child)
				elif type_ in self.noteTypes:
					notes.append(child)
				else:
					log.warning(f"unknown note type {type_}")
					notes.append(child)
				continue

			if child.tag == f"{TEI}ref":
				refs.append(child)
				continue

			if child.tag == f"{TEI}usg":
				if not child.text:
					log.warning(f"empty usg: {self.tostring(child)}")
					continue
				usages.append(child)
				continue

			if child.tag == f"{TEI}lang":
				langs.append(child)
				continue

			if child.tag in {f"{TEI}sense", f"{TEI}gramGrp"}:
				continue

			if child.tag == f"{TEI}xr":
				xrList.append(child)
				continue

			log.warning(f"unknown tag {child.tag} in <sense>")

		return ParsedSense(
			transCits=transCits,
			defs=defs,
			grams=grams,
			notes=notes,
			refs=refs,
			usages=usages,
			xrList=xrList,
			exampleCits=exampleCits,
			langs=langs,
		)

	# TODO: break it down
	# PLR0912 Too many branches (16 > 12)
	def writeSenseSense(  # noqa: PLR0912
		self,
		hf: T_htmlfile,
		sense: Element,
	) -> int:
		# this <sense> element can be 1st-level (directly under <entry>)
		# or 2nd-level
		ps = self.parseSenseSense(sense)

		for child in ps.langs:
			self.writeLangTag(hf, child)

		self.makeList(
			hf,
			ps.defs,
			self.writeDef,
			single_prefix="",
		)
		if ps.grams:
			color = self._gram_color
			attrib = {
				"class": self.gramClass,
			}
			if color:
				attrib["color"] = color
			with hf.element("div"):
				for i, gram in enumerate(ps.grams):
					text = gram.text or ""
					if i > 0:
						hf.write(self.getCommaSep(text))
					with hf.element("font", attrib=attrib):
						hf.write(text)
		self.makeList(
			hf,
			ps.notes,
			self.writeNote,
			single_prefix="",
		)
		self.makeList(
			hf,
			ps.transCits,
			self.writeTransCit,
			single_prefix="",
		)
		if ps.refs:
			with hf.element("div"):
				hf.write("Related: ")
				for i, ref in enumerate(ps.refs):
					if i > 0:
						hf.write(" | ")
					self.writeRef(hf, ref)
		for xr in ps.xrList:
			with hf.element("div"):
				self.writeRichText(hf, xr)
		if ps.usages:
			with hf.element("div"):
				hf.write("Usage: ")
				for i, usg in enumerate(ps.usages):
					text = usg.text or ""
					if i > 0:
						hf.write(self.getCommaSep(text))
					hf.write(text)
		for cit in ps.exampleCits:
			with hf.element(
				"div",
				attrib={
					"class": "example",
					"style": f"padding: {self._example_padding}px 0px;",
				},
			):
				for quote in cit.findall("quote", NAMESPACE):
					self.writeWithDirection(hf, quote, "div")
				for cit2 in cit.findall("cit", NAMESPACE):
					for quote in cit2.findall("quote", NAMESPACE):
						quote.attrib.update(cit2.attrib)
						self.writeWithDirection(hf, quote, "div")

		return len(ps.transCits) + len(ps.exampleCits)

	def getCommaSep(self, sample: str) -> str:
		if sample and self._auto_comma:
			ws = getWritingSystemFromText(sample)
			if ws:
				return ws.comma
		return self._comma

	def writeGramGroups(
		self,
		hf: T_htmlfile,
		gramGrpList: list[Element],
	) -> None:
		from lxml import etree as ET

		color = self._gram_color
		attrib = {
			"class": self.gramClass,
		}
		if color:
			attrib["color"] = color

		for gramGrp in gramGrpList:
			parts: list[str] = []
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

	def writeGramGroupChildren(
		self,
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		self.writeGramGroups(hf, elem.findall("gramGrp", NAMESPACE))

	def writeSense(
		self,
		hf: T_htmlfile,
		sense: Element,
	) -> None:
		# this <sense> element is 1st-level (directly under <entry>)
		self.writeGramGroupChildren(hf, sense)
		self.makeList(
			hf,
			sense.findall("sense", NAMESPACE),
			self.writeSenseSense,
			single_prefix="",
		)
		self.writeSenseSense(hf, sense)

	def writeSenseList(
		self,
		hf: T_htmlfile,
		senseList: list[Element],
	) -> None:
		# these <sense> elements are 1st-level (directly under <entry>)
		if not senseList:
			return

		if self._auto_rtl and self.isRTL(senseList[0]):
			with hf.element("div", dir="rtl"):
				self.makeList(
					hf,
					senseList,
					self.writeSense,
					ordered=(len(senseList) > 3),
				)
			return

		self.makeList(
			hf,
			senseList,
			self.writeSense,
			# list_type="A",
		)

	def normalizeGramGrpChild(self, elem: Element) -> str:  # noqa: PLR0912
		# child can be "pos" or "gen"
		tag = elem.tag
		text = elem.text
		if not text:
			return ""
		text = text.strip()
		if tag == f"{TEI}pos":
			return self.posMapping.get(text.lower(), text)
		if tag == f"{TEI}gen":
			return self.genderMapping.get(text.lower(), text)
		if tag in {f"{TEI}num", f"{TEI}number"}:
			return self.numberMapping.get(text.lower(), text)
		if tag == f"{TEI}subc":
			return self.subcMapping.get(text.lower(), text)
		if tag == f"{TEI}gram":
			type_ = elem.get("type")
			if type_:
				if type_ == "pos":
					return self.posMapping.get(text.lower(), text)
				if type_ == "gen":
					return self.genderMapping.get(text.lower(), text)
				if type_ in {"num", "number"}:
					return self.numberMapping.get(text.lower(), text)
				if type_ == "subc":
					return self.subcMapping.get(text.lower(), text)
				log.warning(f"unrecognize type={type_!r}: {self.tostring(elem)}")
				return text

			log.warning(f"<gram> with no type: {self.tostring(elem)}")
			return text

		if tag == f"{TEI}note":
			return text

		if tag == f"{TEI}colloc":
			return ""

		log.warning(
			f"unrecognize GramGrp child tag: {elem.tag!r}: {self.tostring(elem)}",
		)
		return ""

	def getEntryByElem(  # noqa: PLR0912
		self,
		entry: Element,
	) -> EntryType:
		from lxml import etree as ET

		glos = self._glos
		keywords: list[str] = []
		buff = BytesIO()
		pron_color = self._pron_color

		if self._discover:
			for elem in entry.iter():
				if elem.tag not in self.supportedTags:
					self._discoveredTags[elem.tag] = elem

		def br() -> Element:
			return ET.Element("br")

		inflectedKeywords: list[str] = []

		for form in entry.findall("form", NAMESPACE):
			inflected = form.get("type") == "infl"
			for orth in form.findall("orth", NAMESPACE):
				if not orth.text:
					continue
				if inflected:
					inflectedKeywords.append(orth.text)
				else:
					keywords.append(orth.text)

		keywords += inflectedKeywords

		pronList = [
			pron.text.strip("/")
			for pron in entry.findall("form/pron", NAMESPACE)
			if pron.text
		]
		senseList = entry.findall("sense", NAMESPACE)

		with ET.htmlfile(buff, encoding="utf-8") as hf:
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
							hf.write(pron)
						hf.write("/")
					hf.write(br())
					hf.write("\n")

				hf_ = cast("T_htmlfile", hf)
				self.writeGramGroupChildren(hf_, entry)
				self.writeSenseList(hf_, senseList)

		defi = buff.getvalue().decode("utf-8")
		# defi = defi.replace("\xa0", "&nbsp;")  # do we need to do this?
		file = self._file
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="h",
			byteProgress=(file.tell(), self._fileSize) if self._progress else None,
		)

	def setWordCount(self, header: Element) -> None:
		extent_elem = header.find(".//extent", NAMESPACE)
		if extent_elem is None:
			log.warning(
				"did not find 'extent' tag in metedata, progress bar will not word",
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

	def stripParag(self, elem: Element) -> str:
		text = self.tostring(elem)
		text = self._p_pattern.sub("\\2", text)
		return text  # noqa: RET504

	def stripParagList(
		self,
		elems: list[Element],
	) -> str:
		lines: list[str] = []
		for elem in elems:
			for line in self.stripParag(elem).split("\n"):
				line = line.strip()  # noqa: PLW2901
				if not line:
					continue
				lines.append(line)
		return "\n".join(lines)

	def setGlosInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, unescape_unicode(value))

	def setCopyright(self, header: Element) -> None:
		elems = header.findall(".//availability//p", NAMESPACE)
		if not elems:
			log.warning("did not find copyright")
			return
		copyright_ = self.stripParagList(elems)
		copyright_ = self.replaceRefLink(copyright_)
		self.setGlosInfo("copyright", copyright_)
		log.debug(f"Copyright: {copyright_!r}")

	def setPublisher(self, header: Element) -> None:
		elem = header.find(".//publisher", NAMESPACE)
		if elem is None or not elem.text:
			log.warning("did not find publisher")
			return
		self.setGlosInfo("publisher", elem.text)

	def setCreationTime(self, header: Element) -> None:
		elem = header.find(".//publicationStmt/date", NAMESPACE)
		if elem is None or not elem.text:
			return
		self.setGlosInfo("creationTime", elem.text)

	def replaceRefLink(self, text: str) -> str:
		return self._ref_pattern.sub('<a href="\\1">\\2</a>', text)

	def setDescription(self, header: Element) -> None:
		elems: list[Element] = []
		for tag in ("sourceDesc", "projectDesc"):
			elems += header.findall(f".//{tag}//p", NAMESPACE)
		desc = self.stripParagList(elems)
		if not desc:
			return

		website_list: list[str] = []
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

	def setMetadata(self, header: Element) -> None:
		self.setWordCount(header)
		title = header.find(".//title", NAMESPACE)
		if title is not None and title.text:
			self.setGlosInfo("name", title.text)

		edition = header.find(".//edition", NAMESPACE)
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
		self._file: IOBase = nullBinaryIO
		self._fileSize = 0
		self._progress = True
		self._wordCount = 0
		self._discoveredTags: dict[str, Element] = {}

		self._p_pattern = re.compile(
			"<p( [^<>]*?)?>(.*?)</p>",
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
			exc_note(e, f"Run `{pip} install lxml` to install")
			raise

		self._filename = filename
		self._dirname = dirname(filename)
		cfile = compressionOpen(filename, mode="rb")

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			self._glos.setInfo("input_file_size", str(self._fileSize))
		else:
			log.warning("FreeDict Reader: file is not seekable")

		self._progress = self._glos.progressbar and self._fileSize

		self._glos.setDefaultDefiFormat("h")

		if self._word_title:
			self._glos.setInfo("definition_has_headwords", "True")

		context = ET.iterparse(  # type: ignore # noqa: PGH003
			cfile,
			events=("end",),
			tag=f"{TEI}teiHeader",
		)
		for _, elem in context:
			self.setMetadata(elem)  # type: ignore
			break

		cfile.close()

	def loadInclude(self, elem: Element) -> Reader | None:
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

	def __iter__(self) -> Iterator[EntryType]:
		from lxml import etree as ET

		if self._auto_rtl is None:
			glos = self._glos
			if (glos.sourceLang and glos.sourceLang.rtl) or (
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
			for elem in self._discoveredTags.values():
				log.info(f"{self.tostring(elem)}\n")
