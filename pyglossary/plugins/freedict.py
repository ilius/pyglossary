# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.xml_utils import xml_escape
from pyglossary.html_utils import unescape_unicode
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText
from io import BytesIO
import re
import html

enable = True
format = "FreeDict"
description = "FreeDict (.tei)"
extensions = (".tei",)
singleFile = True
optionsProp = {
	"resources": BoolOption(),
	"discover": BoolOption(),
	"auto_rtl": BoolOption(allowNone=True),
	"word_title": BoolOption(
		comment="add headwords title to begining of definition",
	),
	"pron_color": StrOption(
		comment="pronunciation color",
	),
	"gram_color": StrOption(
		comment="grammar color",
	),
}

# https://freedict.org/
# https://github.com/freedict/fd-dictionaries/wiki

tei = "{http://www.tei-c.org/ns/1.0}"


class Reader(object):
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_discover: bool = False
	_auto_rtl: "Optional[bool]" = None
	_word_title: bool = False
	_pron_color: str = "gray"
	_gram_color: str = "green"

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
		"conj": "conjuction",
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
	def makeList(
		self,
		hf: "lxml.etree.htmlfile",
		input_objects: "List[Any]",
		processor: "Callable",
		single_prefix="",
		skip_single=True,
		ordered=True,
		list_type="",
	):
		""" Wrap elements into <ol> if more than one element """

		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			if single_prefix:
				hf.write(single_prefix)
			processor(hf, input_objects[0])
			return

		kw = {}
		if list_type:
			kw["type"] = list_type

		with hf.element("ol" if ordered else "ul", **kw):
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
		hf: "lxml.etree.htmlfile",
		ref: "lxml.etree.Element",
	):
		target = ref.get("target")
		if not target:
			target = f"bword://{ref.text}"
		with hf.element("a", href=target):
			hf.write(ref.text)

	def writeCit(
		self,
		hf: "lxml.etree.htmlfile",
		cit: "lxml.etree.Element",
	):
		from lxml import etree as ET

		sep = ", "
		# if self._cif_newline:
		# 	sep = ET.Element("br")
		count = 0

		def writeChild(item, depth):
			nonlocal count
			if isinstance(item, str):
				item = item.rstrip()
				if not item:
					return
				if count > 0:
					hf.write(sep)
				with hf.element(self.getTitleTag(item)):
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

		for child in cit.xpath("child::node()"):
			writeChild(child, 0)

	def writeDivSpan(self, hf, child, tag):
		attrib = child.attrib
		try:
			lang = attrib.pop(self.xmlLang)
		except KeyError:
			pass
		else:
			if self._auto_rtl:
				langObj = langDict[lang]
				if langObj:
					if langObj.rtl:
						attrib["dir"] = "rtl"
					else:
						attrib["dir"] = "ltr"
		with hf.element(tag, **attrib):
			self.writeRichText(hf, child)

	def writeRichText(
		self,
		hf: "lxml.etree.htmlfile",
		el: "lxml.etree.Element",
	):
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
				self.writeDivSpan(hf, child, "div")
				continue
			if child.tag == f"{tei}span":
				self.writeDivSpan(hf, child, "span")
				continue

			self.writeRichText(hf, child)

	def writeSenseDefs(
		self,
		hf: "lxml.etree.htmlfile",
		sense: "lxml.etree.Element",
	):
		from lxml import etree as ET
		defiList = sense.findall("sense/def", self.ns)
		self.makeList(
			hf,
			defiList,
			self.writeRichText,
			single_prefix="",
		)
		if len(defiList) == 1:
			hf.write(ET.Element("br"))

	def writeSenseCits(
		self,
		hf: "lxml.etree.htmlfile",
		sense: "lxml.etree.Element",
	):
		# translations
		self.makeList(
			hf,
			sense.findall("cit", self.ns),
			self.writeCit,
			single_prefix="",
		)

	def writeGramGroups(
		self,
		hf: "lxml.etree.htmlfile",
		gramGrpList: "List[lxml.etree.htmlfile]",
	):
		from lxml import etree as ET

		auto_rtl = self._auto_rtl
		color = self._gram_color
		for gramGrp in gramGrpList:
			parts = []
			for child in gramGrp.iterchildren():
				part = self.normalizeGramGrpChild(child)
				if part:
					parts.append(part)
			if not parts:
				continue

			sep = ", "
			if auto_rtl:
				ws = getWritingSystemFromText(parts[0])
				if ws:
					sep = ws.comma + " "

			text = sep.join(parts)
			with hf.element("font", color=color):
				hf.write(text)

			hf.write(ET.Element("br"))

	def writeSenseGrams(
		self,
		hf: "lxml.etree.htmlfile",
		sense: "lxml.etree.Element",
	):
		self.writeGramGroups(hf, sense.findall("gramGrp", self.ns))

	def writeSense(
		self,
		hf: "lxml.etree.htmlfile",
		sense: "lxml.etree.Element",
	):
		self.writeSenseGrams(hf, sense)
		self.writeSenseDefs(hf, sense)
		self.writeSenseCits(hf, sense)

	def getDirection(self, elem: "lxml.etree.Element"):
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
		hf: "lxml.etree.htmlfile",
		senseList: "List[lxml.etree.Element]",
	):
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

	def normalizeGramGrpChild(self, elem) -> str:
		# child can be "pos" or "gen"
		tag = elem.tag
		text = elem.text.strip()
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
			else:
				log.warning(f"<gram> with no type: {self.tostring(elem)}")
				return text
		log.warning(f"unrecognize GramGrp child tag: {self.tostring(elem)}")
		return ""

	def getEntryByElem(self, entry: "lxml.etree.Element") -> "BaseEntry":
		from lxml import etree as ET
		glos = self._glos
		keywords = []
		f = BytesIO()
		pron_color = self._pron_color

		if self._discover:
			for elem in entry.iter():
				if elem.tag not in self.supportedTags:
					self._discoveredTags[elem.tag] = elem

		def br():
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
						with glos.titleElement(hf, keyword):
							hf.write(keyword)
						hf.write(br())

				# TODO: "form/usg"
				# <usg type="geo">Brit</usg>
				# <usg type="geo">US</usg>
				# <usg type="hint">...</usg>

				if pronList:
					for i, pron in enumerate(pronList):
						if i > 0:
							hf.write(", ")
						hf.write("/")
						with hf.element("font", color=pron_color):
							hf.write(f"{pron}")
						hf.write("/")
					hf.write(br())
					hf.write("\n")

				self.writeGramGroups(hf, entry.findall("gramGrp", self.ns))

				self.writeSenseList(hf, senseList)

		defi = f.getvalue().decode("utf-8")
		# defi = defi.replace("\xa0", "&nbsp;")  # do we need to do this?
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="h",
			byteProgress=(self._file.tell(), self._fileSize),
		)

	def setWordCount(self, header):
		extent_elem = header.find(".//extent", self.ns)
		if extent_elem is None:
			log.warn(
				"did not find 'extent' tag in metedata"
				", progress bar will not word"
			)
			return
		extent = extent_elem.text
		if not extent.endswith(" headwords"):
			log.warn(f"unexpected extent={extent}")
			return
		try:
			self._wordCount = int(extent.split(" ")[0])
		except Exception:
			log.exception(f"unexpected extent={extent}")

	def tostring(self, elem: "lxml.etree.Element") -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def stripParag(self, elem: "lxml.etree.Element") -> str:
		text = self.tostring(elem)
		text = self._p_pattern.sub("\\2", text)
		return text

	def stripParagList(self, elems: "List[lxml.etree.Element]") -> str:
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

	def setCopyright(self, header):
		elems = header.findall(".//availability//p", self.ns)
		if not elems:
			log.warn("did not find copyright")
			return
		copyright = self.stripParagList(elems)
		copyright = self.replaceRefLink(copyright)
		self.setGlosInfo("copyright", copyright)
		log.debug(f"Copyright: {copyright!r}")

	def setPublisher(self, header):
		elem = header.find(".//publisher", self.ns)
		if elem is None or not elem.text:
			log.warn("did not find publisher")
			return
		self.setGlosInfo("publisher", elem.text)

	def setCreationTime(self, header):
		elem = header.find(".//publicationStmt/date", self.ns)
		if elem is None or not elem.text:
			return
		self.setGlosInfo("creationTime", elem.text)

	def replaceRefLink(self, text: str) -> str:
		text = self._ref_pattern.sub('<a href="\\1">\\2</a>', text)
		return text

	def setDescription(self, header):
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
			"--------------------------------------"
		)

	def setMetadata(self, header):
		self.setWordCount(header)
		self.setGlosInfo("name", header.find(".//title", self.ns).text)

		edition = header.find(".//edition", self.ns)
		if edition is not None and edition.text:
			self.setGlosInfo("edition", edition.text)

		self.setCopyright(header)
		self.setPublisher(header)
		self.setCreationTime(header)
		self.setDescription(header)

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = ""
		self._file = None
		self._fileSize = 0
		self._wordCount = 0
		self._discoveredTags = dict()

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
		if self._file:
			self._file.close()
			self._file = None
		self._filename = ""
		self._fileSize = 0

	def open(
		self,
		filename: str,
	):
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e

		self._filename = filename
		self._file = compressionOpen(filename, mode="rb")
		self._file.seek(0, 2)
		self._fileSize = self._file.tell()
		self._file.seek(0)

		self._glos.setDefaultDefiFormat("h")

		if self._word_title:
			self._glos.setInfo("definition_has_headwords", "True")

		self._glos.setInfo("input_file_size", f"{self._fileSize}")

		context = ET.iterparse(
			self._file,
			events=("end",),
			tag=f"{tei}teiHeader",
		)
		for action, elem in context:
			self.setMetadata(elem)
			return

	def __iter__(self) -> "Iterator[BaseEntry]":
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
		context = ET.iterparse(
			self._file,
			events=("end",),
			tag=f"{tei}entry",
		)
		for action, elem in context:
			yield self.getEntryByElem(elem)
			# clean up preceding siblings to save memory
			# this reduces memory usage from ~64 MB to ~30 MB
			while elem.getprevious() is not None:
				del elem.getparent()[0]

		if self._discoveredTags:
			log.info("Found unsupported tags")
			for tag, elem in self._discoveredTags.items():
				log.info(f"{self.tostring(elem)}\n")


class Writer(object):
	compressions = stdCompressions
	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._file = None

	def finish(self):
		if self._file is None:
			return
		self._file.write("</body></text></TEI>")
		self._file.close()
		self._file = None
		self._filename = None

	def open(self, filename: str):
		self._filename = filename
		self._file = compressionOpen(filename, mode="wt", encoding="utf-8")

	def write(self) -> "Generator[None, BaseEntry, None]":
		glos = self._glos
		resources = self._resources
		filename = self._filename

		fileObj = self._file
		title = glos.getInfo("name")
		author = glos.getInfo("author")
		# didn't find any tag for author in existing glossaries
		publisher = glos.getInfo("publisher")
		copyright = glos.getInfo("copyright")
		creationTime = glos.getInfo("creationTime")

		fileObj.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
<fileDesc>
<titleStmt>
	<title>{title}</title>
	<respStmt><resp>converted with</resp><name>PyGlossary</name></respStmt>
</titleStmt>
<publicationStmt>
	<author>{author}</author>
	<publisher>{publisher}</publisher>
	<availability><p>{copyright}</p></availability>
	<date>{creationTime}</date>
</publicationStmt>
<sourceDesc><p>{filename}</p></sourceDesc>
</fileDesc>
</teiHeader>
<text><body>""")

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(f"{filename}_res")
				continue
			word = xml_escape(entry.s_word)
			defi = xml_escape(entry.defi)
			fileObj.write(f"""<entry>
<form><orth>{word}</orth></form>
<trans><tr>{defi}</tr></trans>
</entry>""")
