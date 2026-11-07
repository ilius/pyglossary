"""
Read JMdict Japanese-English XML lexicon files.

Parses JMdict XML for kanji, kana readings, and sense blocks. Converts each
lexical entry into one or more glossary headwords with structured HTML
definitions and part-of-speech tags.
"""

from __future__ import annotations

import os
import re
import unicodedata
from io import BytesIO
from typing import TYPE_CHECKING, cast

from pyglossary.compress import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import exc_note, pip
from pyglossary.utils.io_utils import nullBinaryIO

if TYPE_CHECKING:
	import io
	from collections.abc import Callable, Iterator

	from pyglossary.stubs.glossary_types import (
		EntryType,
		ReaderGlossaryType,
	)
	from pyglossary.stubs.lxml_types import Element, T_htmlfile

__all__ = ["Reader"]


class Reader:
	"""Read JMdict glossary files."""

	useByteProgress = True
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
		"romkan": "python-romkan-ng",
	}

	_example_padding: int = 10
	_example_color: str = ""
	# _example_color: str = "#008FE1"
	_translitation: bool = False

	tagStyle = (
		"color:white;"
		"background:green;"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
		# 0.5ex ~= 0.3em, but "ex" is recommended
	)

	gikun_key = "gikun (meaning as reading) or jukujikun (special kanji reading)"
	re_inf_mapping = {
		gikun_key: "gikun/jukujikun",
		"out-dated or obsolete kana usage": "obsolete",  # outdated/obsolete
		"word containing irregular kana usage": "irregular",
	}

	@staticmethod
	def makeList(
		hf: T_htmlfile,
		input_objects: list[Element],
		processor: Callable[[T_htmlfile, Element], None],
		single_prefix: str = "",
		skip_single: bool = True,
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
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

	@staticmethod
	def _br() -> Element:
		from lxml import etree as ET

		return ET.Element("br")

	def _writeSensePos(self, hf: T_htmlfile, sense: Element) -> None:
		for elem in sense.findall("pos"):
			if not elem.text:
				continue
			desc = elem.text
			if desc == "unclassified":
				continue
			with hf.element("i"):
				hf.write(desc.capitalize())
			hf.write(self._br())

	def _writeSenseGloss(self, hf: T_htmlfile, sense: Element) -> None:
		glossList = [elem.text.strip() for elem in sense.findall("gloss") if elem.text]
		if not glossList:
			return
		for i, gloss in enumerate(glossList):
			if i > 0:
				hf.write(", ")
			hf.write(gloss)
		hf.write(self._br())

	def _senseLinkTerms(self, sense: Element, tag: str) -> list[str]:
		terms: list[str] = []
		for elem in sense.findall(tag):
			if not elem.text:
				continue
			term = elem.text.strip()
			term = self._link_number_postfix.sub("", term)
			terms.append(term)
		return terms

	def _writeLinkWords(
		self,
		hf: T_htmlfile,
		label: str,
		terms: list[str],
		cssClass: str = "",
	) -> None:
		if not terms:
			return
		hf.write(label)
		for i, term in enumerate(terms):
			if i > 0:
				with hf.element("big"):
					hf.write(" | ")
			attrib = {"class": cssClass} if cssClass else None
			with hf.element("a", href=f"bword://{term}", attrib=attrib):
				hf.write(term)
		hf.write(self._br())

	def _writeSenseXref(self, hf: T_htmlfile, sense: Element) -> None:
		self._writeLinkWords(
			hf,
			"Related: ",
			self._senseLinkTerms(sense, "xref"),
		)

	def _writeSenseAntonym(self, hf: T_htmlfile, sense: Element) -> None:
		self._writeLinkWords(
			hf,
			"Antonym: ",
			self._senseLinkTerms(sense, "ant"),
			cssClass="antonym",
		)

	def _writeSenseField(self, hf: T_htmlfile, sense: Element) -> None:
		for i, elem in enumerate(sense.findall("field")):
			if not elem.text:
				continue
			if i > 0:
				hf.write(" ")
			desc = elem.text
			with hf.element("span", style=self.tagStyle):
				hf.write(desc)
			hf.write(self._br())

	def _writeSenseMisc(self, hf: T_htmlfile, sense: Element) -> None:
		for i, elem in enumerate(sense.findall("misc")):
			if not elem.text:
				continue
			if i > 0:
				hf.write(" ")
			desc = elem.text
			with hf.element("small"):
				with hf.element("span", style=self.tagStyle):
					hf.write(desc)
			hf.write(self._br())

	def _writeSenseExamples(self, hf: T_htmlfile, sense: Element) -> None:
		examples = sense.findall("example")
		if not examples:
			return
		with hf.element(
			"div",
			attrib={
				"class": "example",
				"style": f"padding: {self._example_padding}px 0px;",
			},
		):
			hf.write("Examples:")
			with hf.element("ul"):
				for i, elem in enumerate(examples):
					if not elem.text:
						continue
					if i > 0:
						hf.write(" ")
					# one ex_srce (id?), one ex_text, and two ex_sent tags
					textElem = elem.find("ex_text")
					if textElem is None:
						continue
					if not textElem.text:
						continue
					text = textElem.text
					sentList: list[str] = []
					for sentElem in elem.findall("ex_sent"):
						if not sentElem.text:
							continue
						sentList.append(sentElem.text)
					with hf.element("li"):
						style: dict[str, str] = {}
						if self._example_color:
							style["color"] = self._example_color
						with hf.element("font", attrib=style):
							hf.write(text)
							for sent in sentList:
								hf.write(self._br())
								hf.write(sent)

	def writeSense(
		self,
		hf: T_htmlfile,
		sense: Element,
	) -> None:
		self._writeSensePos(hf, sense)
		self._writeSenseGloss(hf, sense)
		self._writeSenseXref(hf, sense)
		self._writeSenseAntonym(hf, sense)
		self._writeSenseField(hf, sense)
		self._writeSenseMisc(hf, sense)
		self._writeSenseExamples(hf, sense)

	def _readKanjiElements(
		self,
		entry: Element,
		keywords: list[str],
	) -> tuple[list[str], list[str]]:
		translit = self._translitation
		kebList: list[str] = []
		kebDisplayList: list[str] = []
		for k_ele in entry.findall("k_ele"):
			keb = k_ele.find("keb")
			if keb is None:
				continue
			if not keb.text:
				continue
			keb_text = keb.text
			keb_text_norm = unicodedata.normalize("NFKC", keb_text)
			keywords.append(keb_text_norm)
			if keb_text != keb_text_norm:
				keywords.append(keb_text)
			kebList.append(keb_text)
			keb_display = keb_text
			if translit:
				import romkan

				t_keb = romkan.to_roma(keb_text)
				if t_keb and t_keb.isascii():
					keywords.append(t_keb)
					keb_display += f" ({t_keb})"
			kebDisplayList.append(keb_display)
			# for elem in k_ele.findall("ke_pri"):
			# 	log.info(elem.text)
		return kebList, kebDisplayList

	def _readReadingElements(
		self,
		entry: Element,
		keywords: list[str],
	) -> tuple[list[str], list[tuple[str, list[str]]]]:
		translit = self._translitation
		rebList: list[str] = []
		rebDisplayList: list[tuple[str, list[str]]] = []
		for r_ele in entry.findall("r_ele"):
			reb = r_ele.find("reb")
			if reb is None:
				continue
			if not reb.text:
				continue
			props: list[str] = []
			if r_ele.find("re_nokanji") is not None:
				props.append("no kanji")
			inf = r_ele.find("re_inf")
			if inf is not None and inf.text:
				props.append(
					self.re_inf_mapping.get(inf.text, inf.text),
				)
			keywords.append(reb.text)
			reb_text = reb.text
			rebList.append(reb_text)
			reb_display = reb_text
			if translit:
				import romkan

				t_reb = romkan.to_roma(reb.text)
				if t_reb and t_reb.isascii():
					keywords.append(t_reb)
					reb_display += f" ({t_reb})"
			rebDisplayList.append((reb_display, props))
			# for elem in r_ele.findall("re_pri"):
			# 	log.info(elem.text)
		return rebList, rebDisplayList

	def _addCombinedKeywords(
		self,
		keywords: list[str],
		kebList: list[str],
		rebList: list[str],
	) -> None:
		# this is for making internal links valid
		# this makes too many alternates!
		# but we don't seem to have a choice
		# except for scanning and indexing all words once
		# and then starting over and fixing/optimizing links
		for s_keb in kebList:
			for s_reb in rebList:
				keywords.append(f"{s_keb}・{s_reb}")  # noqa: PERF401

	def _writeKanjiDisplay(
		self,
		hf: T_htmlfile,
		kebDisplayList: list[str],
	) -> None:
		if not kebDisplayList:
			return
		with hf.element("big"):
			for i, s_keb in enumerate(kebDisplayList):
				if i > 0:
					with hf.element("font", color="red"):
						hf.write(" | ")
				hf.write(s_keb)
		hf.write(self._br())

	def _writeReadingDisplay(
		self,
		hf: T_htmlfile,
		rebDisplayList: list[tuple[str, list[str]]],
	) -> None:
		if not rebDisplayList:
			return
		for i, (s_reb, props) in enumerate(rebDisplayList):
			if i > 0:
				with hf.element("font", color="red"):
					hf.write(" | ")
			with hf.element("font", color="green"):
				hf.write(s_reb)
			for prop in props:
				hf.write(" ")
				with hf.element("small"):
					with hf.element("span", style=self.tagStyle):
						hf.write(prop)
		hf.write(self._br())

	def getEntryByElem(
		self,
		entry: Element,
	) -> EntryType:
		from lxml import etree as ET

		keywords: list[str] = []
		f = BytesIO()

		with ET.htmlfile(f, encoding="utf-8") as hf:
			hf_ = cast("T_htmlfile", hf)
			kebList, kebDisplayList = self._readKanjiElements(entry, keywords)
			rebList, rebDisplayList = self._readReadingElements(entry, keywords)
			self._addCombinedKeywords(keywords, kebList, rebList)

			with hf_.element("div"):
				self._writeKanjiDisplay(hf_, kebDisplayList)
				self._writeReadingDisplay(hf_, rebDisplayList)
				self.makeList(
					hf_,
					entry.findall("sense"),
					self.writeSense,
				)

		defi = f.getvalue().decode("utf-8")
		file = self._file
		byteProgress = (file.tell(), self._fileSize)
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="h",
			byteProgress=byteProgress,
		)

	@staticmethod
	def tostring(elem: Element) -> str:
		from lxml import etree as ET

		return (
			ET.tostring(
				elem,
				method="html",
				pretty_print=True,
			)
			.decode("utf-8")
			.strip()
		)

	def setCreationTime(self, header: str) -> None:
		m = re.search("JMdict created: ([0-9]{4}-[0-9]{2}-[0-9]{2})", header)
		if m is None:
			return
		self._glos.setInfo("creationTime", m.group(1))

	def setMetadata(self, header: str) -> None:
		# TODO: self.set_info("edition", ...)
		self.setCreationTime(header)

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._entryCount = 0
		self._filename = ""
		self._file: io.IOBase = nullBinaryIO
		self._fileSize = 0
		self._link_number_postfix = re.compile("・[0-9]+$")

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		return self._entryCount

	def close(self) -> None:
		if self._file:
			self._file.close()
			self._file = nullBinaryIO

	def open(
		self,
		filename: str,
	) -> None:
		try:
			from lxml import etree  # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install lxml` to install")
			raise

		self._filename = filename
		self._fileSize = os.path.getsize(filename)

		self._glos.sourceLangName = "Japanese"

		self._glos.setDefaultDefiFormat("h")
		self._glos.setInfo("definition_has_headwords", "True")
		self._glos.setInfo("entry_url", "https://jisho.org/search/{word}")
		# also good: f"https://sakuradict.com/search?q={{word}}"

		header = ""
		with compressionOpen(filename, mode="rt", encoding="utf-8") as text_file:
			text_file = cast("io.TextIOBase", text_file)
			for line in text_file:
				if "<JMdict>" in line:
					break
				header += line
		self.setMetadata(header)

		self._file = compressionOpen(filename, mode="rb")

	def __iter__(self) -> Iterator[EntryType]:
		from lxml import etree as ET

		context = ET.iterparse(  # noqa: PGH003
			self._file,
			events=("end",),
			tag="entry",
		)
		for _, elem_ in context:
			elem = cast("Element", elem_)
			yield self.getEntryByElem(elem)
			# clean up preceding siblings to save memory
			# this reduces memory usage from ~64 MB to ~30 MB
			parent = elem.getparent()
			if parent is None:
				continue
			while elem.getprevious() is not None:
				del parent[0]
