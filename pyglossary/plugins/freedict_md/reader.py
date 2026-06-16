# -*- coding: utf-8 -*-
from __future__ import annotations

from os.path import isfile, join
from typing import TYPE_CHECKING, cast

from pyglossary.core import log
from pyglossary.plugins.freedict.reader import Reader as FreeDictReader

from .md_emit import MdEmit

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType
	from pyglossary.lxml_types import Element, T_htmlfile


_NAMESPACE = {None: "http://www.tei-c.org/ns/1.0"}

__all__ = ["Reader"]


class Reader(FreeDictReader):
	"""Parse FreeDict TEI; definitions written as Markdown (``defiFormat`` ``m``)."""

	def getEntryByElem(  # noqa: PLR0912 — same TEI traversal as freedict.Reader; MdEmit instead of htmlfile
		self,
		entry: Element,
	) -> EntryType:
		from lxml import etree as ET

		glos = self._glos
		keywords: list[str] = []
		pron_color = self._pron_color

		if self._discover:
			for elem in entry.iter():
				if elem.tag not in self.supportedTags:
					self._discoveredTags[elem.tag] = elem

		def br() -> Element:
			return ET.Element("br")

		inflectedKeywords: list[str] = []

		for form in entry.findall(".//form", _NAMESPACE):
			inflected = form.get("type") == "infl"
			for orth in form.findall("orth", _NAMESPACE):
				if not orth.text:
					continue
				if inflected:
					inflectedKeywords.append(orth.text)
				else:
					keywords.append(orth.text)

		keywords += inflectedKeywords

		pronList = [
			pron.text.strip("/")
			for pron in entry.findall("form/pron", _NAMESPACE)
			if pron.text
		]
		senseList = entry.findall("sense", _NAMESPACE)

		em = MdEmit()
		em_hf = cast("T_htmlfile", em)
		with em.element("div"):
			if self._word_title:
				for kw in keywords:
					tag = glos.titleTag(kw)
					if tag:
						with em.element(tag):
							em.write(kw)
					else:
						em.write(kw)
					em.write(br())

			if pronList:
				for i, pron in enumerate(pronList):
					if i > 0:
						em.write(self.getCommaSep(pron))
					em.write("/")
					with em.element("font", color=pron_color):
						em.write(pron)
					em.write("/")
				em.write(br())
				em.write("\n")

			self.writeGramGroupChildren(em_hf, entry)
			self.writeSenseList(em_hf, senseList)

		defi = em.finish()

		file = self._file
		return self._glos.newEntry(
			keywords,
			defi,
			defiFormat="m",
			byteProgress=(file.tell(), self._fileSize) if self._progress else None,
		)

	def open(self, filename: str) -> None:
		super().open(filename)
		self._glos.setDefaultDefiFormat("m")

	def countResourceFiles(self) -> int:
		return 0

	def loadInclude(self, elem: Element) -> Reader | None:
		href = elem.attrib.get("href")
		if not href:
			log.error(f"empty href in {elem}")
			return None
		filename = join(self._dirname, href)
		if not isfile(filename):
			log.error(f"no such file {filename!r} from {elem}")
			return None
		reader = type(self)(self._glos)
		self._copyOptionsTo(reader)
		reader.open(filename)
		return reader
