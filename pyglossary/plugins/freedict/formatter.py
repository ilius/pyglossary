"""
Format neutral FreeDict documents.

The :class:`Formatter` walks the generic nodes from
:mod:`pyglossary.plugins.freedict.document` and dispatches them to output
methods. It contains no TEI or HTML knowledge; concrete formatters implement
the node methods and choose which ``defiFormat`` they produce.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .document import (
	Block,
	Example,
	Grammar,
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
	from collections.abc import Sequence


__all__ = ["Formatter", "linkTarget"]


class Formatter:
	"""Shared traversal of the neutral document tree."""

	defiFormat = ""

	def __init__(self, owner: Any) -> None:
		self._owner = owner

	def formatDocument(
		self,
		document: Sequence[Node],
	) -> str:
		raise NotImplementedError

	def _writeNodes(
		self,
		nodes: Sequence[Node],
	) -> None:
		for node in nodes:
			self._writeNode(node)

	def _writeNode(  # noqa: PLR0912
		self,
		node: Node,
	) -> None:
		if isinstance(node, Text):
			self._writeText(node)
		elif isinstance(node, LineBreak):
			self._writeLineBreak()
		elif isinstance(node, Link):
			self._writeLink(node)
		elif isinstance(node, Tag):
			self._writeTag(node)
		elif isinstance(node, Grammar):
			self._writeGrammar(node)
		elif isinstance(node, InlineElement):
			self._writeInlineElement(node)
		elif isinstance(node, Block):
			self._writeBlock(node)
		elif isinstance(node, ListBlock):
			self._writeListBlock(node)
		elif isinstance(node, Example):
			self._writeExample(node)
		elif isinstance(node, Pronunciation):
			self._writePronunciation(node)
		elif isinstance(node, Title):
			self._writeTitle(node)
		else:
			raise TypeError(f"unknown document node: {node!r}")

	def _writeText(self, text: Text) -> None:
		raise NotImplementedError

	def _writeLineBreak(self) -> None:
		raise NotImplementedError

	def _writeLink(self, link: Link) -> None:
		raise NotImplementedError

	def _writeTag(self, tag: Tag) -> None:
		raise NotImplementedError

	def _writeGrammar(self, grammar: Grammar) -> None:
		raise NotImplementedError

	def _writeInlineElement(self, element: InlineElement) -> None:
		raise NotImplementedError

	def _writeBlock(self, block: Block) -> None:
		raise NotImplementedError

	def _writeListBlock(self, listBlock: ListBlock) -> None:
		raise NotImplementedError

	def _writeExample(self, example: Example) -> None:
		raise NotImplementedError

	def _writePronunciation(self, pronunciation: Pronunciation) -> None:
		raise NotImplementedError

	def _writeTitle(self, title: Title) -> None:
		raise NotImplementedError


def linkTarget(link: Link) -> str:
	"""Target of a link, generating an internal target when missing."""
	target = link.target
	if target:
		return target
	return f"bword://{''.join(_nodeText(n) for n in link.children)}"


def _nodeText(node: Node) -> str:
	"""Plain text of a node, used for generated internal link targets."""
	if isinstance(node, Text):
		return node.text
	if isinstance(node, Grammar):
		return node.text
	if isinstance(node, (Link, Tag, InlineElement)):
		return "".join(_nodeText(child) for child in node.children)
	return ""
