"""
Format neutral FreeDict documents as Markdown.

:class:`MdFormatter` implements the generic formatter node methods with
Markdown output. It owns all Markdown syntax and list/blockquote layout.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

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


__all__ = ["MdFormatter"]

_LIST_LINE_RE = re.compile(r"^\t*(?:\d+\.|-\s)")


def _md_url(url: str) -> str:
	return quote(url, safe="/:?#[]@!$&'()*+,;=%._~-")


class MdFormatter(Formatter):
	"""Format a neutral FreeDict document as a Markdown definition."""

	defiFormat = "m"

	def __init__(self, owner: Any) -> None:
		super().__init__(owner)
		self._parts: list[str] = []
		self._bufs: list[list[str]] | None = None
		self._list_levels: list[dict[str, Any]] = []

	def formatDocument(self, document: Sequence[Node]) -> str:
		self._parts = []
		self._bufs = None
		self._list_levels = []
		self._writeNodes(document)
		s = "".join(self._parts)
		s = re.sub(r"[ \t]+\n", "\n", s)
		s = re.sub(r"\n{3,}", "\n\n", s)
		return s.strip()

	def _effective_append(self, s: str) -> None:
		if self._bufs is None:
			self._parts.append(s)
		else:
			self._bufs[-1].append(s)

	def _appendText(self, text: str) -> None:
		self._effective_append(text.replace("\xa0", " "))

	def _writeText(self, text: Text) -> None:
		self._appendText(text.text)

	def _writeLineBreak(self) -> None:
		self._effective_append("\n")

	def _writeLink(self, link: Link) -> None:
		self._bufs = self._bufs or []
		self._bufs.append([])
		try:
			self._writeNodes(link.children)
		finally:
			buf_list = self._bufs.pop()
			if not self._bufs:
				self._bufs = None
			label = "".join(buf_list).replace("\xa0", " ").strip()
			href = linkTarget(link)
			self._effective_append(f"[{label}]({_md_url(href)})")

	def _writeTag(self, tag: Tag) -> None:
		self._effective_append("**[")
		self._writeNodes(tag.children)
		self._effective_append("]**")

	def _writeGrammar(self, grammar: Grammar) -> None:
		self._effective_append("*")
		self._appendText(grammar.text)
		self._effective_append("*")

	def _writeInlineElement(self, element: InlineElement) -> None:
		tag = element.tag.lower()
		if tag == "p":
			self._effective_append("\n\n")
			self._writeNodes(element.children)
			self._effective_append("\n\n")
			return
		if tag == "div":
			self._writeDiv(element.attrib, element.children)
			return
		if tag == "span" and "tag" in (element.attrib.get("class") or "").split():
			self._effective_append("**")
			self._writeNodes(element.children)
			self._effective_append("**")
			return
		self._writeNodes(element.children)

	def _writeDiv(self, attrib: dict[str, str], children: Sequence[Node]) -> None:
		if "example" in (attrib.get("class") or "").split():
			self._writeBlockquote(children)
			return
		if attrib.get("dir") == "rtl":
			self._effective_append("\n")
			self._writeNodes(children)
			self._effective_append("\n")
			return
		self._writeNodes(children)

	def _writeBlock(self, block: Block) -> None:
		self._writeDiv(block.attrib, block.children)

	def _writeListBlock(self, listBlock: ListBlock) -> None:
		self._list_levels.append(
			{"ordered": listBlock.ordered, "next": 1 if listBlock.ordered else 0},
		)
		if self._parts and self._parts[-1] not in {"\n", "\n\n"}:
			self._effective_append("\n")
		for item in listBlock.items:
			self._writeListItem(item)
		self._list_levels.pop()
		self._effective_append("\n")

	def _writeListItem(self, item: Sequence[Node]) -> None:  # noqa: PLR0912
		level = len(self._list_levels)
		if not level:
			self._writeNodes(item)
			return

		meta = self._list_levels[-1]
		start = len(self._parts)

		self._writeNodes(item)

		raw = "".join(self._parts[start:])
		del self._parts[start:]
		block = raw.strip("\n")

		tabs = "\t" * max(0, level - 1)
		if meta["ordered"]:
			n = meta["next"]
			meta["next"] = n + 1
			head = f"{tabs}{n}. "
		else:
			head = f"{tabs}- "

		if not block:
			self._effective_append(head + "\n")
			return

		lines = block.split("\n")
		split_at = len(lines)
		for i, ln in enumerate(lines):
			if _LIST_LINE_RE.match(ln):
				split_at = i
				break

		plain = lines[:split_at]
		nested = lines[split_at:]
		cont_tab = tabs + "\t"

		if plain:
			self._effective_append(head + plain[0] + "\n")
			for ln in plain[1:]:
				if _LIST_LINE_RE.match(ln):
					self._effective_append(ln + "\n")
				else:
					self._effective_append(cont_tab + ln + "\n")
		else:
			self._effective_append(head + "\n")

		for ln in nested:
			if _LIST_LINE_RE.match(ln):
				self._effective_append(ln + "\n")
			else:
				self._effective_append(cont_tab + ln + "\n")

	def _writeBlockquote(self, children: Sequence[Node]) -> None:
		self._bufs = self._bufs or []
		self._bufs.append([])
		try:
			self._writeNodes(children)
		finally:
			buf_list = self._bufs.pop()
			body = "" if not buf_list else "".join(buf_list).strip()
			if not self._bufs:
				self._bufs = None
			if body:
				if self._parts and not self._parts[-1].endswith("\n"):
					self._effective_append("\n")
				for ln in body.splitlines() or [" "]:
					line = "> " + ln.strip()
					self._effective_append(line + "\n")

	def _writeExample(self, example: Example) -> None:
		self._writeBlockquote(example.children)

	def _writePronunciation(self, pronunciation: Pronunciation) -> None:
		for i, pron in enumerate(pronunciation.items):
			if i > 0:
				self._effective_append(pronunciation.separators[i - 1])
			self._effective_append("/")
			self._appendText(pron)
			self._effective_append("/")
		self._writeLineBreak()
		self._effective_append("\n")

	def _writeTitle(self, title: Title) -> None:
		titleTag = self._owner._glos.titleTag(title.text)
		if titleTag in {"b", "strong"}:
			self._effective_append("**")
			self._appendText(title.text)
			self._effective_append("**")
		elif titleTag == "big":
			self._effective_append("## ")
			self._appendText(title.text)
			self._effective_append("\n")
		else:
			self._appendText(title.text)
		self._writeLineBreak()
