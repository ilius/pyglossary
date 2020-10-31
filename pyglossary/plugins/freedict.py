# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.xml_utils import xml_escape
from pyglossary.html_utils import unescape_unicode
from io import BytesIO
import re
import html

enable = True
format = "FreeDict"
description = "FreeDict (tei)"
extensions = (".tei",)
singleFile = True
optionsProp = {
	"resources": BoolOption(),
	"discover": BoolOption(),
	"keywords_header": BoolOption(
		comment="repeat keywords on top of definition"
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
	_keywords_header: bool = False

	ns = {
		None: "http://www.tei-c.org/ns/1.0",
	}

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

	def makeList(
		self,
		hf: "lxml.etree.htmlfile",
		input_objects: "List[Any]",
		processor: "Callable",
		single_prefix=None,
		skip_single=True
	):
		""" Wrap elements into <ol> if more than one element """

		if not input_objects:
			return

		if skip_single and len(input_objects) == 1:
			hf.write(single_prefix)
			processor(hf, input_objects[0])
			return

		with hf.element("ol"):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el)

	def writeSense(
		self,
		hf: "lxml.etree.htmlfile",
		sense: "lxml.etree.Element",
	):
		# translations
		hf.write(", ".join(
			el.text
			for el in sense.findall("cit/quote", self.ns)
			if el.text is not None
		))

		self.makeList(
			hf,
			sense.findall("sense/def", self.ns),
			lambda hf, el: hf.write(el.text),
			single_prefix=" — ",
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
			return f"number: {text}"
		log.info(f"unrecognize GramGrp child: {elem}")
		return ""

	def getEntryByElem(self, entry: "lxml.etree.Element") -> "BaseEntry":
		from lxml import etree as ET
		glos = self._glos
		keywords = []
		f = BytesIO()

		if self._discover:
			for elem in entry.iter():
				if elem.tag not in self.supportedTags:
					self._discoveredTags[elem.tag] = elem

		def br():
			return ET.Element("br")

		for form in entry.findall("form/orth", self.ns):
			if form.getparent().get("type"):
				# only use normal form, not inflected one, here
				continue
			keywords.append(form.text)

		# Add keywords for inflected forms
		for orth in entry.findall('.//form[@type="infl"]/orth', self.ns):
			if not orth.text:
				continue
			keywords.append(orth.text)

		gramList = []  # type: List[str]
		for gramGrp in entry.findall("gramGrp", self.ns):
			parts = []
			for child in gramGrp.iterchildren():
				text = self.normalizeGramGrpChild(child)
				if text:
					parts.append(text)
			if parts:
				gramList.append(", ".join(parts))

		pronList = entry.findall("form/pron", self.ns)
		senseList = entry.findall("sense", self.ns)

		with ET.htmlfile(f) as hf:
			with hf.element("div"):
				if self._keywords_header:
					for keyword in keywords:
						with glos.titleElement(hf, keyword):
							hf.write(keyword)
						hf.write(br())

				# TODO: "form/usg"
				# <usg type="geo">Brit</usg>
				# <usg type="geo">US</usg>
				# <usg type="hint">...</usg>

				for text in gramList:
					with hf.element("i"):
						hf.write(text)
					hf.write(br())

				if pronList:
					for i, pron in enumerate(pronList):
						if i > 0:
							hf.write(", ")
						with hf.element("font", color="green"):
							hf.write(f"/{pron.text}/")
					hf.write(br())
					hf.write("\n")

				self.makeList(
					hf,
					senseList,
					self.writeSense,
				)

		defi = unescape_unicode(f.getvalue().decode("utf-8"))
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
		log.info(f"Copyright: {copyright!r}")

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
			log.info(f"Website: {website}")

		desc = self.replaceRefLink(desc)
		self.setGlosInfo("description", desc)
		log.info(
			"------------ Description: ------------\n"
			f"{desc}\n"
			"--------------------------------------"
		)

	def setMetadata(self, header):
		self.setWordCount(header)
		self.setGlosInfo("name", header.find(".//title", self.ns).text)

		edition = header.find(".//edition", self.ns)
		if edition and edition.text:
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
