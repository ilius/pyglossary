"""
Read FreeDict TEI XML dictionaries.

Parses TEI ``<entry>`` elements (including XInclude), resolves FreeDict
translation and orthography modules, detects source/target languages from
``xml:lang``, and builds HTML definitions.

The TEI parsing lives in :mod:`pyglossary.plugins.freedict.parser`; this
module only renders the parsed dataclasses.
"""

from __future__ import annotations

# mypy: ignore-errors
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

from .parser import (
	ENTRY,
	INCLUDE,
	TEI,
	Block,
	Break,
	Elem,
	Entry,
	ExampleCit,
	GramGroup,
	Inline,
	Lang,
	Metadata,
	Parser,
	Ref,
	Sense,
	Tag,
	Text,
	TransCit,
)
from .utils import ReaderUtils

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator
	from io import IOBase

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType
	from pyglossary.stubs.lxml_types import Element, T_htmlfile


__all__ = ["Reader"]


@dataclass(slots=True)
class _PendingTags:
	"""<usg> and <lbl> tags of a sense that are not written yet."""

	usages: list[Tag]
	labels: list[Tag]


class Reader(ReaderUtils, Parser):
	"""Read Freedict glossary files."""

	useByteProgress = True
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

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

	# -----------------------------------------------------------------------
	# Rendering: dataclasses -> HTML (or any htmlfile-compatible writer)
	# -----------------------------------------------------------------------

	def writeRef(self, hf: T_htmlfile, ref: Ref) -> None:
		target = ref.target
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
			hf.write(ref.text)

	def writeInlineNodes(self, hf: T_htmlfile, nodes: list[Inline]) -> None:
		from lxml import etree as ET

		for node in nodes:
			if isinstance(node, Text):
				hf.write(node.text)
			elif isinstance(node, Ref):
				self.writeRef(hf, node)
			elif isinstance(node, Break):
				hf.write(ET.Element("br"))
			elif isinstance(node, Elem):
				if node.tag == "p":
					# <p> only maps xml:lang to lang/dir
					with hf.element("p", attrib=dict(node.attrib)):
						self.writeInlineNodes(hf, node.children)
				elif node.tag in {"div", "span"}:
					with hf.element(node.tag, attrib=dict(node.attrib)):
						self.writeInlineNodes(hf, node.children)
				else:
					self.writeInlineNodes(hf, node.children)

	def writeBlock(
		self,
		hf: T_htmlfile,
		block: Block,
		prefix: list[Tag] | None = None,
	) -> None:
		with hf.element("div", attrib=dict(block.attrib)):
			# Render the prefix inside the block element so it shares the
			# line with the content, rather than appearing on its own line.
			if prefix:
				self.writeInlineTags(hf, prefix)
			if block.tags:
				self.writeInlineTags(hf, block.tags)
			self.writeInlineNodes(hf, block.children)

	def writeTransCit(
		self,
		hf: T_htmlfile,
		transCit: TransCit,
		prefix: list[Tag] | None = None,
	) -> None:
		blocks = transCit.blocks
		if prefix and not blocks:
			self.writeInlineTags(hf, prefix)

		if len(blocks) == 1:
			self.writeBlock(hf, blocks[0], prefix)
		elif blocks:
			with hf.element("ol"):
				for i, block in enumerate(blocks):
					with hf.element("li"):
						self.writeBlock(hf, block, prefix if i == 0 else None)

		if self._senseHasContent(transCit.rest):
			self.writeSense(hf, transCit.rest)

	@staticmethod
	def _senseHasContent(sense: Sense) -> bool:
		return bool(
			sense.gramGroups
			or sense.langs
			or sense.defs
			or sense.grams
			or sense.notes
			or sense.transCits
			or sense.refs
			or sense.xrList
			or sense.exampleCits
			or sense.subSenses
		)

	def writeDef(self, hf: T_htmlfile, definition: list[Inline]) -> None:
		# <def> has phrase-level content (TEI): text, <ref> links and inline
		# elements such as <hi>. All of it stays inline, so no separator is
		# inserted between pieces.
		self.writeInlineNodes(hf, definition)

	def writeNote(self, hf: T_htmlfile, note: list[Inline]) -> None:
		self.writeInlineNodes(hf, note)

	def writeLangTag(self, hf: T_htmlfile, lang: Lang) -> None:
		if not lang.desc:
			return
		if lang.text:
			hf.write(f"{lang.desc}: {lang.text}")
		else:
			hf.write(lang.desc)

	def writeTag(
		self,
		hf: T_htmlfile,
		tag: Tag,
		color: str,
	) -> None:
		style = self.tagStyle.format(color or "transparent")
		with hf.element("span", attrib={"class": "tag", "style": style}):
			hf.write("[")
			self.writeInlineNodes(hf, tag.children)
			hf.write("]")

	def writeUsageTag(self, hf: T_htmlfile, usg: Tag) -> None:
		self.writeTag(hf, usg, self._usage_color)

	def writeLabelTag(self, hf: T_htmlfile, lbl: Tag) -> None:
		self.writeTag(hf, lbl, self._label_color)

	def writeTags(
		self,
		hf: T_htmlfile,
		tags: list[Tag],
		writer: Callable[[T_htmlfile, Tag], None],
	) -> None:
		for i, tag in enumerate(tags):
			if i > 0:
				hf.write(" ")
			writer(hf, tag)
		hf.write(" ")

	def writeUsageTags(self, hf: T_htmlfile, usages: list[Tag]) -> None:
		self.writeTags(hf, usages, self.writeUsageTag)

	def writeLabelTags(self, hf: T_htmlfile, labels: list[Tag]) -> None:
		self.writeTags(hf, labels, self.writeLabelTag)

	def writeInlineTags(self, hf: T_htmlfile, tags: list[Tag]) -> None:
		"""Write a mix of <usg> and <lbl> tags, each with its own color."""

		def writeInline(hf_: T_htmlfile, tag: Tag) -> None:
			if tag.kind == "lbl":
				self.writeLabelTag(hf_, tag)
			else:
				self.writeUsageTag(hf_, tag)

		self.writeTags(hf, tags, writeInline)

	def writeSenseSense(
		self,
		hf: T_htmlfile,
		sense: Sense,
		*,
		topLevel: bool = False,
	) -> None:
		pending = _PendingTags(usages=list(sense.usages), labels=list(sense.labels))

		# First-level senses already have their <gramGrp> rendered by
		# writeSense; nested senses need it rendered here.
		if not topLevel:
			self.writeGramGroups(hf, sense.gramGroups)

		for lang in sense.langs:
			self.writeLangTag(hf, lang)

		if sense.defs:
			self._writePendingTags(hf, pending)
		self.makeList(
			hf,
			sense.defs,
			self.writeDef,
			single_prefix="",
		)
		if sense.grams:
			self._writeGrams(hf, sense.grams, pending)
		if sense.notes:
			self._writePendingTags(hf, pending)
		self.makeList(
			hf,
			sense.notes,
			self.writeNote,
			single_prefix="",
		)
		if sense.transCits:
			self._writeTransCits(hf, sense.transCits, pending)
		self._writePendingTags(hf, pending)
		self._writeRelated(hf, sense.refs)
		for xr in sense.xrList:
			with hf.element("div"):
				self.writeInlineNodes(hf, xr)
		for example in sense.exampleCits:
			with hf.element(
				"div",
				attrib={
					"class": "example",
					"style": f"padding: {self._example_padding}px 0px;",
				},
			):
				self.writeExampleCit(hf, example)

	def _writePendingTags(
		self,
		hf: T_htmlfile,
		pending: _PendingTags,
	) -> None:
		"""Write the pending usage and label tags, then forget them."""
		if pending.usages:
			self.writeUsageTags(hf, pending.usages)
			pending.usages.clear()
		if pending.labels:
			self.writeLabelTags(hf, pending.labels)
			pending.labels.clear()

	def _writeGrams(
		self,
		hf: T_htmlfile,
		grams: list[str],
		pending: _PendingTags,
	) -> None:
		color = self._gram_color
		attrib = {
			"class": self.gramClass,
		}
		if color:
			attrib["color"] = color
		with hf.element("div"):
			self._writePendingTags(hf, pending)
			for i, text in enumerate(grams):
				if i > 0:
					hf.write(self.getCommaSep(text))
				with hf.element("font", attrib=attrib):
					hf.write(text)

	def _writeTransCits(
		self,
		hf: T_htmlfile,
		transCits: list[TransCit],
		pending: _PendingTags,
	) -> None:
		def writeFirstTransCit(hf_: T_htmlfile, elem: TransCit) -> None:
			# the first translation <cit> takes the pending usage tags as its
			# prefix, so they share its line; later ones get none
			prefix = list(pending.usages)
			pending.usages.clear()
			self.writeTransCit(hf_, elem, prefix)

		self.makeList(
			hf,
			transCits,
			writeFirstTransCit,
			single_prefix="",
		)

	def _writeRelated(
		self,
		hf: T_htmlfile,
		refs: list[Ref],
	) -> None:
		if not refs:
			return
		with hf.element("div"):
			hf.write("Related: ")
			for i, ref in enumerate(refs):
				if i > 0:
					hf.write(" | ")
				self.writeRef(hf, ref)

	def writeExampleCit(
		self,
		hf: T_htmlfile,
		example: ExampleCit,
	) -> None:
		# <usg> and <lbl> give the domain/context of the example, so they
		# are written before its quote, in document order, like the tags
		# of a translation <cit>. They share the first quote's block so
		# they stay on the same line as the example text.
		if example.quotes:
			self.writeBlock(hf, example.quotes[0], example.tags)
			for quote in example.quotes[1:]:
				self.writeBlock(hf, quote)
		elif example.tags:
			with hf.element("div"):
				self.writeInlineTags(hf, example.tags)
		# <note> holds the translation of the example, so it is written
		# as its own block after the quote, like a second quote would be
		for note in example.notes:
			with hf.element("div"):
				self.writeNote(hf, note)
		for subCit in example.subCits:
			self.writeExampleCit(hf, subCit)

	def getCommaSep(self, sample: str) -> str:
		if sample and self._auto_comma:
			ws = getWritingSystemFromText(sample)
			if ws:
				return ws.comma
		return self._comma

	def writeGramGroups(
		self,
		hf: T_htmlfile,
		gramGrpList: list[GramGroup],
	) -> None:
		color = self._gram_color
		attrib = {
			"class": self.gramClass,
		}
		if color:
			attrib["color"] = color

		for gramGrp in gramGrpList:
			parts = gramGrp.parts
			if not parts:
				continue
			sep = self.getCommaSep(parts[0])
			text = sep.join(parts)

			with hf.element("div"):
				with hf.element("font", attrib=attrib):
					hf.write(text)

	def _senseIsRTL(self, sense: Sense) -> bool:
		if sense.lang is None:
			return False
		langObj = langDict[sense.lang]
		if langObj is None:
			log.warning(f"unknown language {sense.lang}")
			return False
		return bool(langObj.rtl)

	def writeSense(
		self,
		hf: T_htmlfile,
		sense: Sense,
	) -> None:
		# this <sense> element is 1st-level (directly under <entry>)
		self.writeGramGroups(hf, sense.gramGroups)
		# Write this sense's own content first, then its sub-senses in
		# document order, so a sub-sense never precedes its parent's text.
		self.writeSenseSense(hf, sense, topLevel=True)

		def writeSubSense(hf_: T_htmlfile, subSense: Sense) -> None:
			# Block wrapper keeps the sub-sense text from running into the
			# text of the previous sense.
			with hf_.element("div"):
				self.writeSenseSense(hf_, subSense)

		self.makeList(
			hf,
			sense.subSenses,
			writeSubSense,
			single_prefix="",
		)

	def writeSenseList(
		self,
		hf: T_htmlfile,
		senseList: list[Sense],
	) -> None:
		# these <sense> elements are 1st-level (directly under <entry>)
		if not senseList:
			return

		if self._auto_rtl and self._senseIsRTL(senseList[0]):
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

	def renderEntry(self, entry: Entry) -> str:
		from lxml import etree as ET

		buff = BytesIO()
		with ET.htmlfile(buff, encoding="utf-8") as hf:
			with hf.element("div"):
				if self._word_title:
					self._writeKeywordsTitle(hf, entry.keywords)
				self._writePronunciations(hf, entry.pronunciations)

				hf_ = cast("T_htmlfile", hf)

				if entry.usages:
					self.writeUsageTags(hf_, entry.usages)
				if entry.labels:
					self.writeLabelTags(hf_, entry.labels)

				self.writeGramGroups(hf_, entry.gramGroups)
				self.writeSenseList(hf_, entry.senses)

		return buff.getvalue().decode("utf-8")

	def getEntryByElem(
		self,
		entry: Element,
	) -> EntryType:
		parsedEntry = self.parseEntry(entry)
		defi = self.renderEntry(parsedEntry)
		file = self._file
		return self._glos.newEntry(
			parsedEntry.keywords,
			defi,
			defiFormat="h",
			byteProgress=(file.tell(), self._fileSize) if self._progress else None,
		)

	def _writeKeywordsTitle(
		self,
		hf: T_htmlfile,
		keywords: list[str],
	) -> None:
		from lxml import etree as ET

		for keyword in keywords:
			titleTag = self._glos.titleTag(keyword)
			if titleTag:
				with hf.element(titleTag):
					hf.write(keyword)
			else:
				hf.write(keyword)
			hf.write(ET.Element("br"))

	def _writePronunciations(
		self,
		hf: T_htmlfile,
		pronList: list[str],
	) -> None:
		from lxml import etree as ET

		if not pronList:
			return
		for i, pron in enumerate(pronList):
			if i > 0:
				hf.write(self.getCommaSep(pron))
			hf.write("/")
			with hf.element("font", color=self._pron_color):
				hf.write(pron)
			hf.write("/")
		hf.write(ET.Element("br"))
		hf.write("\n")

	def setGlosInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, unescape_unicode(value))

	def applyMetadata(self, metadata: Metadata) -> None:
		if metadata.entryCount is not None:
			self._entryCount = metadata.entryCount
		for key in (
			"name",
			"edition",
			"copyright",
			"publisher",
			"creationTime",
			"website",
			"description",
		):
			value = getattr(metadata, key)
			if value is not None:
				self.setGlosInfo(key, value)

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
			tag=f"{TEI}teiHeader",
		)
		for _, elem in context:
			self.applyMetadata(self.parseMetadata(elem))  # type: ignore
			break

		cfile.close()

	def loadInclude(self, elem: Element) -> Reader | None:
		href = self.parseIncludeHref(elem)
		if href is None:
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
			tag=(ENTRY, INCLUDE),
		)
		for _, elem_ in context:
			elem = cast("Element", elem_)

			if self.isIncludeElement(elem):
				reader = self.loadInclude(elem)
				if reader is not None:
					yield from reader
					reader.close()
				continue

			yield self.getEntryByElem(elem)
			# clean up preceding siblings to save memory
			# this can reduce memory usage from 1 GB to ~25 MB
			self.dropPreviousSiblings(elem)
