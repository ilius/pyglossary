# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.xml_utils import xml_escape
from typing import List, Union, Callable
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
depends = {
	"lxml": "lxml",
}

# https://freedict.org/
# https://github.com/freedict/fd-dictionaries/wiki

tei = "{http://www.tei-c.org/ns/1.0}"


class Reader(object):
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

	def make_list(
		self,
		hf: "lxml.etree.htmlfile",
		input_elements: "List[lxml.etree.Element]",
		processor: Callable,
		single_prefix=None,
		skip_single=True
	):
		""" Wrap elements into <ol> if more than one element """
		if len(input_elements) == 0:
			return

		if len(input_elements) == 1:
			hf.write(single_prefix)
			processor(hf, input_elements[0])
			return

		with hf.element("ol"):
			for el in input_elements:
				with hf.element("li"):
					processor(hf, el)

	def process_sense(
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

		self.make_list(
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
		keywords = []
		f = BytesIO()

		if self._discover:
			for elem in entry.iter():
				if elem.tag not in self.supportedTags:
					self._discoveredTags[elem.tag] = elem

		def br():
			return ET.Element("br")

		with ET.htmlfile(f) as hf:
			with hf.element("div"):
				for form in entry.findall("form/orth", self.ns):
					keywords.append(form.text)

				if self._keywords_header:
					for keyword in keywords:
						with hf.element("b"):
							hf.write(keyword)
						hf.write(br())

				# TODO: "form/usg"
				# <usg type="geo">Brit</usg>
				# <usg type="geo">US</usg>
				# <usg type="hint">...</usg>

				gramGrpList = entry.findall("gramGrp", self.ns)
				if gramGrpList:
					for gramGrp in gramGrpList:
						parts = []
						for child in gramGrp.iterchildren():
							text = self.normalizeGramGrpChild(child)
							if text:
								parts.append(text)
						with hf.element("i"):
							hf.write(", ".join(parts))
						hf.write(br())

				pronList = entry.findall("form/pron", self.ns)
				if pronList:
					for i, pron in enumerate(pronList):
						if i > 0:
							hf.write(", ")
						with hf.element("font", color="green"):
							hf.write(f"/{pron.text}/")
					hf.write(br())
					hf.write("\n")

				self.make_list(
					hf,
					entry.findall("sense", self.ns),
					self.process_sense,
				)

		defi = f.getvalue().decode("utf-8")
		return self._glos.newEntry(keywords, defi, defiFormat="h")

	def set_word_count(self, header):
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

	def strip_tag_p_elem(self, elem: "lxml.etree.Element") -> str:
		text = self.tostring(elem)
		text = self._p_pattern.sub("\\2", text)
		return text

	def strip_tag_p(self, elems: List["lxml.etree.Element"]) -> str:
		lines = []
		for elem in elems:
			for line in self.strip_tag_p_elem(elem).split("\n"):
				line = line.strip()
				if not line:
					continue
				lines.append(line)
		return "\n".join(lines)

	def set_info(self, key: str, value: str) -> None:
		self._glos.setInfo(key, html.unescape(value))

	def set_copyright(self, header):
		elems = header.findall(".//availability//p", self.ns)
		if not elems:
			log.warn("did not find copyright")
			return
		copyright = self.strip_tag_p(elems)
		copyright = self.replace_ref(copyright)
		self.set_info("copyright", copyright)
		log.info(f"Copyright: {copyright!r}")

	def set_publisher(self, header):
		elem = header.find(".//publisher", self.ns)
		if elem is None:
			log.warn("did not find publisher")
			return
		self.set_info("publisher", elem.text)

	def set_publication_date(self, header):
		elem = header.find(".//publicationStmt/date", self.ns)
		if elem is None:
			return
		self.set_info("creationTime", elem.text)

	def replace_ref(self, text: str) -> str:
		text = self._ref_pattern.sub('<a href="\\1">\\2</a>', text)
		return text

	def set_description(self, header):
		elems = []
		for tag in ("sourceDesc", "projectDesc"):
			elems += header.findall(f".//{tag}//p", self.ns)
		desc = self.strip_tag_p(elems)
		if not desc:
			return

		website_list = []
		for match in self._website_pattern.findall(desc):
			if not match[1]:
				continue
			website_list.append(match[1])
		if website_list:
			website = " | ".join(website_list)
			self.set_info("website", website)
			desc = self._website_pattern.sub("", desc).strip()
			log.info(f"Website: {website}")

		desc = self.replace_ref(desc)
		self.set_info("description", desc)
		log.info(
			"------------ Description: ------------\n"
			f"{desc}\n"
			"--------------------------------------"
		)

	def set_metadata(self, header):
		self.set_word_count(header)
		self.set_info("name", header.find(".//title", self.ns).text)
		self.set_info("edition", header.find(".//edition", self.ns).text)

		self.set_copyright(header)
		self.set_publisher(header)
		self.set_publication_date(header)
		self.set_description(header)

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._wordCount = 0
		self._discover = False
		self._discoveredTags = dict()
		self._keywords_header = False

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
		pass

	def open(
		self,
		filename: str,
		discover: bool = False,
		keywords_header: bool = False,
	):
		try:
			from lxml import etree as ET
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e

		self._filename = filename
		self._discover = discover
		self._keywords_header = keywords_header

		self._glos.setDefaultDefiFormat("h")

		context = ET.iterparse(
			filename,
			events=("end",),
			tag=f"{tei}teiHeader",
		)
		for action, elem in context:
			self.set_metadata(elem)
			return

	def __iter__(self) -> Iterator[BaseEntry]:
		from lxml import etree as ET
		context = ET.iterparse(
			self._filename,
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
			log.info("\nFound unsupported tags")
			for tag, elem in self._discoveredTags.items():
				log.info(f"\n{self.tostring(elem)}\n")


class Writer(object):
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def write(
		self,
		filename: str,
		resources: bool = True,
	) -> Generator[None, "BaseEntry", None]:
		glos = self._glos
		fileObj = open(filename, "w", encoding="utf-8")
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
		fileObj.write("</body></text></TEI>")
		fileObj.close()
