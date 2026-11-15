"""
Format neutral FreeDict documents as HTML.

:class:`HtmlFormatter` implements the generic formatter node methods with
lxml ``htmlfile`` output. It owns all HTML tag and attribute decisions.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

from .formatter import Formatter, linkTarget

if TYPE_CHECKING:
	from collections.abc import Sequence

	from pyglossary.stubs.lxml_types import T_htmlfile

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


__all__ = ["HtmlFormatter"]


class HtmlFormatter(Formatter):
	"""Format a neutral FreeDict document as an HTML definition."""

	defiFormat = "h"

	gramClass = "grammar"
	tagStyle = (
		"color:white;"
		"background:{};"
		"padding-left:3px;"
		"padding-right:3px;"
		"border-radius:0.5ex;"
	)

	def __init__(self, owner: Any) -> None:
		super().__init__(owner)
		self._hf: T_htmlfile

	@property
	def _pron_color(self) -> str:
		return cast("str", self._owner._pron_color)

	@property
	def _gram_color(self) -> str:
		return cast("str", self._owner._gram_color)

	@property
	def _usage_color(self) -> str:
		return cast("str", self._owner._usage_color)

	@property
	def _label_color(self) -> str:
		return cast("str", self._owner._label_color)

	@property
	def _example_padding(self) -> int:
		return cast("int", self._owner._example_padding)

	def formatDocument(self, document: Sequence[Node]) -> str:
		from lxml import etree as ET

		buff = BytesIO()
		with ET.htmlfile(buff, encoding="utf-8") as hf:
			self._hf = cast("T_htmlfile", hf)
			with self._hf.element("div"):
				self._writeNodes(document)
		return buff.getvalue().decode("utf-8")

	def _writeText(self, text: Text) -> None:
		self._hf.write(text.text)

	def _writeLineBreak(self) -> None:
		from lxml import etree as ET

		self._hf.write(ET.Element("br"))

	def _writeLink(self, link: Link) -> None:
		target = linkTarget(link)
		attrib: dict[str, str] = {}
		if link.target and "://" in link.target:
			attrib["class"] = "external"
		with self._hf.element("a", href=target, attrib=attrib):
			self._writeNodes(link.children)

	def _writeTag(self, tag: Tag) -> None:
		color = self._label_color if tag.kind == "label" else self._usage_color
		style = self.tagStyle.format(color or "transparent")
		with self._hf.element("span", attrib={"class": "tag", "style": style}):
			self._hf.write("[")
			self._writeNodes(tag.children)
			self._hf.write("]")

	def _writeGrammar(self, grammar: Grammar) -> None:
		attrib = {"class": self.gramClass}
		if self._gram_color:
			attrib["color"] = self._gram_color
		with self._hf.element("font", attrib=attrib):
			self._hf.write(grammar.text)

	def _writeInlineElement(self, element: InlineElement) -> None:
		with self._hf.element(element.tag, attrib=dict(element.attrib)):
			self._writeNodes(element.children)

	def _writeBlock(self, block: Block) -> None:
		with self._hf.element("div", attrib=dict(block.attrib)):
			self._writeNodes(block.children)

	def _writeListBlock(self, listBlock: ListBlock) -> None:
		with self._hf.element("ol" if listBlock.ordered else "ul"):
			for item in listBlock.items:
				with self._hf.element("li"):
					self._writeNodes(item)

	def _writeExample(self, example: Example) -> None:
		with self._hf.element(
			"div",
			attrib={
				"class": "example",
				"style": f"padding: {self._example_padding}px 0px;",
			},
		):
			self._writeNodes(example.children)

	def _writePronunciation(self, pronunciation: Pronunciation) -> None:
		for i, pron in enumerate(pronunciation.items):
			if i > 0:
				self._hf.write(pronunciation.separators[i - 1])
			self._hf.write("/")
			with self._hf.element("font", color=self._pron_color):
				self._hf.write(pron)
			self._hf.write("/")
		self._writeLineBreak()
		self._hf.write("\n")

	def _writeTitle(self, title: Title) -> None:
		from lxml import etree as ET

		titleTag = self._owner._glos.titleTag(title.text)
		if titleTag:
			with self._hf.element(titleTag):
				self._hf.write(title.text)
		else:
			self._hf.write(title.text)
		self._hf.write(ET.Element("br"))
