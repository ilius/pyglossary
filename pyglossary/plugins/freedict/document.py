"""
Neutral document tree shared by the FreeDict formatters.

These nodes describe dictionary output only in terms of generic concepts:
inline text, links, tags, grammar, blocks, lists, examples, titles and
pronunciations. They contain no TEI knowledge, so the HTML and Markdown
formatters only have to map the nodes to their output syntax.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence

__all__ = [
	"Block",
	"Example",
	"Grammar",
	"Inline",
	"InlineElement",
	"LineBreak",
	"Link",
	"ListBlock",
	"Node",
	"Pronunciation",
	"Tag",
	"Text",
	"Title",
]


@dataclass(slots=True)
class Text:
	text: str


@dataclass(slots=True)
class LineBreak:
	pass


@dataclass(slots=True)
class Link:
	target: str | None
	children: Sequence[Inline]


@dataclass(slots=True)
class Tag:
	"""A usage or label tag, formatted as a colored badge."""

	kind: str
	children: Sequence[Inline]


@dataclass(slots=True)
class Grammar:
	"""One grammar word, formatted in the grammar style."""

	text: str


@dataclass(slots=True)
class InlineElement:
	"""Transparent inline element such as ``<p>``, ``<div>`` or ``<span>``."""

	tag: str
	attrib: dict[str, str]
	children: Sequence[Inline]


Inline = Text | LineBreak | Link | Tag | Grammar | InlineElement


@dataclass(slots=True)
class Block:
	attrib: dict[str, str] = field(default_factory=dict)
	children: Sequence[Node] = field(default_factory=list)


@dataclass(slots=True)
class ListBlock:
	"""A list whose items each hold a sequence of block or inline nodes."""

	ordered: bool
	items: Sequence[Sequence[Node]]


@dataclass(slots=True)
class Example:
	children: Sequence[Node] = field(default_factory=list)


@dataclass(slots=True)
class Pronunciation:
	items: list[str]
	separators: list[str]


@dataclass(slots=True)
class Title:
	text: str


Node = Inline | Block | ListBlock | Example | Pronunciation | Title
