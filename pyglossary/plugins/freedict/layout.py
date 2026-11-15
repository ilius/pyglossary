"""
Convert parsed TEI entries into the neutral FreeDict document tree.

The parser produces TEI-shaped dataclasses; this module decides the document
layout (ordering, lists, pending usage/label tags, grammar grouping) and emits
:mod:`pyglossary.plugins.freedict.document` nodes. Formatters therefore never
need to know about TEI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from pyglossary.core import log
from pyglossary.langs import langDict
from pyglossary.langs.writing_system import getWritingSystemFromText

from . import parser as P
from .document import (
	Block,
	Example,
	Grammar,
	Inline,
	InlineElement,
	LineBreak,
	Link,
	ListBlock,
	Node,
	Pronunciation,
	Tag,
	Text,
	Title,
)

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence


__all__ = ["buildDocument"]


@dataclass(slots=True)
class _PendingTags:
	"""Usage and label tags of a sense that are not written yet."""

	usages: list[P.Tag]
	labels: list[P.Tag]


class _Builder:
	def __init__(self, owner: Any) -> None:
		self._owner = owner

	@property
	def _auto_rtl(self) -> bool:
		return cast("bool", self._owner._auto_rtl)

	@property
	def _auto_comma(self) -> bool:
		return cast("bool", self._owner._auto_comma)

	@property
	def _comma(self) -> str:
		return cast("str", self._owner._comma)

	@property
	def _word_title(self) -> bool:
		return cast("bool", self._owner._word_title)

	def getCommaSep(self, sample: str) -> str:
		if sample and self._auto_comma:
			ws = getWritingSystemFromText(sample)
			if ws:
				return ws.comma
		return self._comma

	# -----------------------------------------------------------------------
	# Inline nodes
	# -----------------------------------------------------------------------

	def _inline_nodes(self, nodes: list[P.Inline]) -> list[Inline]:
		result: list[Inline] = []
		for node in nodes:
			if isinstance(node, P.Text):
				result.append(Text(node.text))
			elif isinstance(node, P.Ref):
				result.append(Link(node.target, [Text(node.text)]))
			elif isinstance(node, P.Break):
				result.append(LineBreak())
			elif isinstance(node, P.Elem):
				if node.tag in {"p", "div", "span"}:
					result.append(
						InlineElement(
							node.tag,
							dict(node.attrib),
							self._inline_nodes(node.children),
						),
					)
				else:
					result.extend(self._inline_nodes(node.children))
		return result

	def _tag_nodes(self, tags: list[P.Tag]) -> list[Node]:
		result: list[Node] = []
		for tag in tags:
			kind = "label" if tag.kind == "lbl" else "usage"
			result.append(Tag(kind, self._inline_nodes(tag.children)))
			result.append(Text(" "))
		return result

	# -----------------------------------------------------------------------
	# Blocks and lists
	# -----------------------------------------------------------------------

	def _make_list(
		self,
		objects: list[Any],
		processor: Callable[[Any], Sequence[Node]],
		single_prefix: str = "",
		ordered: bool = True,
	) -> list[Node]:
		if not objects:
			return []
		if len(objects) == 1:
			result: list[Node] = []
			if single_prefix:
				result.append(Text(single_prefix))
			result.extend(processor(objects[0]))
			return result
		return [ListBlock(ordered, [processor(obj) for obj in objects])]

	def _block(
		self,
		block: P.Block,
		prefix: list[P.Tag] | None = None,
	) -> Block:
		children: list[Node] = []
		# The prefix shares the line with the content, before the block's own
		# tags, exactly like the pending tags of a sense.
		if prefix:
			children.extend(self._tag_nodes(prefix))
		if block.tags:
			children.extend(self._tag_nodes(block.tags))
		children.extend(self._inline_nodes(block.children))
		return Block(dict(block.attrib), children)

	def _gram_groups(self, gramGrpList: list[P.GramGroup]) -> list[Node]:
		result: list[Node] = []
		for gramGrp in gramGrpList:
			parts = gramGrp.parts
			if not parts:
				continue
			sep = self.getCommaSep(parts[0])
			result.append(Block({}, [Grammar(sep.join(parts))]))
		return result

	def _grams(
		self,
		grams: list[str],
		pending: _PendingTags,
	) -> list[Node]:
		children: list[Node] = self._flushPendingTags(pending)
		for i, text in enumerate(grams):
			if i > 0:
				children.append(Text(self.getCommaSep(text)))
			children.append(Grammar(text))
		return [Block({}, children)]

	def _flushPendingTags(self, pending: _PendingTags) -> list[Node]:
		result: list[Node] = []
		if pending.usages:
			result.extend(self._tag_nodes(pending.usages))
			pending.usages.clear()
		if pending.labels:
			result.extend(self._tag_nodes(pending.labels))
			pending.labels.clear()
		return result

	def _related(self, refs: list[P.Ref]) -> list[Node]:
		if not refs:
			return []
		children: list[Node] = [Text("Related: ")]
		for i, ref in enumerate(refs):
			if i > 0:
				children.append(Text(" | "))
			children.append(Link(ref.target, [Text(ref.text)]))
		return [Block({}, children)]

	# -----------------------------------------------------------------------
	# Citations and senses
	# -----------------------------------------------------------------------

	def _example_cit(self, example: P.ExampleCit) -> list[Node]:
		result: list[Node] = []
		# <usg> and <lbl> describe the example, so they share its first quote.
		if example.quotes:
			result.append(self._block(example.quotes[0], example.tags))
			result.extend(self._block(quote) for quote in example.quotes[1:])
		elif example.tags:
			result.append(Block({}, self._tag_nodes(example.tags)))
		# <note> holds the translation of the example, so it follows the quote.
		result.extend(Block({}, self._inline_nodes(note)) for note in example.notes)
		for subCit in example.subCits:
			result.extend(self._example_cit(subCit))
		return result

	def _trans_cit(
		self,
		transCit: P.TransCit,
		prefix: list[P.Tag] | None = None,
	) -> list[Node]:
		result: list[Node] = []
		blocks = transCit.blocks
		if prefix and not blocks:
			result.extend(self._tag_nodes(prefix))

		if len(blocks) == 1:
			result.append(self._block(blocks[0], prefix))
		elif blocks:
			items: list[list[Node]] = []
			for i, block in enumerate(blocks):
				items.append([self._block(block, prefix if i == 0 else None)])
			result.append(ListBlock(True, items))

		if self._senseHasContent(transCit.rest):
			result.extend(self._sense(transCit.rest))
		return result

	@staticmethod
	def _senseHasContent(sense: P.Sense) -> bool:
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

	def _trans_cits(
		self,
		transCits: list[P.TransCit],
		pending: _PendingTags,
	) -> list[Node]:
		def process(transCit: P.TransCit) -> list[Node]:
			# Only the first translation <cit> takes the pending usage tags,
			# so they share its line.
			prefix = list(pending.usages)
			pending.usages.clear()
			return self._trans_cit(transCit, prefix)

		return self._make_list(transCits, process, single_prefix="")

	def _sense_sense(
		self,
		sense: P.Sense,
		*,
		topLevel: bool = False,
		pending: _PendingTags | None = None,
	) -> list[Node]:
		if pending is None:
			pending = _PendingTags(list(sense.usages), list(sense.labels))

		result: list[Node] = []
		# First-level senses have their grammar formatted by _sense already.
		if not topLevel:
			result.extend(self._gram_groups(sense.gramGroups))

		for lang in sense.langs:
			if not lang.desc:
				continue
			text = f"{lang.desc}: {lang.text}" if lang.text else lang.desc
			result.append(Text(text))

		if sense.defs:
			result.extend(self._flushPendingTags(pending))
		result.extend(self._make_list(sense.defs, self._inline_nodes))
		if sense.grams:
			result.extend(self._grams(sense.grams, pending))
		if sense.notes:
			result.extend(self._flushPendingTags(pending))
		result.extend(self._make_list(sense.notes, self._inline_nodes))
		if sense.transCits:
			result.extend(self._trans_cits(sense.transCits, pending))
		result.extend(self._flushPendingTags(pending))
		result.extend(self._related(sense.refs))
		result.extend(Block({}, self._inline_nodes(xr)) for xr in sense.xrList)
		result.extend(
			Example(self._example_cit(example)) for example in sense.exampleCits
		)
		return result

	def _sense(self, sense: P.Sense) -> list[Node]:
		result = self._gram_groups(sense.gramGroups)
		# Write this sense's own content first, then its sub-senses in document
		# order, so a sub-sense never precedes its parent's text.
		result.extend(self._sense_sense(sense, topLevel=True))
		result.extend(
			self._make_list(
				sense.subSenses,
				lambda subSense: [Block({}, self._sense_sense(subSense))],
				single_prefix="",
			),
		)
		return result

	@staticmethod
	def _senseIsRTL(sense: P.Sense) -> bool:
		if sense.lang is None:
			return False
		langObj = langDict[sense.lang]
		if langObj is None:
			log.warning(f"unknown language {sense.lang}")
			return False
		return bool(langObj.rtl)

	def _sense_list(self, senseList: list[P.Sense]) -> list[Node]:
		if not senseList:
			return []
		if self._auto_rtl and self._senseIsRTL(senseList[0]):
			return [
				Block(
					{"dir": "rtl"},
					self._make_list(
						senseList,
						self._sense,
						ordered=(len(senseList) > 3),
					),
				),
			]
		return self._make_list(senseList, self._sense)

	def build(self, entry: P.Entry) -> list[Node]:
		result: list[Node] = []
		if self._word_title:
			result.extend(Title(keyword) for keyword in entry.keywords)
		if entry.pronunciations:
			separators = [self.getCommaSep(pron) for pron in entry.pronunciations[1:]]
			result.append(Pronunciation(entry.pronunciations, separators))
		if entry.usages:
			result.extend(self._tag_nodes(entry.usages))
		if entry.labels:
			result.extend(self._tag_nodes(entry.labels))
		result.extend(self._gram_groups(entry.gramGroups))
		result.extend(self._sense_list(entry.senses))
		return result


def buildDocument(entry: P.Entry, owner: Any) -> list[Node]:
	"""Build the neutral document tree for a parsed FreeDict entry."""
	return _Builder(owner).build(entry)
