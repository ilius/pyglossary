"""
Transform XDXF definitions using a pure-Python event-driven engine.

``XdxfTransformer`` converts XDXF markup (keywords, examples, images, etc.) to
HTML without an XSLT engine — a fallback when ``lxml`` XSLT is unavailable.

The article XML is walked as a flat stream of events (open tag, text, close
tag) and fed to a small state machine, the same pattern as the DSL
transformer. Every event is handled explicitly, so there is no recursive
element-walk bookkeeping:

- text is written verbatim; HTML renderers collapse runs of whitespace like a
  browser, so spaces between inline tags are preserved
- newline becomes ``<br/>`` (or a space in inline contexts such as ``<ex>``)
- leading whitespace after a block-level element is dropped, since a browser
  ignores it there anyway
- inline formatting uses plain ``<font>``/``<b>``/``<i>`` tags so the output
  also renders in limited HTML widgets that do not support CSS

This module is used in plugins.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from urllib.parse import quote
from xml.sax.saxutils import escape, quoteattr

from lxml import etree as ET

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.stubs.lxml_types import Element

log = logging.getLogger("pyglossary")

__all__ = [
	"XdxfTransformer",
]

_GRAM_COLOR = "green"
_EX_STYLE = "margin: 0px 0px 0px 20px; color: #888888;"

# XDXF tags whose output is a block-level HTML element (or ends with a line
# break). A browser ignores leading whitespace after such elements, so we
# collapse it instead of turning it into a redundant ``<br/>``.
_BLOCK_TAGS = frozenset(
	{
		"k",
		"def",
		"ex",
		"blockquote",
		"sr",
		"gr",
		"tr",
		"br",
	},
)

# Tags whose content is inline text, where newlines render as spaces.
_SPACE_NEWLINE_TAGS = frozenset(
	{
		"ex",
		"deftext",
		"categ",
		"iref",
	},
)

_OPEN_HTML = {
	"u": "<u>",
	"i": "<i>",
	"b": "<b>",
	"sub": "<sub>",
	"sup": "<sup>",
	"tt": "<tt>",
	"big": "<big>",
	"small": "<small>",
	"blockquote": '<div class="m">',
	"sr": '<div class="sr">',
	"ex": f'<div class="example" style="{_EX_STYLE}">',
	"k": '<div class="k"><b>',
	"mrkd": '<span class="mrkd"><b>',
	"pos": '<span class="pos"><font color="green"><i>',
	"abr": '<span class="abr"><font color="green"><i>',
	"co": '<span class="co">(',
	"abbr": "<i>",
	"categ": '<span style="background-color: green;">',
	"span": "<span>",
	"ex_orig": "<i>",
	"ex_tran": "<i>",
	"ex_transl": "<i>",
	"gr": f'<font color="{_GRAM_COLOR}">',
	"opt": " (",
	"tr": "[",
	"br": "<br/>",
}

_HREF_SAFE = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"


def _urlencode(value: str) -> str:
	"""
	Percent-encode ``value`` for use in an ``href``.

	Matches lxml's HTML serializer, so ``py_transform`` output matches the XSL
	transform: spaces become ``%20`` and non-ASCII bytes are UTF-8-encoded,
	while printable ASCII (including ``/``, ``:``, ``?``, ``#``) is preserved.
	"""
	return quote(value, safe=_HREF_SAFE)


_CLOSE_HTML = {
	"u": "</u>",
	"i": "</i>",
	"b": "</b>",
	"sub": "</sub>",
	"sup": "</sup>",
	"tt": "</tt>",
	"big": "</big>",
	"small": "</small>",
	"blockquote": "</div>",
	"sr": "</div>",
	"ex": "</div>",
	"k": "</b></div>",
	"mrkd": "</b></span>",
	"pos": "</i></font></span>",
	"abr": "</i></font></span>",
	"co": ")</span>",
	"abbr": "</i>",
	"categ": "</span>",
	"span": "</span>",
	"ex_orig": "</i>",
	"ex_tran": "</i>",
	"ex_transl": "</i>",
	"gr": "</font><br/>",
	"opt": ")",
	"tr": "]<br/>",
}


@dataclass(slots=True)
class _StackItem:
	tag: str
	lastBlock: bool
	payload: str | dict[str, str] = ""


@dataclass(slots=True)
class _StartEvent:
	tag: str
	attrs: dict[str, str]
	elem: Element


@dataclass(slots=True)
class _TextEvent:
	text: str


@dataclass(slots=True)
class _EndEvent:
	tag: str


def _iter_events(
	elem: Element,
) -> Iterator[_StartEvent | _TextEvent | _EndEvent]:
	"""
	Yield events in document order for ``elem``.

	Three kinds of events are yielded: ``_StartEvent`` (with tag, attrs and
	element), ``_TextEvent`` (with the text) and ``_EndEvent`` (with the tag).
	"""
	yield _StartEvent(
		tag=elem.tag,
		attrs=cast("dict[str, str]", elem.attrib),
		elem=elem,
	)
	if elem.text:
		yield _TextEvent(text=elem.text)
	for child in elem:
		yield from _iter_events(child)
		if child.tail:
			yield _TextEvent(text=child.tail)
	yield _EndEvent(tag=elem.tag)


class XdxfTransformer:
	"""Xdxf Transformer."""

	_gram_color: str = _GRAM_COLOR
	_ex_style: str = _EX_STYLE

	def __init__(self, encoding: str = "utf-8") -> None:
		self._encoding = encoding
		# state, reset by ``transform``:
		self._out: list[str] = []
		self._stack: list[_StackItem] = []
		self._buf: str | None = None

	@staticmethod
	def tostring(elem: Element) -> str:
		return (
			ET.tostring(
				elem,
				method="html",
				pretty_print=True,
			)
			.decode("utf-8")
			.strip()
		)

	def _writeSep(self, parentTag: str) -> None:
		self._out.append("<br/>" if parentTag not in _SPACE_NEWLINE_TAGS else " ")

	def _onText(self, text: str) -> None:
		item = self._stack[-1]
		if item.lastBlock:
			text = text.lstrip()
		if text.startswith("\n"):
			self._writeSep(item.tag)
			text = text.lstrip("\n")
		lines = [line for line in text.split("\n") if line]
		for index, line in enumerate(lines):
			if index > 0:
				self._writeSep(item.tag)
			if self._buf is not None:
				self._buf += line
			else:
				self._out.append(escape(line))
		item.lastBlock = False

	def _onDefStart(self, tag: str, elem: Element) -> None:
		hasNested = any(c.tag == "def" for c in elem)
		hasDeftext = any(c.tag == "deftext" for c in elem)
		parentTag = self._stack[-1].tag if self._stack else ""
		if parentTag == "ar":
			openHtml, closeHtml = ("<ol>", "</ol>") if hasNested else ("<div>", "</div>")
		elif hasDeftext:
			openHtml, closeHtml = "<li>", "</li>"
		elif hasNested:
			openHtml, closeHtml = "<li><ol>", "</ol></li>"
		else:
			openHtml, closeHtml = "<li>", "</li>"
		self._out.append(openHtml)
		self._stack.append(
			_StackItem(
				tag=tag,
				lastBlock=True,
				payload=closeHtml,
			)
		)

	def _onStart(self, tag: str, attrs: dict[str, str], elem: Element) -> None:
		if tag in {"kref", "iref"}:
			# buffer the link text so the href can fall back to it
			self._stack.append(
				_StackItem(
					tag=tag,
					lastBlock=False,
					payload=dict(attrs),
				)
			)
			self._buf = ""
			return
		if tag == "def":
			self._onDefStart(tag, elem)
			return
		if tag == "c":
			self._out.append(f'<font color="{attrs.get("c", self._gram_color)}">')
			self._stack.append(_StackItem(tag=tag, lastBlock=True, payload="</font>"))
			return
		if tag == "img":
			attrStr = "".join(
				f" {key}={quoteattr(value)}" for key, value in attrs.items()
			)
			self._out.append(f"<img{attrStr}/>")
			self._stack.append(_StackItem(tag=tag, lastBlock=False))
			return
		if tag in {"nu", "rref"}:
			# empty markers / skipped tags: render nothing
			self._stack.append(_StackItem(tag=tag, lastBlock=False))
			return
		openHtml = _OPEN_HTML.get(tag)
		if openHtml is not None:
			self._out.append(openHtml)
		self._stack.append(
			_StackItem(
				tag=tag,
				lastBlock=True,
				payload=_CLOSE_HTML.get(tag, ""),
			)
		)

	def _onEnd(self) -> None:
		item = self._stack.pop()
		if item.tag in {"kref", "iref"}:
			attrs = item.payload
			assert isinstance(attrs, dict)
			buf = self._buf or ""
			self._buf = None
			if item.tag == "kref":
				if not buf:
					log.warning("kref with no text")
				href = attrs.get("k", buf)
				self._out.append(
					'<a class="kref" href='
					f"{quoteattr('bword://' + _urlencode(href))}>{escape(buf)}</a>"
				)
			else:
				href = _urlencode(attrs.get("href", buf))
				if href.endswith((".mp3", ".wav", ".aac", ".ogg")):
					self._out.append(f'<a class="iref" href={quoteattr(href)}>🔊</a>')
				else:
					self._out.append(
						f'<a class="iref" href={quoteattr(href)}>{escape(buf)}</a>'
					)
			isBlock = False
		else:
			if isinstance(item.payload, str) and item.payload:
				self._out.append(item.payload)
			isBlock = item.tag in _BLOCK_TAGS
		if self._stack:
			self._stack[-1].lastBlock = isBlock

	def transform(self, article: Element) -> str:
		self._out = []
		self._stack = []
		self._buf = None
		for event in _iter_events(article):
			if isinstance(event, _StartEvent):
				self._onStart(event.tag, event.attrs, event.elem)
			elif isinstance(event, _TextEvent):
				self._onText(event.text)
			else:
				self._onEnd()
		return '<div class="article">' + "".join(self._out) + "</div>"

	def transformByInnerString(self, articleInnerStr: str) -> str:
		try:
			article = ET.fromstring(f"<ar>{articleInnerStr}</ar>")
		except Exception as e:
			log.error(f"ignoring bad xdxf: {articleInnerStr}\n{e}")
			return articleInnerStr

		return self.transform(article)
