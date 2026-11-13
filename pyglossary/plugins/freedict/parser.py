"""
Parse FreeDict TEI XML into renderer-independent dataclasses.

Provides the parsed entry model (``Entry``, ``Sense``, ``TransCit``, ...)
and the ``Parser`` mixin used by the FreeDict readers. The renderer only
consumes the dataclasses produced here; it never walks the TEI tree.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.langs import langDict

from .utils import XMLLANG

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.stubs.lxml_types import Element


__all__ = [
	"ENTRY",
	"INCLUDE",
	"NAMESPACE",
	"TEI",
	"Block",
	"Break",
	"Elem",
	"Entry",
	"ExampleCit",
	"GramGroup",
	"Inline",
	"Lang",
	"Metadata",
	"Parser",
	"Ref",
	"Sense",
	"Tag",
	"Text",
	"TransCit",
]


TEI = "{http://www.tei-c.org/ns/1.0}"
ENTRY = f"{TEI}entry"
INCLUDE = "{http://www.w3.org/2001/XInclude}include"
NAMESPACE = {None: "http://www.tei-c.org/ns/1.0"}
_whitespaceRun = re.compile(r"\s+")
_p_pattern = re.compile("<p( [^<>]*?)?>(.*?)</p>", re.DOTALL)
_ref_pattern = re.compile('<ref target="(.*?)">(.*?)</ref>')
_website_pattern = re.compile('Home: <(ref|ptr) target="(.*)">(.*)</\\1>')


def _elementText(elem: Element) -> str:
	"""Return all text inside an element, including nested markup."""
	return "".join(elem.itertext()).strip()


# ---------------------------------------------------------------------------
# Parsed (renderer-independent) representation
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Text:
	text: str


@dataclass(slots=True)
class Ref:
	text: str
	target: str | None = None


@dataclass(slots=True)
class Break:
	pass


@dataclass(slots=True)
class Elem:
	tag: str
	attrib: dict[str, str]
	children: list[Inline]


Inline = Text | Ref | Break | Elem


@dataclass(slots=True)
class Tag:
	kind: str
	children: list[Inline]


@dataclass(slots=True)
class Block:
	attrib: dict[str, str]
	children: list[Inline]
	tags: list[Tag] = field(default_factory=list)


@dataclass(slots=True)
class Lang:
	desc: str | None
	text: str


@dataclass(slots=True)
class GramGroup:
	parts: list[str]


@dataclass(slots=True)
class ExampleCit:
	tags: list[Tag] = field(default_factory=list)
	quotes: list[Block] = field(default_factory=list)
	notes: list[list[Inline]] = field(default_factory=list)
	subCits: list[ExampleCit] = field(default_factory=list)


@dataclass(slots=True)
class Sense:
	gramGroups: list[GramGroup] = field(default_factory=list)
	langs: list[Lang] = field(default_factory=list)
	defs: list[list[Inline]] = field(default_factory=list)
	grams: list[str] = field(default_factory=list)
	notes: list[list[Inline]] = field(default_factory=list)
	transCits: list[TransCit] = field(default_factory=list)
	refs: list[Ref] = field(default_factory=list)
	xrList: list[list[Inline]] = field(default_factory=list)
	exampleCits: list[ExampleCit] = field(default_factory=list)
	usages: list[Tag] = field(default_factory=list)
	labels: list[Tag] = field(default_factory=list)
	subSenses: list[Sense] = field(default_factory=list)
	lang: str | None = None


@dataclass(slots=True)
class TransCit:
	blocks: list[Block] = field(default_factory=list)
	rest: Sense = field(default_factory=Sense)


@dataclass(slots=True)
class Entry:
	keywords: list[str] = field(default_factory=list)
	pronunciations: list[str] = field(default_factory=list)
	usages: list[Tag] = field(default_factory=list)
	labels: list[Tag] = field(default_factory=list)
	gramGroups: list[GramGroup] = field(default_factory=list)
	senses: list[Sense] = field(default_factory=list)


@dataclass(slots=True)
class Metadata:
	entryCount: int | None = None
	name: str | None = None
	edition: str | None = None
	copyright: str | None = None
	publisher: str | None = None
	creationTime: str | None = None
	description: str | None = None
	website: str | None = None


@dataclass(slots=True)
class _CitScan:
	"""State while scanning the children of one translation <cit>."""

	cit: Element
	blocks: list[Block] = field(default_factory=list)
	# <usg> and <lbl> tags, rendered before the first block
	tags: list[Tag] = field(default_factory=list)
	# loose text, joined into one block before the next quote or nested <cit>
	pendingText: list[str] = field(default_factory=list)


class TransCitCollector:
	"""
	Split a translation <cit> into dataclass blocks and a rest sense.

	The collector only reads the source tree. Grammar, notes and unknown
	content that sit next to the quotes are accumulated directly into a
	``Sense`` dataclass, so nothing is copied, moved, or wrapped in synthetic
	elements.
	"""

	def __init__(self, parser: Parser) -> None:
		self._parser = parser
		self._rest = Sense()
		self._gramParts: list[str] = []
		self._gramIndex: int | None = None

	def collect(self, cit: Element) -> TransCit:
		blocks = self._collectBlocks(cit)
		if self._gramIndex is not None:
			self._rest.gramGroups.insert(self._gramIndex, GramGroup(self._gramParts))
		return TransCit(blocks, self._rest)

	def _collectBlocks(self, cit: Element) -> list[Block]:
		scan = _CitScan(cit)
		for child in cit.xpath("child::node()"):
			self._handleChild(scan, child)
		self._flushText(scan)
		if scan.tags:
			if not scan.blocks:
				scan.blocks.append(self._textBlock("", cit))
			scan.blocks[0].tags = scan.tags + scan.blocks[0].tags
		return scan.blocks

	def _handleChild(self, scan: _CitScan, child: str | Element) -> None:  # noqa: PLR0912
		if isinstance(child, str):
			text = child.strip()
			if text:
				log.warning(f"text directly inside <cit>: {text}")
				scan.pendingText.append(text)
			return

		if child.__class__.__name__ == "_Comment":
			return

		if child.tag == f"{TEI}quote":
			self._flushText(scan)
			scan.blocks.append(self._parser._parseBlock(child))
			return

		if child.tag == f"{TEI}gramGrp":
			group = self._parser._parseGramGroup(child)
			if group is not None:
				self._rest.gramGroups.append(group)
			return

		if child.tag == f"{TEI}note":
			self._rest.notes.append(self._parser._parseInlineNodes(child))
			return

		if child.tag in {f"{TEI}usg", f"{TEI}lbl"}:
			# <usg> is kept here (not in the rest sense) because it gives the
			# domain/context of the translation, e.g. "[archaic] word", so it
			# must come first.
			if _elementText(child):
				scan.tags.append(
					self._parser._parseTag(child, self._parser._tagKind(child)),
				)
			return

		if child.tag in {
			f"{TEI}pos",
			f"{TEI}gen",
			f"{TEI}number",
			f"{TEI}num",
			f"{TEI}subc",
		}:
			part = self._parser.normalizeGramGrpChild(child)
			if part:
				if self._gramIndex is None:
					self._gramIndex = len(self._rest.gramGroups)
				self._gramParts.append(part)
			return

		if child.tag == f"{TEI}cit":
			self._handleNestedCit(scan, child)
			return

		self._handleUnknown(child)

	def _handleNestedCit(self, scan: _CitScan, child: Element) -> None:
		typ = child.attrib.get("type", "trans")
		if typ in {"abbrev", "abbreviation"}:
			# An abbreviation <cit> only carries <orth> text that should be
			# shown as a label.
			for orth in child.findall("orth", NAMESPACE):
				text = _elementText(orth)
				if text:
					children = self._parser._normalizeInlineWhitespace([Text(text)])
					scan.tags.append(Tag("lbl", children))
			return
		# A nested <cit> is collected into its own blocks, so its quotes and
		# tags stay with its own content.
		self._flushText(scan)
		scan.blocks += self._collectBlocks(child)

	def _handleUnknown(self, child: Element) -> None:
		log.warning(
			f"unknown tag {child.tag!r} inside translation <cit>"
			f": {self._parser.tostring(child)}",
		)
		# Keep the text of an unknown element as a note instead of dropping it.
		text = _elementText(child)
		if text:
			self._rest.notes.append([Text(text)])

	def _flushText(self, scan: _CitScan) -> None:
		if scan.pendingText:
			text = " ".join(scan.pendingText)
			scan.blocks.append(self._textBlock(text, scan.cit))
			scan.pendingText.clear()

	def _textBlock(self, text: str, cit: Element) -> Block:
		# Loose text has no element of its own. Build a block from the <cit>
		# attributes so xml:lang (lang/dir) and type (class) apply to it as
		# they do to real quotes.
		return Block(
			attrib=self._parser._blockAttrib(dict(cit.attrib)),
			children=[Text(text)],
		)


class Parser:
	"""Parse TEI elements into the dataclasses above."""

	_auto_rtl: bool = True

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

	def _parseRef(self, elem: Element) -> Ref | None:
		target = elem.get("target")
		text = elem.text or ""
		if not target and not text:
			# no target to link to and no text to show
			log.warning("ref without target or text, skipped")
			return None
		return Ref(text=text, target=target)

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

	def _blockAttrib(self, attrib: dict[str, str]) -> dict[str, str]:
		self.setAttribLangDir(attrib)
		try:
			type_ = attrib.pop("type")
		except KeyError:
			pass
		else:
			if type_ != "trans":
				attrib["class"] = type_
		return attrib

	def _parseInlineNodes(self, elem: Element) -> list[Inline]:
		nodes: list[Inline] = []
		for child in elem.xpath("child::node()"):
			if isinstance(child, str):
				nodes.append(Text(child))
				continue
			if not isinstance(child.tag, str):
				# comment or processing instruction
				continue
			if child.tag == f"{TEI}ref":
				ref = self._parseRef(child)
				if ref is not None:
					nodes.append(ref)
				continue
			if child.tag == f"{TEI}br":
				nodes.append(Break())
				continue
			if child.tag == f"{TEI}p":
				# map xml:lang to lang (and dir), like the block parser does;
				# passing the raw attribute would emit an ns0:lang attribute
				attrib = dict(child.attrib)
				self.setAttribLangDir(attrib)
				nodes.append(Elem("p", attrib, self._parseInlineNodes(child)))
				continue
			if child.tag == f"{TEI}div":
				nodes.append(
					Elem(
						"div",
						self._blockAttrib(dict(child.attrib)),
						self._parseInlineNodes(child),
					),
				)
				continue
			if child.tag == f"{TEI}span":
				nodes.append(
					Elem(
						"span",
						self._blockAttrib(dict(child.attrib)),
						self._parseInlineNodes(child),
					),
				)
				continue

			nodes.extend(self._parseInlineNodes(child))
		return nodes

	def _parseBlock(self, elem: Element) -> Block:
		return Block(
			attrib=self._blockAttrib(dict(elem.attrib)),
			children=self._parseInlineNodes(elem),
		)

	@staticmethod
	def _tagKind(elem: Element) -> str:
		return "lbl" if elem.tag == f"{TEI}lbl" else "usg"

	@staticmethod
	def _iterTextNodes(nodes: list[Inline]) -> Iterator[Text]:
		for node in nodes:
			if isinstance(node, Text):
				yield node
			elif isinstance(node, Elem):
				yield from Parser._iterTextNodes(node.children)

	def _normalizeInlineWhitespace(self, nodes: list[Inline]) -> list[Inline]:
		"""
		Collapse whitespace in the parsed inline nodes of a tag.

		Line breaks and indentation in the source are not meaningful, so runs
		of whitespace are collapsed to one space and the content is trimmed at
		both ends. This runs on the parsed nodes, leaving the source tree
		untouched.
		"""
		textNodes = list(self._iterTextNodes(nodes))

		atSpace = True  # True at the start, so leading whitespace is dropped
		for node in textNodes:
			text = node.text
			if not text:
				continue
			text = _whitespaceRun.sub(" ", text)
			if atSpace:
				text = text.lstrip(" ")
			if text:
				atSpace = text.endswith(" ")
			node.text = text

		# drop trailing whitespace, continuing backwards over whitespace-only nodes
		for node in reversed(textNodes):
			text = node.text.rstrip(" ")
			node.text = text
			if text:
				break
		return nodes

	def _parseTag(self, elem: Element, kind: str) -> Tag:
		content = self._parseInlineNodes(elem)
		return Tag(kind, self._normalizeInlineWhitespace(content))

	def _parseLang(self, elem: Element) -> Lang:
		return Lang(self.getLangDesc(elem), elem.text or "")

	def _iterDefPieces(self, node: Element) -> Iterator[str | Ref]:
		"""Yield the text and <ref> pieces of a <def>, recursing into other elements."""
		for child in node.xpath("child::node()"):
			if isinstance(child, str):
				yield child
				continue
			if not isinstance(child.tag, str):
				# comment or processing instruction
				continue
			if child.tag == f"{TEI}ref":
				if child.text:
					ref = self._parseRef(child)
					if ref is not None:
						yield ref
				else:
					log.warning(f"ref without text: {self.tostring(child)}")
				continue
			yield from self._iterDefPieces(child)

	def _parseDef(self, elem: Element) -> list[Inline]:
		"""
		Return the inline pieces of a <def>, ready to render.

		Adjacent text is merged before whitespace is collapsed, so spacing
		around skipped comments and inline elements is kept. Leading and
		trailing whitespace of the whole definition is removed.
		"""
		merged: list[str | Ref] = []
		for piece in self._iterDefPieces(elem):
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

		pieces: list[Inline] = []
		for piece in merged:
			if isinstance(piece, str):
				if piece:
					pieces.append(Text(piece))
			else:
				pieces.append(piece)
		return pieces

	def _parseGramGroup(self, gramGrp: Element) -> GramGroup | None:
		parts: list[str] = []
		for child in gramGrp.iterchildren():
			if not isinstance(child.tag, str):
				# comment or processing instruction
				continue
			part = self.normalizeGramGrpChild(child)
			if part:
				parts.append(part)
		if not parts:
			return None
		return GramGroup(parts)

	def _parseGramGroups(self, elems: list[Element]) -> list[GramGroup]:
		groups: list[GramGroup] = []
		for elem in elems:
			group = self._parseGramGroup(elem)
			if group is not None:
				groups.append(group)
		return groups

	def _parseSense(self, sense: Element, *, parseSubsenses: bool = False) -> Sense:
		# this <sense> element can be 1st-level (directly under <entry>)
		# or 2nd-level
		ps = Sense(lang=sense.get(XMLLANG))
		ps.gramGroups = self._parseGramGroups(sense.findall("gramGrp", NAMESPACE))
		for child in sense.iterchildren():
			if not isinstance(child.tag, str):
				# comment or processing instruction
				continue
			self._parseSenseChild(ps, child)
		if parseSubsenses:
			ps.subSenses = [
				self._parseSense(subSense)
				for subSense in sense.findall(".//sense", NAMESPACE)
				if not self.isMetaSense(subSense)
			]
		return ps

	def _parseSenseChild(self, ps: Sense, child: Element) -> None:
		if child.tag == f"{TEI}cit":
			self._parseSenseCit(ps, child)
		elif child.tag == f"{TEI}def":
			ps.defs.append(self._parseDef(child))
		elif child.tag == f"{TEI}note":
			self._parseSenseNote(ps, child)
		elif child.tag == f"{TEI}ref":
			ref = self._parseRef(child)
			if ref is not None:
				ps.refs.append(ref)
		elif child.tag == f"{TEI}usg":
			if not _elementText(child):
				log.warning(f"empty usg: {self.tostring(child)}")
				return
			ps.usages.append(self._parseTag(child, "usg"))
		elif child.tag == f"{TEI}lbl":
			if _elementText(child):
				ps.labels.append(self._parseTag(child, "lbl"))
		elif child.tag == f"{TEI}lang":
			ps.langs.append(self._parseLang(child))
		elif child.tag == f"{TEI}xr":
			ps.xrList.append(self._parseInlineNodes(child))
		elif child.tag not in {f"{TEI}sense", f"{TEI}gramGrp", f"{TEI}form"}:
			log.warning(f"unknown tag {child.tag} in <sense>: {self.tostring(child)}")

	def _parseSenseCit(self, ps: Sense, cit: Element) -> None:
		typ = cit.attrib.get("type", "trans")
		if typ == "trans":
			ps.transCits.append(self._parseTransCit(cit))
		elif typ == "example":
			ps.exampleCits.append(self._parseExampleCit(cit))
		elif typ == "idiom":
			ps.transCits.append(self._parseTransCit(cit))  # FIXME
		elif typ in {"abbrev", "abbreviation"}:
			ps.notes.append(self._parseInlineNodes(cit))
		else:
			log.warning(f"unknown cit type: {self.tostring(cit)}")
			ps.notes.append(self._parseInlineNodes(cit))

	def _parseSenseNote(self, ps: Sense, note: Element) -> None:
		type_ = note.attrib.get("type")
		if not type_:
			ps.notes.append(self._parseInlineNodes(note))
		elif type_ in {"pos", "gram"}:
			ps.grams.append(_elementText(note))
		elif type_ in self.noteTypes:
			ps.notes.append(self._parseInlineNodes(note))
		else:
			log.warning(f"unknown note type {type_}")
			ps.notes.append(self._parseInlineNodes(note))

	def _parseTransCit(self, cit: Element) -> TransCit:
		return TransCitCollector(self).collect(cit)

	def _parseExampleCit(
		self,
		citElem: Element,
		applyAttrib: dict[str, str] | None = None,
	) -> ExampleCit:
		example = ExampleCit()
		example.tags = [
			self._parseTag(child, self._tagKind(child))
			for child in citElem.iterchildren()
			if isinstance(child.tag, str)
			and child.tag in {f"{TEI}usg", f"{TEI}lbl"}
			and _elementText(child)
		]
		for quote in citElem.findall("quote", NAMESPACE):
			attrib = dict(quote.attrib)
			if applyAttrib:
				attrib.update(applyAttrib)
			example.quotes.append(
				Block(
					attrib=self._blockAttrib(attrib),
					children=self._parseInlineNodes(quote),
				),
			)
		for note in citElem.findall("note", NAMESPACE):
			if not _elementText(note):
				continue
			example.notes.append(self._parseInlineNodes(note))
		for cit2 in citElem.findall("cit", NAMESPACE):
			# The nested <cit> grammar, note and usage content belongs to the
			# nested example; only its attributes are applied to its quotes.
			example.subCits.append(self._parseExampleCit(cit2, dict(cit2.attrib)))
		return example

	@classmethod
	def isMetaSense(cls, sense: Element) -> bool:
		childTagSet = {
			child.tag for child in sense.iterchildren() if isinstance(child.tag, str)
		}
		return childTagSet == {f"{TEI}sense"}

	@staticmethod
	def _entryKeywords(entry: Element) -> list[str]:
		"""Return the headwords, then the inflected forms, of an entry."""
		keywords: list[str] = []
		inflectedKeywords: list[str] = []
		for form in entry.findall(".//form", NAMESPACE):
			inflected = form.get("type") == "infl"
			for orth in form.findall("orth", NAMESPACE):
				text = _elementText(orth)
				if not text:
					continue
				if inflected:
					inflectedKeywords.append(text)
				else:
					keywords.append(text)

		keywords += inflectedKeywords
		return keywords

	@staticmethod
	def _entryPronunciations(entry: Element) -> list[str]:
		pronList: list[str] = []
		for pron in entry.findall("form/pron", NAMESPACE):
			text = _elementText(pron).strip("/")
			if text:
				pronList.append(text)
		return pronList

	def parseEntry(self, entry: Element) -> Entry:
		pe = Entry()
		pe.keywords = self._entryKeywords(entry)
		pe.pronunciations = self._entryPronunciations(entry)
		pe.usages = [
			self._parseTag(usg, "usg")
			for usg in (
				entry.findall("usg", NAMESPACE) + entry.findall("form/usg", NAMESPACE)
			)
		]
		pe.labels = [
			self._parseTag(lbl, "lbl")
			for lbl in (
				entry.findall("lbl", NAMESPACE) + entry.findall("form/lbl", NAMESPACE)
			)
			if _elementText(lbl)
		]
		gramGrpList = entry.findall("gramGrp", NAMESPACE)
		gramGrpList += entry.findall("form/gramGrp", NAMESPACE)
		pe.gramGroups = self._parseGramGroups(gramGrpList)
		pe.senses = [
			self._parseSense(sense, parseSubsenses=True)
			for sense in entry.findall("sense", NAMESPACE)
		]
		return pe

	def _mappingByName(self) -> dict[str, dict[str, str]]:
		# <pos>, <gen>, <num>, <number> and <subc> elements, and the "type"
		# of a <gram> element, all name one of these mappings
		return {
			"pos": self.posMapping,
			"gen": self.genderMapping,
			"num": self.numberMapping,
			"number": self.numberMapping,
			"subc": self.subcMapping,
		}

	def _normalizeGram(self, elem: Element, text: str) -> str:
		type_ = elem.get("type")
		if not type_:
			log.warning(f"<gram> with no type: {self.tostring(elem)}")
			return text
		mapping = self._mappingByName().get(type_)
		if mapping is None:
			log.warning(f"unrecognize type={type_!r}: {self.tostring(elem)}")
			return text
		return mapping.get(text.lower(), text)

	def normalizeGramGrpChild(self, elem: Element) -> str:
		# child can be <pos>, <gen>, <num>, <number>, <subc>, <gram>, <note>
		# or <colloc>
		text = _elementText(elem)
		if not text:
			return ""
		tag = elem.tag
		if tag == f"{TEI}gram":
			return self._normalizeGram(elem, text)
		if tag in {f"{TEI}note", f"{TEI}colloc"}:
			return text
		if tag.startswith(TEI):
			mapping = self._mappingByName().get(tag.removeprefix(TEI))
			if mapping is not None:
				return mapping.get(text.lower(), text)

		log.warning(
			f"unrecognize GramGrp child tag: {elem.tag!r}: {self.tostring(elem)}",
		)
		return text

	def parseIncludeHref(self, elem: Element) -> str | None:
		href = elem.attrib.get("href")
		if not href:
			log.error(f"empty href in {elem}")
			return None
		return href

	@staticmethod
	def isIncludeElement(elem: Element) -> bool:
		return elem.tag == INCLUDE

	@staticmethod
	def dropPreviousSiblings(elem: Element) -> None:
		parent = elem.getparent()
		if parent is None:
			return
		while elem.getprevious() is not None:
			del parent[0]

	def _stripParag(self, elem: Element) -> str:
		text = self.tostring(elem)
		return _p_pattern.sub("\\2", text)

	def _stripParagList(self, elems: list[Element]) -> str:
		lines: list[str] = []
		for elem in elems:
			for line in self._stripParag(elem).split("\n"):
				line = line.strip()  # noqa: PLW2901
				if not line:
					continue
				lines.append(line)
		return "\n".join(lines)

	@staticmethod
	def _replaceRefLink(text: str) -> str:
		return _ref_pattern.sub('<a href="\\1">\\2</a>', text)

	def _parseTermCount(self, header: Element) -> int | None:
		extent_elem = header.find(".//extent", NAMESPACE)
		if extent_elem is None:
			log.warning(
				"did not find 'extent' tag in metedata, progress bar will not word",
			)
			return None
		extent = extent_elem.text or ""
		if not extent.endswith(" headwords"):
			log.warning(f"unexpected {extent=}")
			return None
		try:
			return int(extent.split(" ")[0].replace(",", ""))
		except Exception:
			log.exception(f"unexpected {extent=}")
			return None

	def _parseCopyright(self, header: Element) -> str | None:
		elems = header.findall(".//availability//p", NAMESPACE)
		if not elems:
			log.warning("did not find copyright")
			return None
		copyright_ = self._stripParagList(elems)
		copyright_ = self._replaceRefLink(copyright_)
		log.debug(f"Copyright: {copyright_!r}")
		return copyright_

	def _parsePublisher(self, header: Element) -> str | None:
		elem = header.find(".//publisher", NAMESPACE)
		if elem is None or not elem.text:
			log.warning("did not find publisher")
			return None
		return elem.text

	@staticmethod
	def _parseCreationTime(header: Element) -> str | None:
		elem = header.find(".//publicationStmt/date", NAMESPACE)
		if elem is None or not elem.text:
			return None
		return elem.text

	def _parseDescription(self, header: Element, metadata: Metadata) -> None:
		elems: list[Element] = []
		for tag in ("sourceDesc", "projectDesc"):
			elems += header.findall(f".//{tag}//p", NAMESPACE)
		desc = self._stripParagList(elems)
		if not desc:
			return
		website_list: list[str] = []
		for match in _website_pattern.findall(desc):
			if not match[1]:
				continue
			website_list.append(match[1])
		if website_list:
			metadata.website = " | ".join(website_list)
			desc = _website_pattern.sub("", desc).strip()
			log.debug(f"Website: {metadata.website}")
		metadata.description = self._replaceRefLink(desc)
		log.debug(
			"------------ Description: ------------\n"
			f"{metadata.description}\n"
			"--------------------------------------",
		)

	def parseMetadata(self, header: Element) -> Metadata:
		metadata = Metadata()
		metadata.entryCount = self._parseTermCount(header)

		title = header.find(".//title", NAMESPACE)
		if title is not None and title.text:
			metadata.name = title.text

		edition = header.find(".//edition", NAMESPACE)
		if edition is not None and edition.text:
			metadata.edition = edition.text

		metadata.copyright = self._parseCopyright(header)
		metadata.publisher = self._parsePublisher(header)
		metadata.creationTime = self._parseCreationTime(header)
		self._parseDescription(header, metadata)
		return metadata
