"""
Format neutral FreeDict documents as XDXF markup.

:class:`XdxfFormatter` implements the generic formatter node methods with
XDXF tags. The result is an XDXF article body (without the ``<k>`` headwords,
which PyGlossary stores separately) that can be read back by the XDXF plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from xml.sax.saxutils import escape, quoteattr

from .formatter import Formatter, linkTarget

if TYPE_CHECKING:
	from collections.abc import Sequence

	from .document import (
		Block,
		Example,
		Grammar,
		InlineElement,
		Link,
		ListBlock,
		Node,
		Pronunciation,
		Tag,
		Text,
		Title,
	)


__all__ = ["XdxfFormatter"]

_INLINE_TAGS = frozenset({"b", "i", "u", "sub", "sup", "tt", "big", "small", "span"})
_BWORD_PREFIX = "bword://"


class XdxfFormatter(Formatter):
	"""Format a neutral FreeDict document as an XDXF definition."""

	defiFormat = "x"

	def __init__(self, owner: Any) -> None:
		super().__init__(owner)
		self._parts: list[str] = []

	@property
	def _usage_color(self) -> str:
		return cast("str", self._owner._usage_color)

	@property
	def _label_color(self) -> str:
		return cast("str", self._owner._label_color)

	def formatDocument(self, document: Sequence[Node]) -> str:
		self._parts = []
		self._writeNodes(document)
		result = "".join(self._parts).strip()
		while result.startswith("<br/>"):
			result = result[len("<br/>") :].lstrip()
		while result.endswith("<br/>"):
			result = result[: -len("<br/>")].rstrip()
		return result

	def _write(self, text: str) -> None:
		self._parts.append(text)

	def _beginBlock(self) -> None:
		if not self._parts:
			return
		last = self._parts[-1]
		if last.endswith(("<br/>", "<def>", "<ex>")):
			return
		if last.startswith(("<div", "<p")) and last.endswith(">"):
			return
		self._write("<br/>")

	def _writeText(self, text: Text) -> None:
		self._write(escape(text.text))

	def _writeLineBreak(self) -> None:
		self._write("<br/>")

	def _writeLink(self, link: Link) -> None:
		target = linkTarget(link)
		if target.startswith(_BWORD_PREFIX):
			keyword = target[len(_BWORD_PREFIX) :]
			self._write(f"<kref k={quoteattr(keyword)}>")
			self._writeNodes(link.children)
			self._write("</kref>")
			return
		self._write(f"<iref href={quoteattr(target)}>")
		self._writeNodes(link.children)
		self._write("</iref>")

	def _writeTag(self, tag: Tag) -> None:
		color = self._label_color if tag.kind == "label" else self._usage_color
		classAttr = f" class={quoteattr(tag.kind)}"
		if color:
			self._write(f"<c{classAttr} c={quoteattr(color)}>[")
		else:
			self._write(f"<c{classAttr}>[")
		self._writeNodes(tag.children)
		self._write("]</c>")

	def _writeGrammar(self, grammar: Grammar) -> None:
		self._write("<gr>")
		self._write(escape(grammar.text))
		self._write("</gr>")

	def _writeInlineElement(self, element: InlineElement) -> None:
		attrib = "".join(
			f" {key}={quoteattr(value)}" for key, value in element.attrib.items()
		)
		if element.tag in {"p", "div"}:
			self._write(f"<{element.tag}{attrib}>")
			self._writeNodes(element.children)
			self._write(f"</{element.tag}>")
			return
		if element.tag not in _INLINE_TAGS:
			self._writeNodes(element.children)
			return
		self._write(f"<{element.tag}{attrib}>")
		self._writeNodes(element.children)
		self._write(f"</{element.tag}>")

	def _writeBlock(self, block: Block) -> None:
		if block.attrib:
			attrib = "".join(
				f" {key}={quoteattr(value)}" for key, value in block.attrib.items()
			)
			self._write(f"<div{attrib}>")
			self._writeNodes(block.children)
			self._write("</div>")
		else:
			self._beginBlock()
			self._writeNodes(block.children)

	def _writeListBlock(self, listBlock: ListBlock) -> None:
		self._write("<def>")
		for item in listBlock.items:
			self._write("<def>")
			self._writeNodes(item)
			self._write("</def>")
		self._write("</def>")

	def _writeExample(self, example: Example) -> None:
		self._write("<ex>")
		self._writeNodes(example.children)
		self._write("</ex>")

	def _writePronunciation(self, pronunciation: Pronunciation) -> None:
		self._write("<tr>")
		for i, pron in enumerate(pronunciation.items):
			if i > 0:
				self._write(escape(pronunciation.separators[i - 1]))
			self._write(escape(pron))
		self._write("</tr>")

	def _writeTitle(self, title: Title) -> None:
		titleTag = self._owner._glos.titleTag(title.text)
		if titleTag in {"b", "strong"}:
			self._write("<b>")
			self._write(escape(title.text))
			self._write("</b>")
		elif titleTag == "big":
			self._write("<big>")
			self._write(escape(title.text))
			self._write("</big>")
		else:
			self._write(escape(title.text))
		self._write("<br/>")
