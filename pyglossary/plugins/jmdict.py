# -*- coding: utf-8 -*-

import os
import re
from io import BytesIO
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	import io
	from typing import Callable, Iterator

	from lxml.etree import _Element as Element

	from pyglossary.lxml_type import T_htmlfile

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import pip
from pyglossary.glossary_type import (
	EntryType,
	GlossaryType,
)
from pyglossary.option import (
	IntOption,
	Option,
	StrOption,
)

enable = True
lname = "jmdict"
format = "JMDict"
description = "JMDict"
extensions = ()
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JMdict"
website = (
	"https://www.edrdg.org/jmdict/j_jmdict.html",
	"The JMDict Project",
)
optionsProp: "dict[str, Option]" = {
	"example_color": StrOption(
		comment="Examples color",
	),
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
	),
}


class Reader(object):
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_example_padding: int = 10
	_example_color: str = ""
	# _example_color: str = "#008FE1"

	tagStyle = (
		"color:white;"
		"background:green;"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
		# 0.5ex ~= 0.3em, but "ex" is recommended
	)

	re_inf_mapping = {
		"gikun (meaning as reading) or jukujikun (special kanji reading)":
			"gikun/jukujikun",
		"out-dated or obsolete kana usage": "obsolete",  # outdated/obsolete
		"word containing irregular kana usage": "irregular",
	}

	def makeList(
		self,
		hf: "T_htmlfile",
		input_objects: "list[Element]",
		processor: "Callable",
		single_prefix: str = "",
		skip_single: bool = True,
	) -> None:
		""" Wrap elements into <ol> if more than one element """
		if len(input_objects) == 0:
			return

		if len(input_objects) == 1:
			hf.write(single_prefix)
			processor(hf, input_objects[0])
			return

		with hf.element("ol"):
			for el in input_objects:
				with hf.element("li"):
					processor(hf, el)

	def writeSense(
		self,
		hf: "T_htmlfile",
		sense: "Element",
	) -> None:
		from lxml import etree as ET

		def br() -> "Element":
			return ET.Element("br")

		for elem in sense.findall("pos"):
			if not elem.text:
				continue
			desc = elem.text
			if desc == "unclassified":
				continue
			with hf.element("i"):
				hf.write(f"{desc.capitalize()}")
			hf.write(br())

		glossList = [
			elem.text.strip()
			for elem in sense.findall("gloss")
			if elem.text
		]
		if glossList:
			for i, gloss in enumerate(glossList):
				if i > 0:
					hf.write(", ")
				hf.write(gloss)
			hf.write(br())

		relatedWords = []
		for elem in sense.findall("xref"):
			if not elem.text:
				continue
			word = elem.text.strip()
			word = self._link_number_postfix.sub("", word)
			relatedWords.append(word)

		if relatedWords:
			hf.write("Related: ")
			for i, word in enumerate(relatedWords):
				if i > 0:
					with hf.element("big"):
						hf.write(" | ")
				with hf.element("a", href=f"bword://{word}"):
					hf.write(word)
			hf.write(br())

		antonymWords = []
		for elem in sense.findall("ant"):
			if not elem.text:
				continue
			word = elem.text.strip()
			word = self._link_number_postfix.sub("", word)
			antonymWords.append(word)
		if antonymWords:
			hf.write("Antonym: ")
			for i, word in enumerate(antonymWords):
				if i > 0:
					with hf.element("big"):
						hf.write(" | ")
				with hf.element("a", href=f"bword://{word}"):
					hf.write(word)
			hf.write(br())

		for i, elem in enumerate(sense.findall("field")):
			if not elem.text:
				continue
			if i > 0:
				hf.write(" ")
			desc = elem.text
			with hf.element("span", style=self.tagStyle):
				hf.write(desc)
			hf.write(br())

		for i, elem in enumerate(sense.findall("misc")):
			if not elem.text:
				continue
			if i > 0:
				hf.write(" ")
			desc = elem.text
			with hf.element("small"):
				with hf.element("span", style=self.tagStyle):
					hf.write(desc)
			hf.write(br())

		examples = sense.findall("example")
		if examples:
			with hf.element("div", attrib={
				"class": "example",
				"style": f"padding: {self._example_padding}px 0px;",
			}):
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
						sentList: "list[str]" = []
						for sentElem in elem.findall("ex_sent"):
							if not sentElem.text:
								continue
							sentList.append(sentElem.text)
						with hf.element("li"):
							style = {}
							if self._example_color:
								style["color"] = self._example_color
							with hf.element("font", attrib=style):
								hf.write(text)
								for sent in sentList:
									hf.write(br())
									hf.write(sent)

	def getEntryByElem(
		self,
		entry: "Element",
	) -> "EntryType":
		from lxml import etree as ET
		glos = self._glos
		keywords = []
		f = BytesIO()

		def br() -> "Element":
			return ET.Element("br")

		with ET.htmlfile(f, encoding="utf-8") as hf:
			kebList: "list[str]" = []
			rebList: "list[tuple[str, list[str]]]" = []
			with hf.element("div"):
				for k_ele in entry.findall("k_ele"):
					keb = k_ele.find("keb")
					if keb is None:
						continue
					if not keb.text:
						continue
					kebList.append(keb.text)
					keywords.append(keb.text)
					# for elem in k_ele.findall("ke_pri"):
					# 	log.info(elem.text)

				for r_ele in entry.findall("r_ele"):
					reb = r_ele.find("reb")
					if reb is None:
						continue
					if not reb.text:
						continue
					props = []
					if r_ele.find("re_nokanji") is not None:
						props.append("no kanji")
					inf = r_ele.find("re_inf")
					if inf is not None and inf.text:
						props.append(
							self.re_inf_mapping.get(inf.text, inf.text),
						)
					rebList.append((reb.text, props))
					keywords.append(reb.text)
					# for elem in r_ele.findall("re_pri"):
					# 	log.info(elem.text)

				# this is for making internal links valid
				# this makes too many alternates!
				# but we don't seem to have a choice
				# except for scanning and indexing all words once
				# and then starting over and fixing/optimizing links
				for s_keb in kebList:
					for s_reb, _ in rebList:
						keywords.append(f"{s_keb}・{s_reb}")

				if kebList:
					with hf.element(glos.titleTag(kebList[0])):
						for i, s_keb in enumerate(kebList):
							if i > 0:
								with hf.element("font", color="red"):
									hf.write(" | ")
							hf.write(s_keb)
					hf.write(br())

				if rebList:
					for i, (s_reb, props) in enumerate(rebList):
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
					hf.write(br())

				_hf = cast("T_htmlfile", hf)
				self.makeList(
					_hf,
					entry.findall("sense"),
					self.writeSense,
				)

		defi = f.getvalue().decode("utf-8")
		_file = self._file
		if _file is None:
			raise RuntimeError("_file is None")
		byteProgress = (_file.tell(), self._fileSize)
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="h",
			byteProgress=byteProgress,
		)

	def tostring(
		self,
		elem: "Element",
	) -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def setCreationTime(self, header: str) -> None:
		m = re.search("JMdict created: ([0-9]{4}-[0-9]{2}-[0-9]{2})", header)
		if m is None:
			return
		self._glos.setInfo("creationTime", m.group(1))

	def setMetadata(self, header: str) -> None:
		# TODO: self.set_info("edition", ...)
		self.setCreationTime(header)

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._wordCount = 0
		self._filename = ""
		self._file: "io.IOBase | None" = None
		self._fileSize = 0
		self._link_number_postfix = re.compile("・[0-9]+$")

	def __len__(self) -> int:
		return self._wordCount

	def close(self) -> None:
		if self._file:
			self._file.close()
			self._file = None

	def open(
		self,
		filename: str,
	) -> None:
		try:
			from lxml import etree as ET  # noqa: F401
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e

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

	def __iter__(self) -> "Iterator[EntryType]":
		from lxml import etree as ET

		context = ET.iterparse(  # type: ignore # noqa: PGH003
			self._file,
			events=("end",),
			tag="entry",
		)
		for _, elem in context:
			yield self.getEntryByElem(elem)
			# clean up preceding siblings to save memory
			# this reduces memory usage from ~64 MB to ~30 MB
			while elem.getprevious() is not None:
				del elem.getparent()[0]
