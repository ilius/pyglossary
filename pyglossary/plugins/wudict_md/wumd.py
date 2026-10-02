# Copyright (C) 2026 glowinthedark
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
wudict markdown (WUDICT-MARKDOWN.md), independent of pyglossary.

A port of wudict's Go implementation (internal/format/wmd): it writes what Go
writes, byte for byte, and reads the entries Go reads; conformance.py checks it
against the Go code. HTML is tokenized and parsed as golang.org/x/net/html does
it, markdown by markdown-it-py (CommonMark and tables).
"""

from __future__ import annotations

import bisect
import gzip
import re
import sys
import unicodedata
import zlib
from html.entities import html5
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote_to_bytes

if TYPE_CHECKING:
	from collections.abc import Callable, Collection, Iterator

	from markdown_it import MarkdownIt
	from markdown_it.token import Token

__all__ = [
	"CHUNK_SIZE",
	"CleanError",
	"Document",
	"FormatError",
	"clean_body",
	"decode",
	"field_key",
	"heading_esc",
	"html_body",
	"load",
	"read_text",
	"repair_name",
]


class FormatError(Exception):
	"""A file this reader does not read (§8: E-format, E-version)."""

	def __init__(self, code: str, msg: str) -> None:
		super().__init__(f"wudict markdown: {code}: {msg}")
		self.code = code


class CleanError(Exception):
	"""A body `clean` mode cannot write (R6.8)."""

	def __init__(self, construct: str, reason: str) -> None:
		super().__init__(f"{construct} cannot be written as clean markdown: {reason}")


# ---------------------------------------------------------------------------
# Text, as Go's primitives see it

# unicode.IsSpace: str.isspace() without \x1c-\x1f.
_GO_SPACE = (
	"\t\n\v\f\r \x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007"
	"\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
)
_GO_FIELD = re.compile(f"[^{_GO_SPACE}]+")
_HSPACE = " \t\n\r\f"  # HTML whitespace
_HFIELD = re.compile("[^ \t\n\r\f]+")
_SURROGATES = re.compile("[\ud800-\udfff]")
_ESC = {
	ord("&"): "&amp;",
	ord("'"): "&#39;",
	ord("<"): "&lt;",
	ord(">"): "&gt;",
	ord('"'): "&#34;",
}
_XNET_ESC = _ESC | {ord("\r"): "&#13;"}


def go_fields(s: str) -> list[str]:
	"""strings.Fields."""
	return _GO_FIELD.findall(s)


def go_trim_space(s: str) -> str:
	"""strings.TrimSpace."""
	return s.strip(_GO_SPACE)


def squash(s: str) -> str:
	"""HTML whitespace runs as one space, trimmed."""
	return " ".join(_HFIELD.findall(s))


def go_html_escape(s: str) -> str:
	"""html.EscapeString."""
	return s.translate(_ESC)


def fold_eq_prefix(s: str, p: str) -> bool:
	"""Whether s starts with the lowercase ASCII p, ASCII case ignored."""
	h = s[: len(p)]
	return h.isascii() and h.lower() == p


def ascii_lower(s: str) -> str:
	return s.lower() if s.isascii() else re.sub("[A-Z]+", lambda m: m[0].lower(), s)


def go_lower(s: str) -> str:
	"""strings.ToLower: rune by rune, so a capital dotted I is i, a sigma never final."""
	return s.lower() if s.isascii() else "".join(c.lower()[0] for c in s)


def valid_text(s: str) -> str:
	"""
	R2.1 on a body: each byte of invalid UTF-8 (here a lone surrogate) and
	NUL become U+FFFD.
	"""
	return _SURROGATES.sub("\ufffd", s).replace("\x00", "\ufffd")


# ---------------------------------------------------------------------------
# Lookup links (R5) and destinations (R6.9)


def _pct(m: re.Match[str]) -> str:
	return "".join(f"%{b:02X}" for b in m[0].encode())


_TARGET_ENC = re.compile("[%#\x00-\x1f\x7f]|^@")
_PATH_ENC = re.compile("[%#?\x00-\x1f\x7f]")
_FRAG_ENC = re.compile("[%\x00-\x1f\x7f]")
_BAD_PCT = re.compile("%(?![0-9A-Fa-f]{2})")
_URL_SAFE = "!#$%&'()*+,/:;=?@"  # with quote()'s own, every byte a renderer keeps


def enc_target(s: str) -> str:
	"""R5.1: `%`, `#`, controls and a leading `@` percent-encoded."""
	return _TARGET_ENC.sub(_pct, s)


def dec(s: str) -> str:
	"""R5.2: percent-decoding to UTF-8, all or nothing."""
	if "%" not in s or _BAD_PCT.search(s):
		return s
	try:
		return unquote_to_bytes(s).decode()
	except UnicodeDecodeError:
		return s


def canon_ref(ref: str) -> str:
	"""htmlref.CanonRef: `bword:` and `entry://@` respelled (R6.5)."""
	if fold_eq_prefix(ref, "bword:"):
		rest = ref[6:].removeprefix("//")
	elif fold_eq_prefix(ref, "entry://@"):
		rest = ref[8:]
	else:
		return ref
	return ("entry:" if rest.startswith("@") else "entry://") + rest


def clean_ref(ref: str) -> str:
	"""htmlref.Clean: `href=x.ogg"` is x.ogg."""
	return ref.strip(" \t\n\r\f\v").rstrip("\"'`").strip(" \t\n\r\f\v")


def lookup_rest(href: str) -> str | None:
	"""The target and fragment of a lookup link (R5.2), or None."""
	for p in ("entry:", "bword:", "d:", "x:"):
		if fold_eq_prefix(href, p):
			rest = href[len(p) :]
			return rest[2:] if len(p) > 2 and rest.startswith("//") else rest
	return None


def scheme_ref(v: str) -> bool:
	"""Whether v starts with a URL scheme."""
	return re.match("[A-Za-z][A-Za-z0-9+.-]*:", v) is not None


def entry_ref(rest: str) -> str:
	"""The canonical lookup link to target[#fragment] (R6.9)."""
	target, sep, frag = rest.partition("#")
	if len(target) > 1 and target[0] == "@":
		out = "entry:@" + enc_target(dec(target[1:]))
	else:
		out = "entry://" + enc_target(dec(target).strip(" \t"))
	return out + "#" + _FRAG_ENC.sub(_pct, dec(frag)) if sep else out


# dict.IsAssetName: an href with one of these extensions names a file, any
# other relative href a headword (R5.4).
_ASSET_EXT = frozenset((
	".css", ".js", ".html", ".htm", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
	".bmp", ".ico", ".avif", ".mp3", ".ogg", ".oga", ".wav", ".spx", ".m4a", ".opus",
	".flac", ".aac", ".mp4", ".webm", ".ogv", ".mov", ".m4v", ".3gp", ".avi", ".wmv",
	".mkv", ".mpg", ".mpeg", ".asf", ".flv", ".pcx", ".dcx", ".wmf", ".emf", ".tif",
	".tiff", ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".json", ".xml", ".txt",
))  # fmt: skip
_QUERY = re.compile("[?#]")


def is_asset_name(ref: str) -> bool:
	seg = _QUERY.split(ref, maxsplit=1)[0].rpartition("/")[2]
	i = seg.rfind(".")
	return i >= 0 and seg[i:].lower() in _ASSET_EXT


def cross_ref(v: str) -> str | None:
	"""The lookup link a relative link href stands for (R5.4), or None."""
	v = v.strip(_HSPACE)
	if (
		not v
		or v[0] in "#?/"
		or scheme_ref(v)
		or is_asset_name(v)
		or fold_eq_prefix(v, "res/")
		or fold_eq_prefix(v, "assets/")
		or not dec(v.partition("#")[0]).strip(" \t")
	):
		return None
	return entry_ref(v)


def link_target(v: str) -> str:
	"""The canonical form of a link or media destination (R6.9)."""
	v = v.strip(_HSPACE)
	rest = lookup_rest(v)
	if rest is not None:
		return entry_ref(rest)
	if fold_eq_prefix(v, "sound://") or fold_eq_prefix(v, "file://"):
		v = v[v.index("//") + 2 :]
	if scheme_ref(v) or v.startswith("//"):
		return quote(v, safe=_URL_SAFE)
	m = _QUERY.search(v)
	path, suffix = (v[: m.start()], v[m.start() :]) if m else (v, "")
	return _PATH_ENC.sub(_pct, dec(path)) + quote(suffix, safe=_URL_SAFE)


def link_href(n: Node) -> str:
	"""The canonical destination of a link, "" when it has none."""
	href = n.attr("href") or ""
	ref = cross_ref(href)
	return ref if ref is not None else link_target(href)


def dest(v: str) -> str:
	"""A markdown link destination."""
	if v and not any(c <= " " or c == "\x7f" for c in v):
		return (
			v.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
			.replace("<", "\\<").replace("&", "\\&")
		)  # fmt: skip
	v = (
		v.replace("\\", "\\\\")
		.replace("<", "\\<")
		.replace(">", "\\>")
		.replace("&", "\\&")
	)
	return "<" + v.replace("\n", "%0A").replace("\r", "%0D") + ">"


# ---------------------------------------------------------------------------
# HTML tokens, as golang.org/x/net/html's Tokenizer cuts them

_REF = re.compile(r"&(?:#[xX]([0-9A-Fa-f]+)|#([0-9]+)|([A-Za-z0-9]+))(;?)")
_CP1252 = {x: bytes((x,)).decode("cp1252", "ignore") or chr(x) for x in range(0x80, 0xA0)}


def unescape(s: str, attr: bool = False) -> str:
	"""Character references in text or, attr, an attribute value."""
	if "&" not in s:
		return s

	def ref(m: re.Match[str]) -> str:
		hexa, deci, name, semi = m.groups()
		if name is None:
			x = int(hexa, 16) if hexa else int(deci)
			if 0x80 <= x <= 0x9F:
				return _CP1252[x]
			return "\ufffd" if x == 0 or 0xD800 <= x <= 0xDFFF or x > 0x10FFFF else chr(x)
		if attr and not semi and m.string[m.end() : m.end() + 1] == "=":
			return m[0]
		if (c := html5.get(name + semi)) is not None:
			return c
		if not attr:
			for j in range(min(len(name + semi) - 1, 6), 1, -1):
				if (c := html5.get(name[:j])) is not None:
					return c + name[j:] + semi
		return m[0]

	return _REF.sub(ref, s)


def newlines(s: str) -> str:
	return s.replace("\r\n", "\n").replace("\r", "\n")


START, END, TEXT, COMMENT, DOCTYPE, ERROR = range(6)
_RAW_TEXT = frozenset((
	"iframe", "noembed", "noframes", "noscript", "plaintext", "script", "style",
	"textarea", "title", "xmp",
))  # fmt: skip
_RCDATA = frozenset(("textarea", "title"))
_TOKEN = re.compile("<[A-Za-z!?/]")
_HSPACES = re.compile("[ \t\n\r\f]*")
_TAG_NAME = re.compile("[^ \t\n\r\f/>]*")
# An attribute: its name (a leading `=` is part of it), and a value double
# quoted (and its closing quote), single quoted (and its), or unquoted.
_ATTR = re.compile(
	"([^ \t\n\r\f/>][^ \t\n\r\f/>=]*)[ \t\n\r\f]*"
	"(?:=[ \t\n\r\f]*(?:\"([^\"]*)(\"?)|'([^']*)('?)|([^ \t\n\r\f>]*)))?"
)
_COMMENT_OPEN_END = re.compile("-*>")  # <!-->, <!--->
_COMMENT_END = re.compile("--!?>")
_RAW_END = {
	t: re.compile(f"</{t}[ \t\n\r\f/>]", re.IGNORECASE | re.ASCII) for t in _RAW_TEXT
}
# readScript's states: script data, escaped (in <!--), double escaped (in
# <!--<script>); an escaped `<` not starting a tag returns to script data.
# Only `-->` leaves them: `--!>` ends a comment, which these are not (HTML 13.2.5).
_SCRIPT = (
	re.compile("<!--|</script[ \t\n\r\f/>]", re.IGNORECASE | re.ASCII),
	re.compile(
		"-->|</script[ \t\n\r\f/>]|<script[ \t\n\r\f/>]|<(?![/A-Za-z])",
		re.IGNORECASE | re.ASCII,
	),
	re.compile("-->|</script[ \t\n\r\f/>]", re.IGNORECASE | re.ASCII),
)


class Tok:
	"""
	A token: its kind, s[start:end], and for a tag its name, attributes (a
	start tag's) and self-closing flag. A TEXT token's name is the raw-text
	element holding it.
	"""

	__slots__ = ("attrs", "end", "kind", "name", "self_closing", "start")

	def __init__(  # noqa: PLR0913
		self,
		kind: int,
		start: int,
		end: int,
		name: str = "",
		attrs: list[tuple[str, str]] | None = None,
		self_closing: bool = False,
	) -> None:
		self.kind, self.start, self.end = kind, start, end
		self.name, self.attrs, self.self_closing = name, attrs, self_closing


def _tag(s: str, i: int) -> tuple[int, str, list[tuple[str, str]], int] | None:
	"""
	Read a tag as x/net/html does, from its name at s[i]: its end, name,
	attributes (the first of each name) and the end of the last one's value;
	None at EOF.
	"""
	n = len(s)
	k = _TAG_NAME.match(s, i).end()
	name = ascii_lower(s[i:k])
	attrs: list[tuple[str, str]] = []
	seen: set[str] = set()
	vend = -1
	k = _HSPACES.match(s, k).end()
	while k < n:
		c = s[k]
		if c == ">":
			return k + 1, name, attrs, vend
		if c == "/":
			k = _HSPACES.match(s, k + 1).end()
			continue
		m = _ATTR.match(s, k)
		k = m.end()
		if k >= n or m[3] == "" or m[5] == "":  # EOF, or an unclosed quote
			return None
		key = ascii_lower(m[1])
		if key not in seen:
			seen.add(key)
			g = 2 if m[2] is not None else 4 if m[4] is not None else 6
			v = m[g] or ""
			if "&" in v or "\r" in v:
				v = unescape(newlines(v), attr=True)
			attrs.append((key, v))
			vend = m.end(g) if m[g] is not None else m.end(1)
		k = _HSPACES.match(s, k).end()
	return None


def _script_end(s: str, i: int) -> int:
	state = 0
	while m := _SCRIPT[state].search(s, i):
		t = m[0]
		if t == "<!--":
			state, i = 1, m.end() - 2  # its dashes may end it: <!-->
		elif t in ("-->", "<"):
			state, i = 0, m.end()
		elif t[1] != "/":
			state, i = 2, m.end()
		elif state == 2:
			state, i = 1, m.end()
		else:
			return m.start()
	return len(s)


def _close_angle(s: str, i: int) -> int:
	k = s.find(">", i)
	return len(s) if k < 0 else k + 1


def tokens(s: str, plain: Callable[[], bool] | None = None) -> Iterator[Tok]:  # noqa: PLR0912
	"""
	The tokens of s, as x/net/html cuts them. plain() is a tree builder
	saying the raw-text element just started is not one (foreign content).
	"""
	n, i = len(s), 0
	while i < n:
		m = _TOKEN.search(s, i)
		if m is None:
			yield Tok(TEXT, i, n)
			return
		j = m.start()
		if j > i:
			yield Tok(TEXT, i, j)
		c = s[j + 1]
		if c == "/":
			c = s[j + 2 : j + 3]
			if not c:
				yield Tok(TEXT, j, n)
				return
			if c == ">":
				i = j + 3
				yield Tok(COMMENT, j, i)
			elif c.isascii() and c.isalpha():
				t = _tag(s, j + 2)
				if t is None:
					yield Tok(ERROR, j, n)
					return
				i = t[0]
				yield Tok(END, j, i, t[1])
			else:
				i = _close_angle(s, j + 2)
				yield Tok(COMMENT, j, i)
		elif c == "!":
			if s.startswith("<!--", j):
				e = _COMMENT_OPEN_END.match(s, j + 4) or _COMMENT_END.search(s, j + 4)
				i = e.end() if e else n
				yield Tok(COMMENT, j, i)
			else:
				i = _close_angle(s, j + 2)
				doctype = (
					s[j + 2 : j + 9].isascii() and s[j + 2 : j + 9].lower() == "doctype"
				)
				yield Tok(DOCTYPE if doctype else COMMENT, j, i)
		elif c == "?":
			i = _close_angle(s, j + 2)
			yield Tok(COMMENT, j, i)
		else:
			t = _tag(s, j + 1)
			if t is None:
				yield Tok(ERROR, j, n)
				return
			i, name, attrs, vend = t
			sc = s[i - 2] == "/" and (not attrs or i - 2 != vend - 1)
			yield Tok(START, j, i, name, attrs, sc)
			if name in _RAW_TEXT and not (plain and plain()):
				if name == "plaintext":
					e = n
				elif name == "script":
					e = _script_end(s, i)
				else:
					e = ((m := _RAW_END[name].search(s, i)) and m.start()) or n
				if e > i:
					yield Tok(TEXT, i, e, name)
				i = e


# ---------------------------------------------------------------------------
# The tree x/net/html's ParseFragment (context <div>) builds, as far as the
# writer depends on it


MAX_OPEN = 512  # x/net/html refuses more open elements, its root included


class ParseError(Exception):
	"""HTML x/net/html does not parse."""


class Node:
	__slots__ = ("attrs", "children", "data", "kind", "parent", "tag")

	def __init__(
		self, kind: str, tag: str = "", attrs: list | None = None, data: str = ""
	) -> None:
		self.kind, self.tag, self.attrs, self.data = kind, tag, attrs or [], data
		self.children: list[Node] = []
		self.parent: Node | None = None

	def attr(self, key: str) -> str | None:
		for k, v in self.attrs:
			if k == key:
				return v
		return None


# A foreign (SVG, MathML) element is `svg` or `math`, or `#svg-` or `#math-`
# and its name, so no HTML rule matches it by name.
def _foreign(n: Node) -> bool:
	return n.tag in ("svg", "math") or n.tag.startswith(("#svg-", "#math-"))


def _integration(n: Node, tag: str | None) -> bool:
	"""
	A token that is HTML inside foreign element n: a start tag (tag) in an
	integration point, text (None) in an HTML one.
	"""
	if n.tag in ("#svg-foreignobject", "#svg-desc", "#svg-title"):
		return True
	if n.tag in ("#math-mi", "#math-mo", "#math-mn", "#math-ms", "#math-mtext"):
		return tag is not None and tag not in ("mglyph", "malignmark")
	if n.tag == "#math-annotation-xml":
		enc = (n.attr("encoding") or "").lower()
		return tag == "svg" or enc in ("text/html", "application/xhtml+xml")
	return False


_VOID = frozenset((
	"area", "base", "basefont", "bgsound", "br", "col", "embed", "frame", "hr", "img",
	"input", "keygen", "link", "meta", "param", "source", "track", "wbr",
))  # fmt: skip
_P_CLOSERS = frozenset((
	"address", "article", "aside", "blockquote", "center", "details", "dialog", "dir",
	"div", "dl", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
	"h4", "h5", "h6", "header", "hgroup", "hr", "main", "menu", "nav", "ol", "p", "pre",
	"search", "section", "summary", "table", "ul", "listing", "plaintext", "xmp", "li",
	"dd", "dt",
))  # fmt: skip
_HEADINGS = frozenset(("h1", "h2", "h3", "h4", "h5", "h6"))
_SPECIAL = frozenset((
	"address", "applet", "area", "article", "aside", "base", "basefont", "bgsound",
	"blockquote", "body", "br", "button", "caption", "center", "col", "colgroup", "dd",
	"details", "dir", "div", "dl", "dt", "embed", "fieldset", "figcaption", "figure",
	"footer", "form", "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head",
	"header", "hgroup", "hr", "html", "iframe", "img", "input", "keygen", "li", "link",
	"listing", "main", "marquee", "menu", "meta", "nav", "noembed", "noframes",
	"noscript", "object", "ol", "p", "param", "plaintext", "pre", "script", "section",
	"select", "source", "style", "summary", "table", "tbody", "td", "template",
	"textarea", "tfoot", "th", "thead", "title", "tr", "track", "ul", "wbr", "xmp",
	"#root", "#math-mi", "#math-mo", "#math-mn", "#math-ms", "#math-mtext",
	"#math-annotation-xml", "#svg-foreignobject", "#svg-desc", "#svg-title",
))  # fmt: skip
# What ends a scope: the default one, and those of list items, buttons, tables.
_SCOPE = frozenset((
	"applet", "caption", "html", "table", "td", "th", "marquee", "object", "template",
	"select", "#root", "#math-mi", "#math-mo", "#math-mn", "#math-ms", "#math-mtext",
	"#math-annotation-xml", "#svg-foreignobject", "#svg-desc", "#svg-title",
))  # fmt: skip
_LIST_SCOPE = _SCOPE | {"ol", "ul"}
_BUTTON_SCOPE = _SCOPE | {"button"}
_TABLE_SCOPE = frozenset(("html", "table", "template", "#root"))
# End tags that close an element in scope (WHATWG "in body").
_CLOSE_BLOCK = frozenset((
	"address", "article", "aside", "blockquote", "button", "center", "details", "dialog",
	"dir", "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup",
	"listing", "main", "menu", "nav", "ol", "pre", "search", "section", "select",
	"summary", "ul", "dd", "dt",
))  # fmt: skip
_TABLE_CTX = frozenset(("table", "tbody", "thead", "tfoot", "tr"))
_TBODY = ("tbody", "thead", "tfoot")
_TABLE_MODE = frozenset(("table", "tbody", "thead", "tfoot", "tr", "td", "th", "caption"))
_TABLE_END = _TABLE_MODE | {"col", "colgroup"}
_TABLE_OK = frozenset((
	"caption", "colgroup", "col", "tbody", "thead", "tfoot", "tr", "td", "th", "script",
	"style", "template", "form",
))  # fmt: skip
_TABLE_PART = frozenset(
	("tr", "td", "th", "tbody", "thead", "tfoot", "caption", "col", "colgroup")
)
_FORMATTING = frozenset((
	"a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike", "strong",
	"tt", "u",
))  # fmt: skip
_MARKER_TAGS = frozenset(
	("td", "th", "caption", "marquee", "object", "applet", "template")
)
# Start tags inserted without reconstructing the active formatting elements.
_NO_RECONSTRUCT = (_P_CLOSERS - {"xmp"}) | frozenset((
	"caption", "col", "colgroup", "tbody", "td", "tfoot", "th", "thead", "tr",
	"textarea", "iframe", "noembed", "noframes", "noscript", "script", "style",
	"template", "title", "base", "basefont", "bgsound", "link", "meta", "param",
	"source", "track", "rb", "rtc", "rp", "rt",
))  # fmt: skip
_IMPLIED_END = frozenset(
	("dd", "dt", "li", "optgroup", "option", "p", "rb", "rp", "rt", "rtc")
)
# Start tags that end foreign content.
_BREAKOUT = frozenset((
	"b", "big", "blockquote", "body", "br", "center", "code", "dd", "div", "dl", "dt",
	"em", "embed", "h1", "h2", "h3", "h4", "h5", "h6", "head", "hr", "i", "img", "li",
	"listing", "menu", "meta", "nobr", "ol", "p", "pre", "ruby", "s", "small", "span",
	"strong", "strike", "sub", "sup", "table", "tt", "u", "ul", "var",
))  # fmt: skip
_MARKER = None
# The elements an insertion mode other than in body starts with.
_MODES = _TABLE_MODE | {"colgroup", "template"}
# A template's mode, as the first start tag in it sets it ("body" for any other).
_TEMPLATE_MODE = {
	"caption": "table", "colgroup": "table", "tbody": "table", "tfoot": "table",
	"thead": "table", "col": "colgroup", "tr": "tbody", "td": "tr", "th": "tr",
}  # fmt: skip
_IN_HEAD = frozenset((
	"base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style",
	"template", "title",
))  # fmt: skip
_TABLE_CTX_STOP = frozenset(("table", "template", "#root"))
_TBODY_CTX = frozenset((*_TBODY, "template", "#root"))
_ROW_CTX = frozenset(("tr", "template", "#root"))


def _detach(n: Node) -> None:
	if n.parent is not None:
		n.parent.children.remove(n)
		n.parent = None


def _append(parent: Node, n: Node) -> None:
	_detach(n)
	n.parent = parent
	parent.children.append(n)


class _Builder:
	"""
	x/net/html's parser, as far as the writer depends on it: the in-body,
	table and template insertion modes, and its customizable <select>.
	"""

	def __init__(self) -> None:
		self.root = Node("el", "#root")
		self.stack = [self.root]  # the open elements
		# The active formatting elements; None is a marker.
		self.active: list[Node | None] = []
		self.form: Node | None = None

	@property
	def cur(self) -> Node:
		return self.stack[-1]

	def plain(self) -> bool:
		return _foreign(self.stack[-1])

	def feed(self, t: Tok, src: str) -> None:
		if t.kind == TEXT:
			s = newlines(src[t.start : t.end])
			self.text(unescape(s) if not t.name or t.name in _RCDATA else s)
		elif t.kind == START:
			self.start(t.name, t.attrs, t.self_closing)
		elif t.kind == END:
			self.end(t.name)
		elif t.kind == COMMENT:
			self._insert(Node("comment"))

	def _scope(self, tags: Collection[str], stop: frozenset[str] = _SCOPE) -> int:
		"""The index of the topmost element in tags that is in scope, or -1."""
		for i in range(len(self.stack) - 1, -1, -1):
			t = self.stack[i].tag
			if t in tags:
				return i
			if t in stop:
				return -1
		return -1

	def _pop_until(self, tags: Collection[str], stop: frozenset[str] = _SCOPE) -> bool:
		i = self._scope(tags, stop)
		if i > 0:
			del self.stack[i:]
		return i > 0

	def _clear(self, ctx: frozenset[str]) -> None:
		"""Back to a table, table body or row context."""
		while self.cur.tag not in ctx:
			self.stack.pop()

	def _mode(self) -> str:
		"""
		The insertion mode, by the element that sets it: a table element, or
		"template" until the template's content has one; "" for in body.
		"""
		for n in reversed(self.stack):
			if n.tag == "template":
				return {"": "template", "body": ""}.get(n.data, n.data)
			if n.tag in _MODES:
				return n.tag
		return ""

	def _foster(self, node: Node) -> None:
		"""Insert node before the open table, or into a template opened after it."""
		ti = max((i for i, n in enumerate(self.stack) if n.tag == "table"), default=-1)
		tj = max((i for i, n in enumerate(self.stack) if n.tag == "template"), default=-1)
		if tj > ti:
			_append(self.stack[tj], node)
			return
		table = self.stack[ti] if ti >= 0 else None
		parent = table.parent if table else self.root
		k = parent.children.index(table) if table else len(parent.children)
		if node.kind == "text" and k > 0 and parent.children[k - 1].kind == "text":
			parent.children[k - 1].data += node.data
			return
		node.parent = parent
		parent.children.insert(k, node)

	def _insert(self, node: Node, foster: bool = True) -> None:
		parent = self.cur
		if (
			foster
			and parent.tag in _TABLE_CTX
			and (
				(node.kind == "el" and node.tag not in _TABLE_OK)
				or (node.kind == "text" and node.data.strip(_HSPACE))
			)
		):
			self._foster(node)
		elif (
			node.kind == "text" and parent.children and parent.children[-1].kind == "text"
		):
			parent.children[-1].data += node.data
		else:
			node.parent = parent
			parent.children.append(node)

	def _add(
		self,
		tag: str,
		attrs: list[tuple[str, str]],
		push: bool = True,
		foster: bool = True,
	) -> Node:
		node = Node("el", tag, attrs)
		self._insert(node, foster)
		if push:
			self.stack.append(node)
			if len(self.stack) > MAX_OPEN:
				raise ParseError("html: open stack of elements exceeds 512 nodes")
		return node

	def _reconstruct(self) -> None:
		"""A formatting element closed only implicitly opens again for what follows."""
		active = self.active
		if not active or active[-1] is _MARKER or active[-1] in self.stack:
			return
		i = len(active) - 1
		while i > 0 and active[i - 1] is not _MARKER and active[i - 1] not in self.stack:
			i -= 1
		for k in range(i, len(active)):
			active[k] = self._add(active[k].tag, active[k].attrs)

	def _clear_to_marker(self) -> None:
		while self.active and self.active.pop() is not _MARKER:
			pass

	def start(self, tag: str, attrs: list[tuple[str, str]], self_closing: bool) -> None:  # noqa: PLR0912
		stack, active = self.stack, self.active
		cur = stack[-1]
		if _foreign(cur) and not _integration(cur, tag):
			breakout = tag in _BREAKOUT or (
				tag == "font" and any(k in ("color", "face", "size") for k, _ in attrs)
			)
			if not breakout:
				svg = cur.tag == "svg" or cur.tag.startswith("#svg-")
				self._add(("#svg-" if svg else "#math-") + tag, attrs, not self_closing)
				return
			while _foreign(self.cur) and not _integration(self.cur, tag):
				stack.pop()
		if tag in ("html", "body", "head", "frame", "frameset"):
			return
		if tag == "image":
			tag = "img"
		mode = self._mode()
		if mode == "template" and tag not in _IN_HEAD:
			# The first start tag in a template sets its mode, kept in its data.
			tmpl = next(n for n in reversed(stack) if n.tag == "template")
			tmpl.data = _TEMPLATE_MODE.get(tag, "body")
			mode = self._mode()
		if (
			mode
			and mode != "template"
			and self._table_start(tag, attrs, self_closing, mode)
		):
			return
		if tag in _TABLE_PART:  # in body (a caption's <th> too, as x/net/html), ignored
			return
		if tag == "form" and self.form is not None and not self._in("template"):
			return
		if tag in _P_CLOSERS:
			self._pop_until(("p",), _BUTTON_SCOPE)
		if tag in _HEADINGS and self.cur.tag in _HEADINGS:
			stack.pop()
		elif tag in ("li", "dd", "dt"):
			same = ("li",) if tag == "li" else ("dd", "dt")
			for i in range(len(stack) - 1, 0, -1):
				t = stack[i].tag
				if t in same:
					del stack[i:]
					break
				if t in _SPECIAL and t not in ("address", "div", "p"):
					break
		elif tag == "button":
			self._pop_until(("button",))
		elif tag == "select":
			if self._pop_until(("select",)):
				return
		elif tag == "input":
			self._pop_until(("select",))
		elif tag in ("option", "optgroup", "hr"):
			if self._scope(("select",)) > 0:
				self._implied_end("optgroup" if tag == "option" else "")
			elif tag != "hr" and self.cur.tag == "option":
				stack.pop()
		elif tag in ("rb", "rtc", "rp", "rt") and self._scope(("ruby",)) > 0:
			self._implied_end("rtc" if tag in ("rp", "rt") else "")
		elif tag == "a":
			for e in reversed(active):
				if e is _MARKER:
					break
				if e.tag == "a":
					self._adopt("a")
					if e in stack:
						stack.remove(e)
					if e in active:
						active.remove(e)
					break
		if tag not in _NO_RECONSTRUCT:
			self._reconstruct()
		if tag == "nobr" and self._scope(("nobr",)) >= 0:
			self._adopt("nobr")
			self._reconstruct()
		if tag in _FORMATTING:
			attrs = sorted(attrs)
			k = 0
			for e in reversed(active[:]):  # Noah's ark: three of a kind at most
				if e is _MARKER:
					break
				if e.tag == tag and e.attrs == attrs:
					k += 1
					if k >= 3:
						active.remove(e)
		node = self._add(
			tag, attrs, tag not in _VOID and not (self_closing and tag in ("svg", "math"))
		)
		if tag in _FORMATTING:
			active.append(node)
		elif tag in _MARKER_TAGS:
			active.append(_MARKER)
		elif tag == "form" and not self._in("template"):
			self.form = node

	def _implied_end(self, keep: str) -> None:
		while self.cur.tag in _IMPLIED_END and self.cur.tag != keep:
			self.stack.pop()

	def _in(self, tag: str) -> bool:
		return any(n.tag == tag for n in self.stack)

	def _table_start(  # noqa: PLR0911, PLR0912
		self, tag: str, attrs: list[tuple[str, str]], self_closing: bool, mode: str
	) -> bool:
		"""In a table mode: whether the start tag was dealt with."""
		stack = self.stack
		if mode in ("td", "th", "caption"):
			# x/net/html's caption mode lets th through
			if tag not in _TABLE_PART or (mode == "caption" and tag == "th"):
				return False
			if self._pop_until(
				("caption",) if mode == "caption" else ("td", "th"), _TABLE_SCOPE
			):
				self._clear_to_marker()
				self.start(tag, attrs, self_closing)
			return True
		if mode == "colgroup":
			if tag == "col":
				self._add(tag, attrs, False)
				return True
			if tag == "template":
				return False
			if self.cur.tag == "colgroup":
				stack.pop()
				self.start(tag, attrs, self_closing)
			return True
		if mode == "tr":
			if tag in ("td", "th"):
				self._clear(_ROW_CTX)
				self._add(tag, attrs)
				self.active.append(_MARKER)
				return True
			if tag in _TABLE_PART:
				if self._pop_until(("tr",), _TABLE_SCOPE):
					self.start(tag, attrs, self_closing)
				return True
		elif mode in _TBODY:
			if tag == "tr":
				self._clear(_TBODY_CTX)
				self._add(tag, attrs)
				return True
			if tag in ("td", "th"):
				self._clear(_TBODY_CTX)
				self._add("tr", [])
				self.start(tag, attrs, self_closing)
				return True
			if tag in _TABLE_PART:
				if self._scope(_TBODY, _TABLE_SCOPE) > 0:
					self._clear(_TBODY_CTX)
					stack.pop()
					self.start(tag, attrs, self_closing)
				return True
		if tag in ("caption", "colgroup", *_TBODY):
			self._clear(_TABLE_CTX_STOP)
			if tag == "caption":
				self.active.append(_MARKER)
			self._add(tag, attrs)
			return True
		if tag in ("col", "td", "th", "tr"):
			self._clear(_TABLE_CTX_STOP)
			self._add("colgroup" if tag == "col" else "tbody", [])
			self.start(tag, attrs, self_closing)
			return True
		if tag == "table":
			if self._pop_until(("table",), _TABLE_SCOPE):
				self.start(tag, attrs, self_closing)
			return True
		if tag == "input" and ascii_lower(dict(attrs).get("type", "")) == "hidden":
			self._add(tag, attrs, False, False)
			return True
		if tag == "form":
			if self.form is None and not self._in("template"):
				self.form = self._add(tag, attrs, False)
			return True
		return False

	def end(self, tag: str) -> None:  # noqa: PLR0912
		stack = self.stack
		if _foreign(self.cur):
			if tag in ("br", "p"):
				while _foreign(self.cur) and not _integration(self.cur, None):
					stack.pop()
			else:
				for i in range(len(stack) - 1, 0, -1):
					n = stack[i]
					if not _foreign(n):
						break
					if n.tag.rpartition("-")[2] == tag or n.tag == tag:
						del stack[i:]
						return
		mode = self._mode()
		if mode == "template" and tag != "template":
			return
		if mode == "colgroup" and tag != "template":
			if tag != "col" and self.cur.tag == "colgroup":
				stack.pop()
				if tag != "colgroup":
					self.end(tag)
		elif tag in _TABLE_END and mode and mode != "template":
			self._table_end(tag, mode)
		elif tag in _CLOSE_BLOCK:
			self._pop_until((tag,))
		elif tag == "p":
			if self._scope(("p",), _BUTTON_SCOPE) < 0:
				self.start("p", [], False)
			self._pop_until(("p",), _BUTTON_SCOPE)
		elif tag == "li":
			self._pop_until(("li",), _LIST_SCOPE)
		elif tag in _HEADINGS:
			self._pop_until(_HEADINGS)
		elif tag in _FORMATTING:
			self._adopt(tag)
		elif tag in ("applet", "marquee", "object"):
			if self._pop_until((tag,)):
				self._clear_to_marker()
		elif tag == "br":
			self.start("br", [], False)
		elif tag == "form":
			if self._in("template"):
				if self._scope(("form",)) > 0:
					self._implied_end("")
					self._pop_until(("form",))
			else:
				node, self.form = self.form, None
				i = self._scope(("form",))
				if node is not None and i > 0 and stack[i] is node:
					self._implied_end("")
					stack.remove(node)
		elif tag == "template":
			i = next(
				(i for i in range(len(stack) - 1, 0, -1) if stack[i].tag == "template"), 0
			)
			if i:
				del stack[i:]
				self._clear_to_marker()
		elif tag not in ("html", "body"):
			self._end_other(tag)

	def _end_other(self, tag: str) -> None:
		for i in range(len(self.stack) - 1, 0, -1):
			t = self.stack[i].tag
			if t == tag:
				del self.stack[i:]
				return
			if t in _SPECIAL:
				return

	def _table_end(self, tag: str, mode: str) -> None:  # noqa: PLR0912
		"""A table end tag in the insertion mode of mode, a table element."""

		def close(tags: Collection[str]) -> bool:
			return self._pop_until(tags, _TABLE_SCOPE)

		if mode in ("td", "th"):
			if tag in ("td", "th"):
				if close((tag,)):
					self._clear_to_marker()
			elif (
				tag not in ("caption", "col", "colgroup")
				and self._scope((tag,), _TABLE_SCOPE) > 0
			):
				close(("td", "th"))
				self._clear_to_marker()
				self.end(tag)
		elif mode == "tr":
			if tag == "tr":
				close(("tr",))
			elif (
				tag == "table"
				or (tag in _TBODY and self._scope((tag,), _TABLE_SCOPE) > 0)
			) and close(("tr",)):
				self.end(tag)
		elif mode in _TBODY:
			if tag in _TBODY:
				close((tag,))
			elif tag == "table" and close(_TBODY):
				self.end(tag)
		elif mode == "caption":
			if tag == "caption":
				if close(("caption",)):
					self._clear_to_marker()
			elif tag == "table" and close(("caption",)):
				self._clear_to_marker()
				self.end(tag)
		elif tag == "table":
			close(("table",))

	def _adopt(self, tag: str) -> None:  # noqa: PLR0912
		"""The adoption agency algorithm, for the end tag of formatting element tag."""
		stack, active = self.stack, self.active
		cur = stack[-1]
		if cur.tag == tag and cur not in active:
			stack.pop()
			return
		for _ in range(8):
			fe = None
			for e in reversed(active):
				if e is _MARKER:
					break
				if e.tag == tag:
					fe = e
					break
			if fe is None:
				self._end_other(tag)
				return
			if fe not in stack:
				active.remove(fe)
				return
			if self._scope((tag,)) < 0:
				return
			fi = stack.index(fe)
			fb = next((e for e in stack[fi:] if e.tag in _SPECIAL), None)
			if fb is None:
				del stack[fi:]
				active.remove(fe)
				return
			common = stack[fi - 1]
			bookmark = active.index(fe)
			last = node = fb
			x = stack.index(fb)
			j = 0
			while True:
				j += 1
				x -= 1
				node = stack[x]
				if node is fe:
					break
				if j > 3 and node in active:
					ni = active.index(node)
					active.remove(node)
					if ni <= bookmark:
						bookmark -= 1
					continue
				if node not in active:
					stack.remove(node)
					continue
				clone = Node("el", node.tag, node.attrs)
				active[active.index(node)] = clone
				stack[stack.index(node)] = clone
				node = clone
				if last is fb:
					bookmark = active.index(node) + 1
				_append(node, last)
				last = node
			_detach(last)
			if common.tag in _TABLE_CTX:
				self._foster(last)
			else:
				_append(common, last)
			clone = Node("el", fe.tag, fe.attrs)
			for k in fb.children:
				k.parent = clone
			clone.children, fb.children = fb.children, []
			_append(fb, clone)
			if fe in active and active.index(fe) < bookmark:
				bookmark -= 1
			active.remove(fe)
			active.insert(bookmark, clone)
			stack.remove(fe)
			stack.insert(stack.index(fb) + 1, clone)

	def text(self, data: str) -> None:
		cur = self.cur
		if (
			cur.tag in ("pre", "listing", "textarea")
			and not cur.children
			and data[:1] == "\n"
		):
			data = data[1:]  # a newline that starts a pre, listing or textarea
		mode = self._mode()
		if mode == "colgroup":
			rest = data.lstrip(_HSPACE)
			if rest != data:
				self._insert(Node("text", data=data[: len(data) - len(rest)]))
			if not rest or cur.tag != "colgroup":
				return
			self.stack.pop()
			data, cur, mode = rest, self.cur, self._mode()
		if not data:
			return
		if not (cur.tag in _TABLE_CTX and not data.strip(_HSPACE)) and (
			not _foreign(cur) or _integration(cur, None)
		):
			self._reconstruct()
		self._insert(Node("text", data=data))


def parse_fragment(src: str) -> list[Node]:
	b = _Builder()
	for t in tokens(src, b.plain):
		b.feed(t, src)
	return b.root.children


# ---------------------------------------------------------------------------
# `clean` mode (R6.6-R6.7)

_DROPPED = frozenset((
	"script", "style", "template", "iframe", "noscript", "noembed", "noframes", "input",
	"select", "textarea", "button", "embed", "head", "meta", "link", "title", "base",
	"frame", "frameset", "canvas", "map",
))  # fmt: skip
_UNWRAP = frozenset((
	"p", "div", "section", "article", "main", "header", "footer", "aside", "nav",
	"figure", "figcaption", "address", "center", "hgroup", "fieldset", "legend", "dl",
	"dt", "dd", "form", "body", "html", "caption", "li", "tr", "td", "th", "thead",
	"tbody", "tfoot", "summary", "menu", "dir", "listing", "xmp", "plaintext", "search",
	"dialog", "option", "optgroup",
))  # fmt: skip
_BLOCK = _UNWRAP | frozenset((
	"h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote", "pre", "hr", "table",
	"details",
))  # fmt: skip
# Elements the inline writer gives markup of its own; a link, with a destination.
_MARKUP = frozenset((
	"em", "i", "strong", "b", "sup", "sub", "u", "small", "del", "s", "strike", "ins",
	"code", "kbd", "samp", "tt", "img", "audio", "video", "source", "object",
))  # fmt: skip
MAX_NEST = 16

# The dictionary's display table (R6.6): class -> DISPLAY_*, | GAP when the
# stylesheet sets the class apart, as wudict's htmlref.ParseCSS derives it.
DISPLAY_UNSET, DISPLAY_NONE, DISPLAY_INLINE, DISPLAY_BLOCK = 0, 1, 2, 3
_DISPLAY_MASK, GAP = 0x0F, 0x80

K_PARA, K_LIST, K_OTHER = 0, 1, 2
IN_PARA, IN_HEADING, IN_CELL = 0, 1, 2

_MD_ESC = {ord(c): "\\" + c for c in "\\`*_[]<>&~|"}
_HEADING_ESC = {ord(c): "\\" + c for c in "\\`*_[]<>&~"}
_TEXT_RUN = re.compile("([ \t\n\r\f]+)|[^ \t\n\r\f]+")
_ORDERED = re.compile("([0-9]+)[.)](?=[ \t\n]|\\Z)")  # an ordered list marker
_STAR = re.compile(r"(?<!\\)(?:\\\\)*\*")  # an unescaped `*`
_BACKTICKS = re.compile("`+")
_LIST_MARK = re.compile("[0-9]*(.)", re.DOTALL)
_ALTERNATE = {"-": "*", "*": "-", ".": ")", ")": "."}
_ALIGN = {"": "---", "left": ":--", "center": ":-:", "right": "--:"}


class Block:
	__slots__ = ("interrupts", "kind", "list", "md")

	def __init__(
		self, md: str, kind: int, lst: str = "", interrupts: bool = False
	) -> None:
		self.md, self.kind, self.list, self.interrupts = md, kind, lst, interrupts


def media_src(n: Node) -> str:
	def src(n: Node) -> str:
		return go_trim_space(n.attr("src") or "")

	if n.tag in ("audio", "video", "source"):
		return src(n) or next(
			(
				s
				for k in n.children
				if k.kind == "el" and k.tag == "source" and (s := src(k))
			),
			"",
		)
	if n.tag == "object" and go_trim_space(n.attr("type") or "").lower().startswith(
		("audio/", "video/")
	):
		return go_trim_space(n.attr("data") or "")
	return ""


def dropped(n: Node) -> bool:
	if n.kind != "el":
		return n.kind == "comment"
	return _foreign(n) or n.tag in _DROPPED or (n.tag == "object" and not media_src(n))


def block_elem(n: Node) -> bool:
	return n.kind == "el" and n.tag in _BLOCK


def display(st: dict[str, int] | None, n: Node) -> int:
	"""The strongest display of n's classes."""
	if not st or n.kind != "el":
		return DISPLAY_UNSET
	return max(
		(st.get(c, 0) & _DISPLAY_MASK for c in _HFIELD.findall(n.attr("class") or "")),
		default=0,
	)


def gap(st: dict[str, int] | None, n: Node) -> bool:
	"""Whether the stylesheet sets n apart from its neighbours: a space each side."""
	if not st or n.kind != "el":
		return False
	return any(st.get(c, 0) & GAP for c in _HFIELD.findall(n.attr("class") or ""))


def skipped(st: dict[str, int] | None, n: Node) -> bool:
	return dropped(n) or display(st, n) == DISPLAY_NONE


def styled_block(st: dict[str, int] | None, n: Node) -> bool:
	return not block_elem(n) and display(st, n) == DISPLAY_BLOCK


def formatting(n: Node) -> bool:
	return link_href(n) != "" if n.tag == "a" else n.tag in _MARKUP


def text_content(n: Node) -> str:
	out: list[str] = []

	def walk(n: Node) -> None:
		if n.kind == "text":
			out.append(n.data)
		elif n.tag == "br":
			out.append("\n")
		elif not dropped(n):
			for k in n.children:
				walk(k)

	walk(n)
	return "".join(out)


def list_mark(md: str) -> str:
	"""The marker character of a list's first item: `-`, `*`, `.` or `)`."""
	m = _LIST_MARK.match(md)
	return m[1] if m else ""


def alternate(md: str) -> str:
	"""md, a list, with the other marker (R6.10)."""
	frm = list_mark(md)
	lines = md.split("\n")
	for i, line in enumerate(lines):
		if line and line[0] != " ":
			j = len(line) - len(line.lstrip("0123456789"))
			if line[j : j + 1] == frm:
				lines[i] = line[:j] + _ALTERNATE.get(frm, "") + line[j + 1 :]
	return "\n".join(lines)


def code_block(pre: Node) -> str:
	text = text_content(pre).removesuffix("\n")
	info = ""
	for k in pre.children:
		if k.kind == "el" and k.tag == "code":
			for cl in go_fields(k.attr("class") or ""):
				if (
					cl.startswith("language-")
					and len(cl) > 9
					and not any(c in cl[9:] for c in "`~")
				):
					info = cl[9:]
	fence = "`" * max(3, max(map(len, _BACKTICKS.findall(text)), default=0) + 1)
	return "\n".join([fence + info, *([text] if text else []), fence])


def cell_align(c: Node) -> str:
	for k, raw in c.attrs:
		v = go_trim_space(raw).lower()
		if k == "align":
			if v in ("left", "center", "right"):
				return v
		elif k == "style":
			for decl in v.split(";"):
				key, sep, val = decl.partition(":")
				if sep and go_trim_space(key) == "text-align":
					val = go_trim_space(val)
					if val in ("left", "center", "right"):
						return val
	return ""


def table(t: Node, st: dict[str, int] | None) -> str:
	rows: list[list[Node]] = []

	def walk(n: Node) -> None:
		for k in n.children:
			if k.kind != "el" or skipped(st, k):
				continue
			if k.tag == "tr":
				rows.append(
					[c for c in k.children if c.kind == "el" and c.tag in ("td", "th")]
				)
			elif k.tag in ("thead", "tbody", "tfoot"):
				walk(k)

	walk(t)
	cols = max(map(len, rows), default=0)
	if cols == 0:
		return ""

	def line(r: list[Node]) -> str:
		out = "|"
		for i in range(cols):
			md = ""
			if i < len(r) and not skipped(st, r[i]):
				w = Inline(IN_CELL, st)
				w.nodes(r[i].children)
				md = w.done()
			out += " " + md + " |" if md else " |"
		return out

	head = rows[0]
	delim = "".join(
		" " + _ALIGN[cell_align(head[i]) if i < len(head) else ""] + " |"
		for i in range(cols)
	)
	return "\n".join([line(head), "|" + delim, *map(line, rows[1:])])


class Converter:
	def __init__(self, st: dict[str, int] | None) -> None:
		self.st = st
		self.holds: dict[int, bool] = {}

	def holds_block(self, n: Node) -> bool:
		"""
		Whether a block, by tag or stylesheet, is among n's descendants, outside
		anything skipped.
		"""
		v = self.holds.get(id(n))
		if v is None:
			st = self.st
			v = any(
				k.kind == "el"
				and not skipped(st, k)
				and (block_elem(k) or styled_block(st, k) or self.holds_block(k))
				for k in n.children
			)
			self.holds[id(n)] = v
		return v

	def flow(self, nodes: list[Node], depth: int) -> list[Block]:
		st = self.st
		out: list[Block] = []
		para = Inline(IN_PARA, st)

		def flush() -> None:
			nonlocal para
			if md := para.done():
				out.append(Block(md, K_PARA))
			para = Inline(IN_PARA, st)

		def add(b: Block) -> None:
			if b.kind == K_LIST and out:
				p = out[-1]
				if (
					p.kind == K_LIST
					and p.list == b.list
					and list_mark(p.md) == list_mark(b.md)
				):
					b.md = alternate(b.md)
			out.append(b)

		def walk(nodes: list[Node]) -> None:  # noqa: PLR0912
			for n in nodes:
				if skipped(st, n):
					continue
				if styled_block(st, n):
					flush()
					if formatting(n):
						para.node(n)
						flush()
					else:
						for b in self.flow(n.children, depth):
							add(b)
				elif not block_elem(n):
					if n.kind == "el" and not formatting(n) and self.holds_block(n):
						walk(n.children)  # block-in-inline: its content joins this flow
					else:
						para.node(n)
				elif n.tag in _UNWRAP or (
					n.tag in ("ul", "ol", "blockquote") and depth >= MAX_NEST
				):
					flush()
					for b in self.flow(n.children, depth):
						add(b)
				else:
					flush()
					if b := self.block_of(n, depth):
						add(b)

		walk(nodes)
		flush()
		return out

	def block_of(self, n: Node, depth: int) -> Block | None:  # noqa: PLR0911
		tag = n.tag
		if tag in _HEADINGS:
			w = Inline(IN_HEADING, self.st)
			w.nodes(n.children)
			t = w.done()
			return (
				Block("#" * max(int(tag[1]), 3) + " " + esc_closing(t), K_OTHER)
				if t
				else None
			)
		if tag == "hr":
			return Block("***", K_OTHER)
		if tag == "pre":
			return Block(code_block(n), K_OTHER)
		if tag == "blockquote":
			inner = "\n\n".join(b.md for b in self.flow(n.children, depth + 1))
			lines = (">" + (" " + line if line else "") for line in inner.split("\n"))
			return Block("\n".join(lines), K_OTHER) if inner else None
		if tag in ("ul", "ol"):
			md, interrupts = self.list_block(n, depth + 1)
			return Block(md, K_LIST, tag, interrupts) if md else None
		if tag == "table":
			md = table(n, self.st)
			return Block(md, K_OTHER) if md else None
		if tag == "details":
			return Block(self.details(n, depth), K_OTHER)
		return None

	def list_block(self, n: Node, depth: int) -> tuple[str, bool]:
		groups: list[list[Node]] = []
		for k in n.children:
			if skipped(self.st, k) or (k.kind == "text" and not go_trim_space(k.data)):
				continue
			if k.kind == "el" and k.tag == "li":
				groups.append(list(k.children))
			elif groups:
				groups[-1].append(k)
			else:
				groups.append([k])
		items = [bs for bs in (self.flow(g, depth) for g in groups) if bs]
		if not items:
			return "", False
		tight = all(
			b.kind == K_LIST and it[0].kind == K_PARA and b.interrupts
			for it in items
			for b in it[1:]
		)
		start = 1
		if n.tag == "ol":
			v = go_trim_space(n.attr("start") or "")
			if re.fullmatch("[+-]?[0-9]+", v) and 0 <= int(v) <= 999999999:
				start = int(v)
		sep = "\n" if tight else "\n\n"
		out = []
		for i, it in enumerate(items):
			marker = f"{start + i}." if n.tag == "ol" else "-"
			pad = " " * (len(marker) + 1)
			first, *rest = sep.join(b.md for b in it).split("\n")
			out.append(
				"\n".join(
					[marker + " " + first, *(pad + ln if ln else ln for ln in rest)]
				)
			)
		return sep.join(out), n.tag == "ul" or start == 1

	def details(self, n: Node, depth: int) -> str:
		summary, rest = "", []
		for k in n.children:
			if k.kind == "el" and k.tag == "summary" and not summary:
				summary = " ".join(go_fields(text_content(k)))
			else:
				rest.append(k)
		out = "<details>\n"
		if summary:
			out += "<summary>" + go_html_escape(summary) + "</summary>\n"
		if inner := "\n\n".join(b.md for b in self.flow(rest, depth)):
			out += "\n" + inner + "\n\n"
		return out + "</details>"


def esc_closing(t: str) -> str:
	"""Escape the first `#` of a trailing `#` run after a space (or alone)."""
	j = len(t.rstrip("#"))
	return t[:j] + "\\" + t[j:] if j < len(t) and (j == 0 or t[j - 1] == " ") else t


def line_start_escape(s: str, off: int) -> int:
	"""Where a line starting at off needs a backslash (R6.7), or -1."""
	if off >= len(s):
		return -1
	if s[off] in "#+-=:":
		return off
	m = _ORDERED.match(s, off)
	return m.end(1) if m and len(m[1]) <= 9 else -1


def marked(c: str) -> bool:
	"""A letter, mark or decimal digit."""
	cat = unicodedata.category(c)
	return cat[0] in "LM" or cat == "Nd"


class Inline:
	"""The inline content of a paragraph, heading or table cell."""

	def __init__(self, mode: int, st: dict[str, int] | None) -> None:
		self.st = st
		self.mode = mode
		self.b: list[str] = []
		self.n = 0  # length of the text in b
		self.line_start = True
		self.starts: list[int] = []  # offsets of line starts
		self.space = False
		self.brk = False
		self.lead = False  # a space before the first content: the parent writes it

	def _write(self, s: str) -> None:
		self.b.append(s)
		self.n += len(s)

	def value(self) -> str:
		s = "".join(self.b)
		self.b = [s]
		return s

	def last(self) -> str:
		for part in reversed(self.b):
			if part:
				return part[-1]
		return ""

	def done(self) -> str:
		s = self.value()
		for off in reversed(self.starts):
			at = line_start_escape(s, off)
			if at >= 0:
				s = s[:at] + "\\" + s[at:]
		return s

	def spaced(self) -> None:
		self.space = True
		if self.n == 0:
			self.lead = True

	def hoist(self, sub: Inline, before: bool) -> None:
		"""The space at an edge of an element's content goes outside its markup."""
		if sub.lead if before else sub.space:
			self.spaced()

	def pending(self) -> None:
		if self.n and self.brk:
			if self.mode == IN_PARA:
				self._write("<br>\n" if self.last() == "\\" else "\\\n")
				self.line_start = True
			else:
				self._write("<br>" if self.mode == IN_CELL else " ")
		elif self.n and self.space:
			self._write(" ")
		self.space = self.brk = False

	def syntax(self, s: str) -> None:
		self.pending()
		self._write(s)
		self.line_start = False

	def text(self, s: str) -> None:
		for m in _TEXT_RUN.finditer(s):
			if m[1]:
				self.spaced()
				continue
			self.pending()
			if self.line_start and self.mode == IN_PARA:
				self.starts.append(self.n)
			self._write(m[0].translate(_MD_ESC))
			self.line_start = False

	def nodes(self, ns: list[Node]) -> None:
		for n in ns:
			self.node(n)

	def sub(self, ns: list[Node]) -> Inline:
		s = Inline(self.mode, self.st)
		s.line_start = False
		s.nodes(ns)
		return s

	def node(self, n: Node) -> None:
		if n.kind == "text":
			self.text(n.data)
		elif n.kind == "el" and not skipped(self.st, n):
			if styled_block(self.st, n):
				if self.n:
					self.brk = True
				self._element(n)
				self.brk = True
			elif gap(self.st, n):
				self.spaced()
				self._element(n)
				self.space = True
			else:
				self._element(n)

	def _element(self, n: Node) -> None:  # noqa: PLR0912
		tag = n.tag
		if tag == "br":
			if self.n:
				self.brk = True
		elif tag in ("em", "i", "strong", "b"):
			d, name = ("**", "strong") if tag in ("strong", "b") else ("*", "em")
			sub = self.sub(n.children)
			inner = sub.done()
			self.hoist(sub, True)
			if inner:
				self.pending()
				if (
					marked(inner[0])
					and marked(inner[-1])
					and self.last() != "*"
					and not _STAR.search(inner)
				):
					self.syntax(d + inner + d)
				else:
					self.syntax(f"<{name}>{inner}</{name}>")
			self.hoist(sub, False)
		elif tag in ("sup", "sub", "u", "small", "del", "s", "strike", "ins", "kbd"):
			name = "del" if tag in ("s", "strike") else tag
			sub = self.sub(n.children)
			self.hoist(sub, True)
			if inner := sub.done():
				self.syntax(f"<{name}>{inner}</{name}>")
			self.hoist(sub, False)
		elif tag in ("code", "samp", "tt"):
			t = squash(text_content(n))
			if not t:
				return
			self.pending()
			if self.last() == "`":
				self.syntax("<code>")
				self.text(t)
				self.syntax("</code>")
				return
			if self.mode == IN_CELL:
				t = t.replace("|", "\\|")
			runs = set(map(len, _BACKTICKS.findall(t)))
			f = "`" * next(k for k in range(1, len(runs) + 2) if k not in runs)
			if t[0] == "`" or t[-1] == "`":
				t = " " + t + " "
			self.syntax(f + t + f)
		elif tag == "a":
			href = link_href(n)
			if not href:
				self.nodes(n.children)
				return
			sub = self.sub(n.children)
			text = sub.done()
			self.hoist(sub, True)
			self.bang_guard()
			self.syntax("[" + text + "](" + self.cell_safe(dest(href), title(n)) + ")")
			self.hoist(sub, False)
		elif tag == "img":
			src = link_target(n.attr("src") or "")
			alt = (
				squash(n.attr("alt") or "")
				.replace("\\", "\\\\")
				.replace("[", "\\[")
				.replace("]", "\\]")
			)
			if self.mode == IN_CELL:
				alt = alt.replace("|", "\\|")
			if src:
				self.bang_guard()
				self.syntax("![" + alt + "](" + self.cell_safe(dest(src), title(n)) + ")")
			elif alt:
				self.text(alt)
		elif tag in ("audio", "video", "source", "object"):
			if s := media_src(n):
				self.bang_guard()
				self.syntax("[▶](" + self.cell_safe(dest(link_target(s)), "") + ")")
		else:
			block = block_elem(n)
			if block and self.n:
				self.brk = True
			self.nodes(n.children)
			if block:
				self.brk = True

	def bang_guard(self) -> None:
		"""Escape a `!` the next `[` would turn into an image."""
		if self.space or self.brk or not self.n:
			return
		s = self.value()
		if s[-1] == "!" and s[-2:-1] != "\\":
			self.b = [s[:-1] + "\\!"]
			self.n += 1

	def cell_safe(self, d: str, t: str) -> str:
		if self.mode != IN_CELL:
			return d + t
		return d.replace("|", "%7C") + t.replace("|", "\\|")


def title(n: Node) -> str:
	t = squash(n.attr("title") or "")
	return ' "' + t.replace("\\", "\\\\").replace('"', '\\"') + '"' if t else ""


def clean_body(src: str, st: dict[str, int] | None = None) -> str:
	"""
	`clean` mode (R6.6-R6.7); raises CleanError. st is the dictionary's
	display table ({class: DISPLAY_* | GAP}), None without a stylesheet.
	"""
	try:
		nodes = parse_fragment(valid_text(src))
	except ParseError as e:
		raise CleanError("the article", str(e)) from e
	# The converter recurses per level of a tree MAX_OPEN deep at most.
	limit = sys.getrecursionlimit()
	sys.setrecursionlimit(max(limit, 12 * MAX_OPEN))
	try:
		md = "\n\n".join(b.md for b in Converter(st).flow(nodes, 0))
	finally:
		sys.setrecursionlimit(limit)
	if md.startswith("see:") and "\n" not in md:
		md = "see\\:" + md[4:]
	if md and any(
		t.level == 0 and t.type == "heading_open" and t.tag in ("h1", "h2")
		for t in block_parse(md)
	):
		raise CleanError("a heading", "it would read as the start of an entry")
	return md


# ---------------------------------------------------------------------------
# `html` mode (R6.5)

# A type-6 start tag the reader (goldmark) opens a block with.
_TYPE6_START = re.compile("<([A-Za-z][A-Za-z0-9]*)(?: |>|/>)")
_TYPE6 = frozenset((
	"address", "article", "aside", "base", "basefont", "blockquote", "body", "caption",
	"center", "col", "colgroup", "dd", "details", "dialog", "dir", "div", "dl", "dt",
	"fieldset", "figcaption", "figure", "footer", "form", "frame", "frameset", "h1",
	"h2", "h3", "h4", "h5", "h6", "head", "header", "hr", "html", "iframe", "legend",
	"li", "link", "main", "menu", "menuitem", "nav", "noframes", "ol", "optgroup",
	"option", "p", "param", "search", "section", "summary", "table", "tbody", "td",
	"tfoot", "th", "thead", "title", "tr", "track", "ul",
))  # fmt: skip
_BLANK_LINE = re.compile("^[ \t]*$", re.MULTILINE)


def _wrapped(s: str) -> bool:
	"""Whether s is one element that starts a type-6 HTML block, and nothing else."""
	m = _TYPE6_START.match(s)
	if not m or (tag := m[1].lower()) not in _TYPE6:
		return False
	b = _Builder()
	kids = b.root.children
	try:
		for t in tokens(s, b.plain):
			b.feed(t, s)
			if (
				len(kids) > 1
				and sum(k.kind != "text" or bool(k.data.strip(" \t\n\f")) for k in kids)
				> 1
			):
				return False  # nothing is ever taken away
	except ParseError:
		return False
	only = [k for k in kids if k.kind != "text" or k.data.strip(" \t\n\f")]
	return len(only) == 1 and only[0].kind == "el" and only[0].tag == tag


def _no_blank_lines(s: str) -> str:
	"""
	Remove blank lines from s; one inside pre, textarea or listing text becomes
	`&#10;` at the start of the next line.
	"""
	if not _BLANK_LINE.search(s):
		return s
	keep, depth = [], 0
	for t in tokens(s):
		if (t.kind == END or (t.kind == START and not t.self_closing)) and t.name in (
			"pre",
			"textarea",
			"listing",
		):
			depth = depth + 1 if t.kind == START else max(depth - 1, 0)
		elif t.kind == TEXT and depth:
			keep.append((t.start, t.end))
	out, at = [], 0
	for line in s.split("\n"):
		if line.strip(" \t"):
			out.append(line + "\n")
		elif any(a <= at < b for a, b in keep):
			out.append(line + "&#10;")
		at += len(line) + 1
	return "".join(out).rstrip("\n")


def canon_links(doc: str) -> str:
	"""htmlref.CanonLinks: every lookup link in its canonical spelling."""
	low = doc.lower()
	if "bword:" not in low and "entry://@" not in low:
		return doc
	out, raw = [], ""
	for t in tokens(doc):
		chunk = doc[t.start : t.end]
		if t.kind == START:
			if (
				not raw
				and t.name in _RAW_TEXT
				and t.name != "plaintext"
				and not t.self_closing
			):
				raw = t.name
			attrs = [(k, _canon_attr(k, v)) for k, v in t.attrs]
			if attrs != t.attrs:
				tag = t.name + "".join(
					f' {k}="{v.translate(_XNET_ESC)}"' for k, v in attrs
				)
				chunk = "<" + tag + ("/>" if t.self_closing else ">")
		elif t.kind == END and t.name == raw:
			raw = ""
		elif t.kind == TEXT and raw == "style":
			chunk = _rewrite_css(chunk)
		out.append(chunk)
	return "".join(out)


_URL_ATTR = frozenset(
	("src", "href", "data", "poster", "background", "longdesc", "usemap")
)
_CSS_URL = re.compile(
	r"""url\([ \t\n\f\r]*(?:"([^"]*)"|'([^']*)'|([^) \t\n\f\r]*))[ \t\n\f\r]*\)""",
	re.IGNORECASE,
)


def _canon_attr(k: str, v: str) -> str:
	if k == "style":
		return _rewrite_css(v)
	if k in ("srcset", "imagesrcset") or k.endswith(("-srcset", ":srcset")):
		return _rewrite_srcset(v)
	if k[max(k.rfind("-"), k.rfind(":")) + 1 :] in _URL_ATTR:  # src, data-src, xlink:href
		return canon_ref(clean_ref(v))
	return v


def _rewrite_css(css: str) -> str:
	if "url(" not in css and "URL(" not in css and "Url(" not in css:
		return css

	def one(m: re.Match[str]) -> str:
		ref = (m[1] or "") + (m[2] or "") + (m[3] or "")
		nu = canon_ref(clean_ref(ref))
		if nu == ref:
			return m[0]
		if any(c in nu for c in " \t()\"'"):
			return "url('" + nu.replace("'", "%27") + "')"
		return "url(" + nu + ")"

	return _CSS_URL.sub(one, css)


def _rewrite_srcset(val: str) -> str:
	parts = val.split(",")
	changed = False
	for i, p in enumerate(parts):
		fs = go_fields(p)
		if fs and (nu := canon_ref(clean_ref(fs[0]))) != fs[0]:
			fs[0] = nu
			parts[i] = " ".join(fs)
			changed = True
	return ", ".join(parts) if changed else val


def html_body(src: str) -> str:
	"""`html` mode (R6.5)."""
	s = canon_links(valid_text(src)).strip(" \t\r\n\f")
	if not s:
		return ""
	s = _no_blank_lines(newlines(s))
	return s if _wrapped(s) else "<div>\n" + s + "\n</div>"


# ---------------------------------------------------------------------------
# Names and header keys (R6.2-R6.3)

_NAME_MAP = dict.fromkeys((*range(32), 127)) | dict.fromkeys(map(ord, "\r\n\t"), " ")
_NOT_KEY = re.compile("[^a-z0-9]+")


def repair_name(s: str) -> str:
	"""R6.2 on a name or header value."""
	return _SURROGATES.sub("\ufffd", s).translate(_NAME_MAP).strip(" ")


def heading_esc(s: str) -> str:
	"""A name as the text of a heading (R6.2)."""
	return esc_closing(s.translate(_HEADING_ESC))


def field_key(name: str) -> str:
	"""R6.3: a source key as a header key, "" when nothing of it is usable."""
	k = _NOT_KEY.sub("-", go_lower(name)).strip("-")
	if k[:1].isdigit() or k in ("wudict", "from", "to", "meta"):
		k = "x-" + k
	return k


# ---------------------------------------------------------------------------
# The reader (§3)

_TAG = re.compile("[A-Za-z][A-Za-z0-9-]*")
_HTML6 = _TYPE6 | {"meta"}  # goldmark's type-6 names
# What may follow a type-7 tag's name in goldmark: attributes, then spaces
# (not tabs), `>` or `/>`, and spaces to the end of the line.
_TYPE7_REST = re.compile(
	"((?:[ \t\r\n]+[A-Za-z_:][A-Za-z0-9:._-]*"
	"(?:[ \t\r\n]*=[ \t\r\n]*(?:\"[^\"]*\"|'[^']*'|[^\\x00-\\x20\"'=<>`]+))?)*) */?> *\\Z"
)
# What ends an HTML block of each type (CommonMark 4.6, not HTML: type 2 ends
# at `-->` only); 6 and 7 end before a blank line.
_HTML_END = {
	1: re.compile("</(?:script|pre|style|textarea)>", re.IGNORECASE),
	2: re.compile("-->"),
	3: re.compile(r"\?>"),
	4: re.compile(">"),
	5: re.compile(r"\]\]>"),
}


def html_block_start(line: str, in_paragraph: bool, eof: bool) -> int:  # noqa: PLR0911, PLR0912
	"""
	The kind of HTML block line starts, 0 for none, as goldmark decides it:
	CommonMark 4.6 but for `<pre/>` (type 1), `</textarea>`, `</ span>` (type
	7), `meta` (a type-6 name), a tab after the tag or before `>` and a bare
	`<div` line but the last (none), `<!doctype` (none). in_paragraph: a
	paragraph is open; eof: the line ends the text without a newline.
	"""
	if len(line) < 2 or line[0] != "<":
		return 0
	for name in ("textarea", "script", "style", "pre"):
		if line[1 : len(name) + 1].lower() == name:
			rest = line[len(name) + 1 :]
			if rest[:1] in ("", " ", "\t", "\r", ">") or rest.startswith("/>"):
				return 1
			break
	if line.startswith("<!--"):
		return 2
	if line[1] == "?":
		return 3
	if line[1] == "!" and "A" <= line[2:3] <= "Z":
		return 4
	if line.startswith("<![CDATA["):
		return 5
	closing = line[1] == "/"
	m = _TAG.match(line, len(line) - len(line[2:].lstrip(" ")) if closing else 1)
	if not m:
		return 0
	name, rest = m[0].lower(), line[m.end() :]
	if t7 := _TYPE7_REST.match(rest):
		if name in _HTML6:
			return 6
		if (
			name not in ("script", "style", "pre")
			and not in_paragraph
			and not (closing and t7[1])
		):
			return 7
	if name in _HTML6 and (
		rest[:1] in (" ", ">") or rest.startswith("/>") or (not rest and eof)
	):
		return 6
	return 0


_UNDERLINE = re.compile("(?:=+|-+)[ \t]*")
_PARSER: MarkdownIt | None = None


def parser() -> MarkdownIt:
	"""
	Stock CommonMark with tables, where markdown-it departs from CommonMark:
	headings and paragraphs are trimmed of spaces and tabs only (R3.4); HTML
	blocks start as CommonMark says; the lines after a link reference
	definition continue its paragraph; and an autolink's text is its URL as
	written.
	"""
	global _PARSER
	if _PARSER is not None:
		return _PARSER
	from markdown_it import MarkdownIt

	md = MarkdownIt("commonmark", {"html": True}).enable("table")
	md.normalizeLinkText = str  # type: ignore[method-assign]
	rules = {r.name: r for r in md.block.ruler.__rules__}
	heading, lheading, reference, paragraph = (
		rules[k].fn for k in ("heading", "lheading", "reference", "paragraph")
	)

	def atx(state, start, end, silent):  # noqa: ANN001, ANN202
		ok = heading(state, start, end, silent)
		if ok and not silent:
			at = state.bMarks[start] + state.tShift[start] + len(state.tokens[-1].markup)
			s = state.src[at : state.eMarks[start]].rstrip(" \t")
			t = s.rstrip("#")
			state.tokens[-2].content = (
				t if t != s and t.endswith((" ", "\t")) else s
			).strip(" \t")
		return ok

	def setext(state, start, end, silent):  # noqa: ANN001, ANN202
		ok = lheading(state, start, end, silent)
		if ok and not silent:
			text = state.getLines(start, state.line - 1, state.blkIndent, False)
			state.tokens[-2].content = text.strip(" \t")
		return ok

	def para(state, start, end, silent):  # noqa: ANN001, ANN202
		ok = paragraph(state, start, end, silent)
		if ok and not silent:
			# markdown-it strips any whitespace; refill only when an edge has some
			last = state.line - 1
			first = state.src[state.bMarks[start] + state.tShift[start]]
			tail = state.src[state.bMarks[last] : state.eMarks[last]].rstrip(" \t")
			if first.isspace() or tail[-1:].isspace():
				text = state.getLines(start, state.line, state.blkIndent, False)
				state.tokens[-2].content = text.strip(" \t")
		return ok

	def html_block(state, start, end, silent):  # noqa: ANN001, ANN202
		# A rule is called silently to ask whether its block interrupts a paragraph.
		if state.is_code_block(start):
			return False
		line = state.src[state.bMarks[start] + state.tShift[start] : state.eMarks[start]]
		kind = html_block_start(line, silent, state.eMarks[start] >= len(state.src))
		if not kind or silent:
			return bool(kind)
		stop, k = _HTML_END.get(kind), start + 1
		if not (stop and stop.search(line)):
			while k < end and state.sCount[k] >= state.blkIndent:
				text = state.src[state.bMarks[k] + state.tShift[k] : state.eMarks[k]]
				if stop is None and not text:
					break
				k += 1
				if stop and stop.search(text):
					break
		state.line = k
		token = state.push("html_block", "", 0)
		token.map = [start, k]
		token.content = state.getLines(start, k, state.blkIndent, True)
		return True

	def ref(state, start, end, silent):  # noqa: ANN001, ANN202
		# A definition ends before a setext underline: `[a]:` over `===` is a heading.
		if not state.src.startswith("[", state.bMarks[start] + state.tShift[start]):
			return False
		k, top = start + 1, state.lineMax
		while k < top and not state.isEmpty(k):
			if state.sCount[k] - state.blkIndent < 4 and _UNDERLINE.fullmatch(
				state.src, state.bMarks[k] + state.tShift[k], state.eMarks[k]
			):
				break
			k += 1
		state.lineMax = k
		try:
			ok = reference(state, start, end, silent)
		finally:
			state.lineMax = top
		if ok and not silent:
			state.env["_wumd_ref"] = state.line
		return ok

	def continued(state, start, end, silent):  # noqa: ANN001, ANN202
		if silent or state.env.get("_wumd_ref") != start:
			return False
		if (
			0 <= state.sCount[start] - state.blkIndent <= 3
		):  # else a lazy continuation line
			parent, state.parentType = state.parentType, "paragraph"
			stop = any(
				r(state, start, end, True) for r in md.block.ruler.getRules("paragraph")
			)
			state.parentType = parent
			if stop:
				return False
		return (
			ref(state, start, end, False)
			or setext(state, start, end, False)
			or para(state, start, end, False)
		)

	for k, fn in (
		("heading", atx),
		("lheading", setext),
		("html_block", html_block),
		("reference", ref),
		("paragraph", para),
	):
		md.block.ruler.at(k, fn, {"alt": rules[k].alt})
	md.block.ruler.before("table", "wumd_continued", continued)
	_PARSER = md
	return md


def block_parse(text: str, refs: dict | None = None) -> list[Token]:
	"""
	The block tokens of decoded text; inline tokens not parsed. refs, every
	link reference definition known, gains those of text.
	"""
	md, out = parser(), []
	md.block.parse(text, md, {"references": {} if refs is None else refs}, out)
	return out


MAX_MARKDOWN = 1 << 30  # what a compressed file may unpack to (R2.4)
_INVALID_BYTE = re.compile("[\x00\udc80-\udcff]")  # one U+FFFD each, as Go decodes


def decode(b: bytes) -> str:
	"""R2.1."""
	s = newlines(b.removeprefix(b"\xef\xbb\xbf").decode("utf-8", "surrogateescape"))
	return _INVALID_BYTE.sub("\ufffd", s)


def load(path: str) -> str:
	"""The decoded text of a file, gzip-compressed (`.gz`, `.dz`) or not."""
	if not path.lower().endswith((".gz", ".dz")):
		with open(path, "rb") as f:
			return decode(f.read())
	try:
		with gzip.open(path, "rb") as f:
			b = f.read(MAX_MARKDOWN + 1)
	except (OSError, EOFError, zlib.error) as e:
		raise FormatError("E-format", f"not a gzip stream: {e}") from e
	if len(b) > MAX_MARKDOWN:
		raise FormatError("E-format", f"decompressed markdown over {MAX_MARKDOWN} bytes")
	return decode(b)


def head_lines(s: str, n: int) -> list[str]:
	"""The first n lines of s, "" past its end, without copying the rest of s."""
	end = -1
	for _ in range(n):
		end = s.find("\n", end + 1)
		if end < 0:
			end = len(s)
			break
	return [*s[:end].split("\n"), *[""] * n][:n]


def check_header(text: str) -> None:
	"""R3.1: the title line and the version line."""
	line1, line2 = head_lines(text, 2)
	if not (
		len(line1) > 2
		and line1[0] == "#"
		and line1[1] in " \t"
		and line1[1:].strip(" \t")
	):
		raise FormatError("E-format", "line 1 must be `# ` and the dictionary title")
	k = line2[:6]
	if not (
		k.isascii() and k.lower() == "wudict" and line2[6:].lstrip(" \t").startswith(":")
	):
		raise FormatError(
			"E-format", "line 2 must be `wudict: 1`, the version of the format"
		)
	kv = parse_field(line2)
	if not kv or kv[0] != "wudict":
		raise FormatError("E-version", "line 2 must be `wudict: 1`")
	v = kv[1]
	if not re.fullmatch("[0-9]+(?:\\.[0-9]+)?", v, re.ASCII):
		raise FormatError("E-version", f"line 2 must be `wudict: 1`, not {v!r}")
	if v.partition(".")[0].lstrip("0") != "1":
		raise FormatError(
			"E-version", f"version {v} is not supported; this reader reads `wudict: 1`"
		)


def parse_field(line: str) -> tuple[str, str] | None:
	"""`key: value` (R3.2)."""
	m = re.match("([a-z][a-z0-9-]*):[ \t](.*)", line, re.DOTALL)
	return (m[1], v) if m and (v := m[2].strip(" \t")) else None


def top_blocks(tokens: list[Token], stop: int | None = None) -> list[tuple[int, int]]:
	"""
	The top-level blocks of a token stream, before token stop, as (first,
	last) index pairs.
	"""
	out, i, n = [], 0, len(tokens) if stop is None else stop
	while i < n:
		j, depth = i + 1, tokens[i].nesting
		while depth > 0:
			depth += tokens[j].nesting
			j += 1
		out.append((i, j - 1))
		i = j
	return out


_CANDIDATE = re.compile("^##(?=[ \t]|$)", re.MULTILINE)  # a line that may start an entry


def _swallowed(line: str, start: int) -> str:
	return (
		f"{go_quote(clip(line))} is inside the HTML block that starts on line {start}, so"
		" it is not an entry; end that block before it (a blank line, or its closing tag)"
	)


def clip(s: str) -> str:
	"""A line quoted in a warning, cut at 60 bytes."""
	b = s.rstrip("\r").encode()
	return b[:60].decode(errors="ignore") + "\u2026" if len(b) > 60 else s.rstrip("\r")


def go_quote(s: str) -> str:
	"""strconv.Quote."""
	out = ['"']
	for c in s:
		if c in '"\\':
			out.append("\\" + c)
		elif c.isprintable():
			out.append(c)
		else:
			o = ord(c)
			esc = {7: "a", 8: "b", 9: "t", 10: "n", 11: "v", 12: "f", 13: "r"}.get(o)
			out.append(
				"\\" + esc
				if esc
				else f"\\x{o:02x}"
				if o < 0x80
				else f"\\u{o:04x}"
				if o < 0x10000
				else f"\\U{o:08x}"
			)
	return "".join(out) + '"'


def _is_h2(t: Token) -> bool:
	"""A heading that starts an entry (R3.5): `## `; a setext one is content."""
	return t.type == "heading_open" and t.markup == "##"


_INLINE_SYNTAX = re.compile(
	r"[\n!#$%&*+\-:<=>@\[\\\]^_`{}~]"
)  # markdown-it's terminators


def plain(children: list[Token]) -> str:
	"""R3.4: the text content of inline tokens."""
	out = []
	for c in children:
		if c.type in ("text", "text_special", "code_inline"):
			out.append(c.content)
		elif c.type in ("softbreak", "hardbreak"):
			out.append(" ")
		elif c.type == "image":
			out.append(plain(c.children or []))
	return "".join(out)


class Entry:
	__slots__ = ("chunk", "folded", "group", "line", "names", "see")

	def __init__(
		self, names: list[str], chunk: int, group: int, line: int, see: str
	) -> None:
		self.names, self.chunk, self.group, self.line, self.see = (
			names,
			chunk,
			group,
			line,
			see,
		)
		self.folded = False


class Document:
	"""
	A dictionary read from decoded text: meta, warnings, and (names, HTML)
	for each article.

	As in the Go reader, the text is parsed in chunks of about CHUNK_SIZE, cut
	where the parser confirms a top-level heading group starts: a top-level
	heading closes every block, so the chunks parse as the whole text does. The
	first pass reads the block structure; headings are read when every link
	reference definition is known, and each chunk is parsed again for its
	bodies when iteration reaches it.
	"""

	def __init__(self, text: str) -> None:
		check_header(text)
		self.text = text
		self.meta = {"name": "", "from": "", "to": "", "fields": [], "description": ""}
		self.refs: dict = {}
		self.chunks: list[tuple[int, int]] = []
		self.entries: list[Entry] = []
		# Each warning keyed (chunk, step, line), the order wudict says them in:
		# per chunk, the header's, the swallowed lines', the heading groups'.
		self._warns: list[tuple[tuple[int, int, int], str]] = []
		self._cands = [m.start() for m in _CANDIDATE.finditer(text)]
		self._title = ""  # its heading's content
		self._desc = 0  # where the description ends, 0 for none
		start, line = 0, 1
		while start < len(text):
			end, tokens, stop = self._next_chunk(start)
			self._scan(len(self.chunks), tokens, stop, text[start:end], line)
			self.chunks.append((start, end))
			line += text.count("\n", start, end)
			start = end
		# Headings read last, with every link reference definition known.
		self.meta["name"] = self._heading_text(self._title)
		if not self.meta["name"]:
			raise FormatError("E-format", "the title on line 1 is empty")
		self._name()
		self._fold()
		self.warnings = [
			f"W-entry: {key[2]}: {msg}"
			for key, msg in sorted(self._warns, key=lambda w: w[0])
		]
		if self._desc:
			tokens = parser().parse(text[: self._desc], {"references": self.refs})
			self.meta["description"] = _render(tokens, top_blocks(tokens)[2:])

	def _next_chunk(self, start: int) -> tuple[int, list[Token], int | None]:
		"""
		Where the chunk from start ends, the tokens it was confirmed with
		(which may run on into the next chunk), and the token it stops at.
		"""
		text, cands = self.text, self._cands
		k = bisect.bisect_left(cands, start + max(CHUNK_SIZE, 1))
		while k < len(cands):
			c = cands[k]
			le = text.find("\n", c) + 1 or len(text)
			tokens = block_parse(text[start:le], self.refs)
			blocks = top_blocks(tokens)
			line = text.count("\n", start, c)
			t = tokens[blocks[-1][0]]
			if _is_h2(t) and t.map[0] == line:
				g = len(blocks) - 1
				while g > 0 and _is_h2(tokens[blocks[g - 1][0]]):
					g -= 1
				if g > 0:  # the group starts after the chunk's start
					return (
						_offset(text, tokens[blocks[g][0]].map[0], start),
						tokens,
						blocks[g][0],
					)
			# Inside a block, or not a group's first heading: the window
			# doubles, so the work stays linear.
			k = bisect.bisect_left(cands, max(c + 1, start + 2 * (c - start)))
		return len(text), block_parse(text[start:], self.refs), None

	def _scan(
		self, ci: int, tokens: list[Token], stop: int | None, chunk: str, line0: int
	) -> None:  # noqa: PLR0913
		"""Read a chunk's heading groups (R3.5), and the header in the first."""
		blocks = top_blocks(tokens, stop)
		lines = None
		i = self._header(tokens, blocks, stop) if ci == 0 else 0
		# R3.5: a line that would start an entry, inside an HTML block, is content
		for a, _ in blocks:
			if tokens[a].type == "html_block" and tokens[a].map[1] - tokens[a].map[0] > 1:
				lines = lines or chunk.split("\n")
				l0, l1 = tokens[a].map
				for k in range(l0 + 1, l1):
					if _CANDIDATE.match(lines[k]):
						self._warns.append(
							((ci, 1, line0 + k), _swallowed(lines[k], line0 + l0))
						)
		group = 0
		while i < len(blocks):
			at = tokens[blocks[i][0]]
			heads = []
			while i < len(blocks) and _is_h2(tokens[blocks[i][0]]):
				heads.append(tokens[blocks[i][0] + 1].content)
				i += 1
			body = i
			while i < len(blocks) and not _is_h2(tokens[blocks[i][0]]):
				i += 1
			line = line0 + at.map[0]
			if body == i:
				self._warns.append(
					((ci, 2, line), "heading group without a body; skipped")
				)
			else:
				see = ""
				t = tokens[blocks[body][0]]
				if (
					i - body == 1
					and t.type == "paragraph_open"
					and t.map[1] - t.map[0] == 1
					and tokens[blocks[body][0] + 1].content.startswith("see:")
				):
					lines = lines or chunk.split("\n")
					# the line as written, without its indentation (R3.6)
					m = re.match("see:[ \t](.*)", lines[t.map[0]].lstrip(" \t"))
					see = m[1].strip(" \t") if m else ""
				self.entries.append(Entry(heads, ci, group, line, see))
			group += 1

	def _header(
		self, tokens: list[Token], blocks: list[tuple[int, int]], stop: int | None
	) -> int:
		"""Read the header (R3.1-R3.3); the index of the first entry's block."""
		t = tokens[0]
		if t.type != "heading_open" or t.tag != "h1":
			raise FormatError("E-format", "line 1 must be `# ` and the dictionary title")
		self._title = tokens[1].content  # read again once every definition is known
		if not self._heading_text(self._title):
			raise FormatError("E-format", "the title on line 1 is empty")
		if len(blocks) > 1 and tokens[blocks[1][0]].markup in ("-", "="):
			raise FormatError(
				"E-format",
				"the header must end at a blank line: "
				"the `---` or `===` line under it makes it a heading",
			)
		if (
			len(blocks) < 2
			or (p := tokens[blocks[1][0]]).type != "paragraph_open"
			or p.map[0] != 1
		):
			raise FormatError(
				"E-format", "line 2 must be `wudict: 1`, directly under the title"
			)
		meta = self.meta
		for i, ln in enumerate(head_lines(self.text, p.map[1])[1:], 2):
			kv = parse_field(
				ln.lstrip(" \t")
			)  # a paragraph line, without its indentation
			if not kv:
				msg = (
					f"header line {i} is not `key: value`; it and the rest of the header"
				)
				self._warns.append(((0, 0, i), msg + " are ignored"))
				break
			k, v = kv
			if k in ("from", "to"):
				meta[k] = meta[k] or v
			elif k != "wudict":
				meta["fields"].append((k, v))
		i = 2
		while i < len(blocks) and not _is_h2(tokens[blocks[i][0]]):
			i += 1
		if i > 2:
			first = blocks[i][0] if i < len(blocks) else stop
			self._desc = (
				len(self.text)
				if first is None
				else _offset(self.text, tokens[first].map[0])
			)
		return i

	def _heading_text(self, content: str) -> str:
		if not _INLINE_SYNTAX.search(content):
			return content
		md, children = parser(), []
		md.inline.parse(content, md, {"references": self.refs}, children)
		return plain(children).strip(" \t")

	def _name(self) -> None:
		"""Each entry's names, read with every reference definition known."""
		kept = []
		for e in self.entries:
			names: list[str] = []
			for c in e.names:
				if (t := self._heading_text(c)) and t not in names:
					names.append(t)
			if names:
				e.names = names
				kept.append(e)
			else:
				self._warns.append(
					((e.chunk, 2, e.line), "entry without a headword; skipped")
				)
		self.entries = kept

	def _fold(self) -> None:
		"""
		R3.6: a redirect's names become aliases of every article its target
		names, exactly or else ignoring case.
		"""
		exact: dict[str, list[Entry]] = {}
		folded: dict[str, list[Entry]] = {}
		for e in self.entries:
			if not e.see:
				for n in e.names:
					exact.setdefault(n, []).append(e)
					folded.setdefault(go_lower(n), []).append(e)
		for e in self.entries:
			if e.see and (targets := exact.get(e.see) or folded.get(go_lower(e.see))):
				e.folded = True
				for a in targets:
					a.names += [n for n in e.names if n not in a.names]

	def __iter__(self) -> Iterator[tuple[list[str], str]]:
		"""(names, HTML) of each article, in file order."""
		cur, groups = -1, []
		for e in self.entries:
			if e.folded:
				continue
			if e.see:
				href = go_html_escape("entry://" + enc_target(e.see))
				yield e.names, f'<p><a href="{href}">{go_html_escape(e.see)}</a></p>\n'
				continue
			if e.chunk != cur:
				cur = e.chunk
				s, end = self.chunks[cur]
				tokens = parser().parse(self.text[s:end], {"references": self.refs})
				groups = list(_bodies(tokens, top_blocks(tokens), cur == 0))
			yield e.names, _render(*groups[e.group])

	def __len__(self) -> int:
		return sum(not e.folded for e in self.entries)


def _offset(s: str, line: int, at: int = 0) -> int:
	"""Where the line-th line after offset at starts."""
	for _ in range(line):
		at = s.index("\n", at) + 1
	return at


def _bodies(
	tokens: list[Token], blocks: list[tuple[int, int]], first: bool
) -> Iterator[tuple[list[Token], list[tuple[int, int]]]]:
	"""(tokens, body blocks) of each heading group."""
	i = 0
	if first:
		i = 2
		while i < len(blocks) and not _is_h2(tokens[blocks[i][0]]):
			i += 1
	while i < len(blocks):
		while i < len(blocks) and _is_h2(tokens[blocks[i][0]]):
			i += 1
		body = i
		while i < len(blocks) and not _is_h2(tokens[blocks[i][0]]):
			i += 1
		yield tokens, blocks[body:i]


def _render(tokens: list[Token], blocks: list[tuple[int, int]]) -> str:
	if not blocks:
		return ""
	md = parser()
	return md.renderer.render(tokens[blocks[0][0] : blocks[-1][1] + 1], md.options, {})


CHUNK_SIZE = 1 << 20


def read_text(text: str) -> Document:
	"""A dictionary from decoded text (decode); raises FormatError."""
	return Document(text)
