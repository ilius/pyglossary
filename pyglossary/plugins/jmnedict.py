# -*- coding: utf-8 -*-
import os
import re
from io import BytesIO
from typing import TYPE_CHECKING, Callable, Iterator, List

if TYPE_CHECKING:
	import lxml
	from lxml.etree import Element

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import pip
from pyglossary.glossary_type import (
	EntryType,
	GlossaryType,
)

enable = True
lname = "jmnedict"
format = "JMnedict"
description = "JMnedict"
extensions = ()
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JMdict"
website = (
	"https://www.edrdg.org/wiki/index.php/Main_Page",
	"EDRDG Wiki",
)
optionsProp = {
}


class Reader(object):
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

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
		hf: "lxml.etree.htmlfile",
		input_objects: "List[Element]",
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

	def writeTrans(
		self,
		hf: "lxml.etree.htmlfile",
		trans: "Element",
	) -> None:
		from lxml import etree as ET

		def br() -> "Element":
			return ET.Element("br")

		for elem in trans.findall("name_type"):
			if not elem.text:
				continue
			desc = elem.text
			with hf.element("i"):
				hf.write(f"{desc.capitalize()}")
			hf.write(br())

		for elem in trans.findall("trans_det"):
			if not elem.text:
				continue
			desc = elem.text
			hf.write(f"{desc}")
			hf.write(br())

		relatedWords = []
		for elem in trans.findall("xref"):
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
			kebList = []  # type: List[str]
			rebList = []  # type: List[str]
			with hf.element("div"):
				for k_ele in entry.findall("k_ele"):
					keb = k_ele.find("keb")
					if keb is None:
						continue
					kebList.append(keb.text)
					keywords.append(keb.text)
					# for elem in k_ele.findall("ke_pri"):
					# 	log.info(elem.text)

				for r_ele in entry.findall("r_ele"):
					reb = r_ele.find("reb")
					if reb is None:
						continue
					props = []
					if r_ele.find("re_nokanji") is not None:
						props.append("no kanji")
					inf = r_ele.find("re_inf")
					if inf is not None:
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
				for keb in kebList:
					for reb, _ in rebList:
						keywords.append(f"{keb}・{reb}")

				if kebList:
					with glos.titleElement(hf, kebList[0]):
						for i, keb in enumerate(kebList):
							if i > 0:
								with hf.element("font", color="red"):
									hf.write(" | ")
							hf.write(keb)
					hf.write(br())

				if rebList:
					for i, (reb, props) in enumerate(rebList):
						if i > 0:
							with hf.element("font", color="red"):
								hf.write(" | ")
						with hf.element("font", color="green"):
							hf.write(reb)
						for prop in props:
							hf.write(" ")
							with hf.element("small"):
								with hf.element("span", style=self.tagStyle):
									hf.write(prop)
					hf.write(br())

				self.makeList(
					hf,
					entry.findall("trans"),
					self.writeTrans,
				)

		defi = f.getvalue().decode("utf-8")
		byteProgress = (self._file.tell(), self._fileSize)
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
		self._file = None
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
		with compressionOpen(filename, mode="rt", encoding="utf-8") as _file:
			for line in _file:
				if "<JMdict>" in line:
					break
				header += line
		self.setMetadata(header)

		self._file = compressionOpen(filename, mode="rb")

	def __iter__(self) -> "Iterator[EntryType]":
		from lxml import etree as ET

		context = ET.iterparse(
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
