"""
Read FreeDict TEI XML dictionaries.

Parses TEI ``<entry>`` elements (including XInclude), resolves FreeDict
translation and orthography modules, detects source/target languages from
``xml:lang``, and builds HTML definitions. Supports bzip2/gzip-compressed
``.dct`` files.
"""

from __future__ import annotations

# mypy: ignore-errors
import re
from dataclasses import dataclass
from io import BytesIO
from os.path import dirname, isfile, join, realpath
from typing import TYPE_CHECKING, cast

from pyglossary.compress import compressionOpen, stdCompressions
from pyglossary.core import exc_note, log, pip
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText
from pyglossary.utils.html_utils import unescape_unicode
from pyglossary.utils.io_utils import nullBinaryIO

from .utils import XMLLANG, ReaderUtils

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator
	from io import IOBase

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType
	from pyglossary.stubs.lxml_types import Element, T_htmlfile


__all__ = ["Reader"]


_TEI = "{http://www.tei-c.org/ns/1.0}"
_ENTRY = f"{_TEI}entry"
_INCLUDE = "{http://www.w3.org/2001/XInclude}include"
_NAMESPACE = {None: "http://www.tei-c.org/ns/1.0"}
_whitespaceRun = re.compile(r"\s+")


def _elementText(elem: Element) -> str:
	"""Return all text inside an element, including nested markup."""
	return "".join(elem.itertext()).strip()


@dataclass(slots=True)
class _ParsedSense:
	"""Internal parsed sense."""

	transCits: list[Element]
	defs: list[Element]
	grams: list[Element]
	notes: list[Element]
	refs: list[Element]
	usages: list[Element]
	labels: list[Element]
	xrList: list[Element]
	exampleCits: list[Element]
	langs: list[Element]


class Reader(ReaderUtils):
	"""Read Freedict glossary files."""

	useByteProgress = True
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_auto_rtl: bool = True
	_auto_comma: bool = True
	_comma: str = ", "
	_word_title: bool = False
	_pron_color: str = "gray"
	_gram_color: str = "green"
	_usage_color: str = "green"
	_label_color: str = "darkblue"
	_example_padding: int = 10

	def _copyOptionsTo(self, other: Reader) -> None:
		other._auto_rtl = self._auto_rtl
		other._auto_comma = self._auto_comma
		other._comma = self._comma
		other._word_title = self._word_title
		other._pron_color = self._pron_color
		other._gram_color = self._gram_color
		other._usage_color = self._usage_color
		other._label_color = self._label_color
		other._example_padding = self._example_padding

	gramClass = "grammar"
	tagStyle = (
		"color:white;"
		"background:{};"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
	)
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
	}
	numberMapping: dict[str, str] = {
		"pl": "plural",
		"sg": "singular",
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
		"gloss",
		"idarex",
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
			if not ref.text:
				# no target to link to and no text to show
				log.warning("ref without target or text, skipped")
				return
			target = f"bword://{ref.text}"
		with hf.element("a", href=target, attrib=attrib):
			hf.write(ref.text or "")

	def writeQuote(
		self,
		hf: T_htmlfile,
		elem: Element,
		prefix: list[Element] | None = None,
	) -> None:
		self.writeWithDirection(hf, elem, "div", prefix=prefix)

	def writeTransCit(
		self,
		hf: T_htmlfile,
		elem: Element,
		prefix: list[Element] | None = None,
	) -> None:
		from copy import deepcopy

		from lxml import etree as ET

		children = elem.xpath("child::node()")
		if not children:
			return
		assert isinstance(children, list), f"{children=}"

		# The writers below (writeSense, writeGramGroups, writeUsageTag, ...)
		# only read from a <sense> tree, but the grammar, usage and note
		# children of a translation <cit> sit next to its quotes. Copying
		# them into a synthetic <sense> lets writeSense render them with
		# the same code path as real senses, without duplicating that logic.
		# The source <cit> is left unchanged, so the same entry can be
		# rendered again.
		sense = ET.Element(f"{_TEI}sense")
		gramGrp: Element | None = None

		def copyToSense(parent: Element, child: Element) -> None:
			# Copy instead of move: moving would detach the child from the
			# source <cit>, so a second render of the same entry would lose
			# it. The copy has no tail: collectCit already collects the tail
			# text as loose text (through the xpath "child::node()" snapshot),
			# so keeping it here would render that text twice.
			copied = deepcopy(child)
			copied.tail = None
			parent.append(copied)

		def appendGramChild(child: Element) -> None:
			nonlocal gramGrp
			# Bare <pos>/<gen>/<number>/<num>/<subc> inside a translation <cit>
			# are not wrapped in <gramGrp> in the TEI. writeGramGroups only
			# reads <gramGrp> children, so create one in the synthetic sense
			# and group these elements under it.
			if gramGrp is None:
				gramGrp = ET.SubElement(sense, f"{_TEI}gramGrp")
			copyToSense(gramGrp, child)

		def newTextBlock(text: str, cit: Element) -> Element:
			# Loose text has no element of its own, but the block writers
			# (writeQuote -> writeWithDirection) need an Element. Wrap the
			# text in a new <quote> that copies the <cit> attributes, so
			# xml:lang (lang/dir) and type (class) are applied to it as they
			# are to real quotes. The source tree is not modified here.
			quote = ET.Element(f"{_TEI}quote", attrib=dict(cit.attrib))
			quote.text = text
			return quote

		def collectCit(  # noqa: PLR0912
			cit: Element,
		) -> list[tuple[Element, list[Element]]]:
			"""
			Return render blocks (quote element, tags) for this <cit>.

			Tags are <usg> and <lbl> elements of this <cit>. They are rendered
			inline before the first block it produces, so they stay next to
			the content they describe. Nested <cit> elements are collected
			separately, so their tags stay with their own content.
			"""
			blocks: list[tuple[Element, list[Element]]] = []
			# <usg> and <lbl> are both rendered as bracketed tags before the
			# content, in document order. <usg> is kept here (not moved into
			# the synthetic sense) because it gives the domain/context of the
			# translation, e.g. "[archaic] word", so it must come first.
			tags: list[Element] = []
			pendingText: list[str] = []

			def flushText() -> None:
				if pendingText:
					blocks.append((newTextBlock(" ".join(pendingText), cit), []))
					pendingText.clear()

			for child in cit.xpath("child::node()"):
				if isinstance(child, str):
					text = child.strip()
					if text:
						log.warning(f"text directly inside <cit>: {text}")
						pendingText.append(text)
					continue

				if child.__class__.__name__ == "_Comment":
					continue

				if child.tag == f"{_TEI}quote":
					flushText()
					blocks.append((child, []))
					continue

				if child.tag in {f"{_TEI}gramGrp", f"{_TEI}note"}:
					copyToSense(sense, child)
					continue

				if child.tag in {f"{_TEI}usg", f"{_TEI}lbl"}:
					if _elementText(child):
						tags.append(child)
					continue

				if child.tag in {
					f"{_TEI}pos",
					f"{_TEI}gen",
					f"{_TEI}number",
					f"{_TEI}num",
					f"{_TEI}subc",
				}:
					appendGramChild(child)
					continue

				if child.tag == f"{_TEI}cit":
					typ = child.attrib.get("type", "trans")
					if typ in {"abbrev", "abbreviation"}:
						# An abbreviation <cit> only carries <orth> text that
						# should be shown as a label. Create a detached <lbl>
						# (not added to the tree) because writeLabelTag takes
						# an Element.
						for orth in child.findall("orth", _NAMESPACE):
							text = _elementText(orth)
							if text:
								lbl = ET.Element(f"{_TEI}lbl")
								lbl.text = text
								tags.append(lbl)
						continue
					# A nested <cit> is collected into its own blocks, so its
					# quotes and tags stay with its own content.
					flushText()
					blocks += collectCit(child)
					continue

				log.warning(
					f"unknown tag {child.tag!r} inside translation <cit>"
					f": {self.tostring(child)}",
				)
				# Keep the text of an unknown element as a <note> in the
				# synthetic sense instead of dropping it.
				text = _elementText(child)
				if text:
					note = ET.SubElement(sense, f"{_TEI}note")
					note.text = text

			flushText()
			if tags:
				if not blocks:
					blocks.append((newTextBlock("", cit), []))
				quote, prefixOfFirst = blocks[0]
				blocks[0] = (quote, tags + prefixOfFirst)
			return blocks

		blocks = collectCit(elem)

		if prefix:
			if blocks:
				quote, prefixOfFirst = blocks[0]
				blocks[0] = (quote, prefix + prefixOfFirst)
			else:
				self.writeInlineTags(hf, prefix)

		if len(blocks) == 1:
			self.writeQuote(hf, blocks[0][0], blocks[0][1])
		elif blocks:
			with hf.element("ol"):
				for quote, blockPrefix in blocks:
					with hf.element("li"):
						self.writeQuote(hf, quote, blockPrefix)

		if next(sense.iterchildren(), False) is not None:
			self.writeSense(hf, sense)

	def iterDefPieces(self, node: Element) -> Iterator[str | Element]:
		"""Yield the text and <ref> pieces of a <def>, recursing into other elements."""
		for child in node.xpath("child::node()"):
			if isinstance(child, str):
				yield child
				continue
			if not isinstance(child.tag, str):
				# comment or processing instruction
				continue
			if child.tag == f"{_TEI}ref":
				if child.text:
					yield child
				else:
					log.warning(f"ref without text: {self.tostring(child)}")
				continue
			yield from self.iterDefPieces(child)

	def getDefPieces(self, elem: Element) -> list[str | Element]:
		"""
		Return the inline pieces of a <def>, ready to write.

		Adjacent text is merged before whitespace is collapsed, so spacing
		around skipped comments and inline elements is kept. Leading and
		trailing whitespace of the whole definition is removed.
		"""
		merged: list[str | Element] = []
		for piece in self.iterDefPieces(elem):
			if isinstance(piece, str) and merged and isinstance(merged[-1], str):
				merged[-1] += piece
			else:
				merged.append(piece)

		for i, piece in enumerate(merged):
			if isinstance(piece, str):
				merged[i] = re.sub(r"\s+", " ", piece)
		if merged and isinstance(merged[0], str):
			merged[0] = merged[0].lstrip()
		if merged and isinstance(merged[-1], str):
			merged[-1] = merged[-1].rstrip()

		return [piece for piece in merged if not (isinstance(piece, str) and not piece)]

	def writeDef(
		self,
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		# <def> has phrase-level content (TEI): text, <ref> links and inline
		# elements such as <hi>. All of it stays inline, so no separator is
		# inserted between pieces.
		for piece in self.getDefPieces(elem):
			if isinstance(piece, str):
				hf.write(piece)
			else:
				self.writeRef(hf, piece)

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
		prefix: list[Element] | None = None,
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
			# Render the prefix inside the block element so it shares the
			# line with the content, rather than appearing on its own line.
			if prefix:
				self.writeInlineTags(hf, prefix)
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
			if child.tag == f"{_TEI}ref":
				self.writeRef(hf, child)
				continue
			if child.tag == f"{_TEI}br":
				hf.write(ET.Element("br"))
				continue
			if child.tag == f"{_TEI}p":
				# map xml:lang to lang (and dir), like writeWithDirection does;
				# passing the raw attribute would emit an ns0:lang attribute
				attrib: dict[str, str] = dict(child.attrib)
				self.setAttribLangDir(attrib)
				with hf.element("p", attrib=attrib):
					self.writeRichText(hf, child)
					continue
			if child.tag == f"{_TEI}div":
				self.writeWithDirection(hf, child, "div")
				continue
			if child.tag == f"{_TEI}span":
				self.writeWithDirection(hf, child, "span")
				continue

			self.writeRichText(hf, child)

	def writeNote(
		self,
		hf: T_htmlfile,
		note: Element,
	) -> None:
		self.writeRichText(hf, note)

	def writeTag(
		self,
		hf: T_htmlfile,
		elem: Element,
		color: str,
	) -> None:
		style = self.tagStyle.format(color or "transparent")
		content = self.normalizeTagContent(elem)
		with hf.element("span", attrib={"class": "tag", "style": style}):
			hf.write("[")
			self.writeRichText(hf, content)
			hf.write("]")

	@staticmethod
	def normalizeTagContent(elem: Element) -> Element:
		"""
		Return a copy of a <usg> or <lbl> element for writing inside a tag.

		Line breaks and indentation in the source are not meaningful, so runs
		of whitespace are collapsed to one space and the content is trimmed at
		both ends. The copy is used so the source tree is not modified.
		"""
		from copy import deepcopy

		copied = deepcopy(elem)
		copied.tail = None

		# text slots (element .text and child .tail) in document order, so a
		# space at the end of one slot is seen when the next slot starts
		slots: list[tuple[Element, str]] = []

		def collect(node: Element) -> None:
			if not isinstance(node.tag, str):
				return  # comments are not written
			slots.append((node, "text"))
			for child in node:
				collect(child)
				slots.append((child, "tail"))

		collect(copied)

		atSpace = True  # True at the start, so leading whitespace is dropped
		for node, attr in slots:
			text = getattr(node, attr)
			if not text:
				continue
			text = _whitespaceRun.sub(" ", text)
			if atSpace:
				text = text.lstrip(" ")
			if text:
				atSpace = text.endswith(" ")
			setattr(node, attr, text or None)

		# drop trailing whitespace, continuing backwards over whitespace-only slots
		for node, attr in reversed(slots):
			text = getattr(node, attr)
			if not text:
				continue
			text = text.rstrip(" ")
			setattr(node, attr, text or None)
			if text:
				break
		return copied

	def writeUsageTag(
		self,
		hf: T_htmlfile,
		usg: Element,
	) -> None:
		self.writeTag(hf, usg, self._usage_color)

	def writeLabelTag(
		self,
		hf: T_htmlfile,
		lbl: Element,
	) -> None:
		self.writeTag(hf, lbl, self._label_color)

	def writeTags(
		self,
		hf: T_htmlfile,
		elems: list[Element],
		writer: Callable[[T_htmlfile, Element], None],
	) -> None:
		for i, elem in enumerate(elems):
			if i > 0:
				hf.write(" ")
			writer(hf, elem)
		hf.write(" ")

	def writeUsageTags(
		self,
		hf: T_htmlfile,
		usages: list[Element],
	) -> None:
		self.writeTags(hf, usages, self.writeUsageTag)

	def writeLabelTags(
		self,
		hf: T_htmlfile,
		labels: list[Element],
	) -> None:
		self.writeTags(hf, labels, self.writeLabelTag)

	def writeInlineTags(
		self,
		hf: T_htmlfile,
		elems: list[Element],
	) -> None:
		"""Write a mix of <usg> and <lbl> elements, each with its own color."""

		def writeInline(hf_: T_htmlfile, elem: Element) -> None:
			if elem.tag == f"{_TEI}lbl":
				self.writeLabelTag(hf_, elem)
			else:
				self.writeUsageTag(hf_, elem)

		self.writeTags(hf, elems, writeInline)

	def parseSenseSense(  # noqa: PLR0912
		self,
		sense: Element,
	) -> _ParsedSense:
		# this <sense> element can be 1st-level (directly under <entry>)
		# or 2nd-level
		transCits: list[Element] = []
		defs: list[Element] = []
		grams: list[Element] = []
		notes: list[Element] = []
		refs: list[Element] = []
		usages: list[Element] = []
		labels: list[Element] = []
		xrList: list[Element] = []
		exampleCits: list[Element] = []
		langs: list[Element] = []
		for child in sense.iterchildren():
			if not isinstance(child.tag, str):
				# comment or processing instruction
				continue

			if child.tag == f"{_TEI}cit":
				typ = child.attrib.get("type", "trans")
				if typ == "trans":
					transCits.append(child)
				elif typ == "example":
					exampleCits.append(child)
				elif typ == "idiom":
					transCits.append(child)  # FIXME
				elif typ in {"abbrev", "abbreviation"}:
					notes.append(child)
				else:
					log.warning(f"unknown cit type: {self.tostring(child)}")
					notes.append(child)
				continue

			if child.tag == f"{_TEI}def":
				defs.append(child)
				continue

			if child.tag == f"{_TEI}note":
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

			if child.tag == f"{_TEI}ref":
				if not child.get("target") and not child.text:
					log.warning("empty <ref> in <sense> without target, skipped")
					continue
				refs.append(child)
				continue

			if child.tag == f"{_TEI}usg":
				# check the full text, including nested markup such as <lang>
				if not _elementText(child):
					log.warning(f"empty usg: {self.tostring(child)}")
					continue
				usages.append(child)
				continue

			if child.tag == f"{_TEI}lbl":
				if not _elementText(child):
					continue
				labels.append(child)
				continue

			if child.tag == f"{_TEI}lang":
				langs.append(child)
				continue

			if child.tag in {f"{_TEI}sense", f"{_TEI}gramGrp"}:
				continue

			if child.tag == f"{_TEI}xr":
				xrList.append(child)
				continue

			if child.tag == f"{_TEI}form":
				continue

			log.warning(f"unknown tag {child.tag} in <sense>: {self.tostring(child)}")

		return _ParsedSense(
			transCits=transCits,
			defs=defs,
			grams=grams,
			notes=notes,
			refs=refs,
			usages=usages,
			labels=labels,
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
		usages = list(ps.usages)
		labels = list(ps.labels)

		# First-level senses already have their <gramGrp> rendered by
		# writeSense; nested senses need it rendered here.
		parent = sense.getparent()
		if parent is not None and parent.tag != _ENTRY:
			self.writeGramGroupChildren(hf, sense)

		def writeUsages() -> None:
			if usages:
				self.writeUsageTags(hf, usages)
				usages.clear()
			if labels:
				self.writeLabelTags(hf, labels)
				labels.clear()

		for child in ps.langs:
			self.writeLangTag(hf, child)

		if ps.defs:
			writeUsages()
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
				writeUsages()
				for i, gram in enumerate(ps.grams):
					text = _elementText(gram)
					if i > 0:
						hf.write(self.getCommaSep(text))
					with hf.element("font", attrib=attrib):
						hf.write(text)
		if ps.notes:
			writeUsages()
		self.makeList(
			hf,
			ps.notes,
			self.writeNote,
			single_prefix="",
		)
		if ps.transCits:

			def writeFirstTransCit(hf_: T_htmlfile, elem: Element) -> None:
				prefix = list(usages)
				usages.clear()
				self.writeTransCit(hf_, elem, prefix)

			self.makeList(
				hf,
				ps.transCits,
				writeFirstTransCit,
				single_prefix="",
			)
		writeUsages()
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

		def writeExampleCit(citElem: Element) -> None:
			# <usg> and <lbl> give the domain/context of the example, so they
			# are written before its quote, in document order, like the tags
			# of a translation <cit>. They share the first quote's block so
			# they stay on the same line as the example text.
			tags = [
				child
				for child in citElem.iterchildren()
				if child.tag in {f"{_TEI}usg", f"{_TEI}lbl"} and _elementText(child)
			]
			quotes = citElem.findall("quote", _NAMESPACE)
			if quotes:
				self.writeQuote(hf, quotes[0], tags)
				for quote in quotes[1:]:
					self.writeQuote(hf, quote)
			elif tags:
				with hf.element("div"):
					self.writeInlineTags(hf, tags)
			# <note> holds the translation of the example, so it is written
			# as its own block after the quote, like a second quote would be
			for note in citElem.findall("note", _NAMESPACE):
				if not _elementText(note):
					continue
				with hf.element("div"):
					self.writeNote(hf, note)
			for cit2 in citElem.findall("cit", _NAMESPACE):
				# This mutates the source tree on purpose: writeWithDirection
				# reads xml:lang and type from the quote itself, so the nested
				# <cit> attributes (e.g. type="example") are copied onto each
				# quote before it is written. It is safe to repeat because
				# it only copies the same values again.
				for quote in cit2.findall("quote", _NAMESPACE):
					quote.attrib.update(cit2.attrib)
				writeExampleCit(cit2)

		for cit in ps.exampleCits:
			with hf.element(
				"div",
				attrib={
					"class": "example",
					"style": f"padding: {self._example_padding}px 0px;",
				},
			):
				writeExampleCit(cit)

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
		color = self._gram_color
		attrib = {
			"class": self.gramClass,
		}
		if color:
			attrib["color"] = color

		for gramGrp in gramGrpList:
			parts: list[str] = []
			for child in gramGrp.iterchildren():
				if not isinstance(child.tag, str):
					# comment or processing instruction
					continue
				part = self.normalizeGramGrpChild(child)
				if part:
					parts.append(part)
			if not parts:
				continue

			sep = self.getCommaSep(parts[0])
			text = sep.join(parts)

			with hf.element("div"):
				with hf.element("font", attrib=attrib):
					hf.write(text)

	def writeGramGroupChildren(
		self,
		hf: T_htmlfile,
		elem: Element,
	) -> None:
		gramGrpList = elem.findall("gramGrp", _NAMESPACE)
		if elem.tag == _ENTRY:
			# Some dictionaries put grammar info on the headword form.
			gramGrpList += elem.findall("form/gramGrp", _NAMESPACE)
		self.writeGramGroups(hf, gramGrpList)

	@classmethod
	def isMetaSense(cls, sense: Element) -> bool:
		childTagSet = {
			child.tag for child in sense.iterchildren() if isinstance(child.tag, str)
		}
		return childTagSet == {f"{_TEI}sense"}

	def writeSense(
		self,
		hf: T_htmlfile,
		sense: Element,
	) -> None:
		# this <sense> element is 1st-level (directly under <entry>)
		self.writeGramGroupChildren(hf, sense)
		# Write this sense's own content first, then its sub-senses in
		# document order, so a sub-sense never precedes its parent's text.
		self.writeSenseSense(hf, sense)
		subSenses = [
			subSense
			for subSense in sense.findall(".//sense", _NAMESPACE)
			if not self.isMetaSense(subSense)
		]

		def writeSubSense(hf_: T_htmlfile, subSense: Element) -> None:
			# Block wrapper keeps the sub-sense text from running into the
			# text of the previous sense.
			with hf_.element("div"):
				self.writeSenseSense(hf_, subSense)

		self.makeList(
			hf,
			subSenses,
			writeSubSense,
			single_prefix="",
		)

	def writeSenseList(
		self,
		hf: T_htmlfile,
		senseList: list[Element],
	) -> None:
		# these <sense> elements are 1st-level (directly under <entry>)
		if not senseList:
			return

		if self._auto_rtl and self.isRTL(senseList[0]):
			# Use unordered list for just 2 items
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
		text = _elementText(elem)
		if not text:
			return ""
		if tag == f"{_TEI}pos":
			return self.posMapping.get(text.lower(), text)
		if tag == f"{_TEI}gen":
			return self.genderMapping.get(text.lower(), text)
		if tag in {f"{_TEI}num", f"{_TEI}number"}:
			return self.numberMapping.get(text.lower(), text)
		if tag == f"{_TEI}subc":
			return self.subcMapping.get(text.lower(), text)
		if tag == f"{_TEI}gram":
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

		if tag == f"{_TEI}note":
			return text

		if tag == f"{_TEI}colloc":
			return text

		log.warning(
			f"unrecognize GramGrp child tag: {elem.tag!r}: {self.tostring(elem)}",
		)
		return text

	def getEntryByElem(  # noqa: PLR0912
		self,
		entry: Element,
	) -> EntryType:
		from lxml import etree as ET

		glos = self._glos
		keywords: list[str] = []
		buff = BytesIO()
		pron_color = self._pron_color

		def br() -> Element:
			return ET.Element("br")

		def write_keywords_title(keywords: list[str]) -> None:
			for keyword in keywords:
				titleTag = glos.titleTag(keyword)
				if titleTag:
					with hf.element(titleTag):
						hf.write(keyword)
				else:
					hf.write(keyword)
				hf.write(br())

		inflectedKeywords: list[str] = []

		for form in entry.findall(".//form", _NAMESPACE):
			inflected = form.get("type") == "infl"
			for orth in form.findall("orth", _NAMESPACE):
				text = _elementText(orth)
				if not text:
					continue
				if inflected:
					inflectedKeywords.append(text)
				else:
					keywords.append(text)

		keywords += inflectedKeywords

		pronList: list[str] = []
		for pron in entry.findall("form/pron", _NAMESPACE):
			text = _elementText(pron).strip("/")
			if text:
				pronList.append(text)
		usgList = entry.findall("usg", _NAMESPACE) + entry.findall(
			"form/usg",
			_NAMESPACE,
		)
		lblList = [
			lbl
			for lbl in (
				entry.findall("lbl", _NAMESPACE) + entry.findall("form/lbl", _NAMESPACE)
			)
			if _elementText(lbl)
		]
		senseList = entry.findall("sense", _NAMESPACE)

		with ET.htmlfile(buff, encoding="utf-8") as hf:
			with hf.element("div"):
				if self._word_title:
					write_keywords_title(keywords)

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

				if usgList:
					self.writeUsageTags(hf_, usgList)
				if lblList:
					self.writeLabelTags(hf_, lblList)

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

	def setTermCount(self, header: Element) -> None:
		extent_elem = header.find(".//extent", _NAMESPACE)
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
			self._entryCount = int(extent.split(" ")[0].replace(",", ""))
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
		elems = header.findall(".//availability//p", _NAMESPACE)
		if not elems:
			log.warning("did not find copyright")
			return
		copyright_ = self.stripParagList(elems)
		copyright_ = self.replaceRefLink(copyright_)
		self.setGlosInfo("copyright", copyright_)
		log.debug(f"Copyright: {copyright_!r}")

	def setPublisher(self, header: Element) -> None:
		elem = header.find(".//publisher", _NAMESPACE)
		if elem is None or not elem.text:
			log.warning("did not find publisher")
			return
		self.setGlosInfo("publisher", elem.text)

	def setCreationTime(self, header: Element) -> None:
		elem = header.find(".//publicationStmt/date", _NAMESPACE)
		if elem is None or not elem.text:
			return
		self.setGlosInfo("creationTime", elem.text)

	def replaceRefLink(self, text: str) -> str:
		return self._ref_pattern.sub('<a href="\\1">\\2</a>', text)

	def setDescription(self, header: Element) -> None:
		elems: list[Element] = []
		for tag in ("sourceDesc", "projectDesc"):
			elems += header.findall(f".//{tag}//p", _NAMESPACE)
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
		self.setTermCount(header)
		title = header.find(".//title", _NAMESPACE)
		if title is not None and title.text:
			self.setGlosInfo("name", title.text)

		edition = header.find(".//edition", _NAMESPACE)
		if edition is not None and edition.text:
			self.setGlosInfo("edition", edition.text)

		self.setCopyright(header)
		self.setPublisher(header)
		self.setCreationTime(header)
		self.setDescription(header)

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dirname = ""
		self._file: IOBase = nullBinaryIO
		self._fileSize = 0
		self._progress = True
		self._entryCount = 0
		# real paths of the files from the top-level file down to this one
		self._includeChain: frozenset[str] = frozenset()

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

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		return self._entryCount

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
		# an empty chain means this is the top-level file, not an XInclude
		isTopLevel = not self._includeChain
		self._includeChain = self._includeChain | {realpath(filename)}
		cfile = compressionOpen(filename, mode="rb")

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			if isTopLevel:
				# only the top-level file defines the glossary's input size,
				# included files must not overwrite it
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
			tag=f"{_TEI}teiHeader",
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
		if realpath(filename) in self._includeChain:
			log.error(f"include cycle: {filename!r} from {elem}, skipping")
			return None
		reader = Reader(self._glos)
		self._copyOptionsTo(reader)
		reader._includeChain = self._includeChain
		reader.open(filename)
		return reader

	def __iter__(self) -> Iterator[EntryType]:
		from lxml import etree as ET

		self._file = compressionOpen(self._filename, mode="rb")
		context = ET.iterparse(  # type: ignore # noqa: PGH003
			self._file,
			events=("end",),
			tag=(_ENTRY, _INCLUDE),
		)
		for _, elem_ in context:
			elem = cast("Element", elem_)

			if elem.tag == _INCLUDE:
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
