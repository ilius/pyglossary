from __future__ import annotations

from os.path import splitext
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape, quoteattr

from pyglossary.core import log

if TYPE_CHECKING:
	from ._types import ErrorType, LexType, TransformerType

__all__ = ["lexRoot"]


# rename to lexText?
def lexRoot(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.start < tr.pos:
		log.warning(f"incomplete buffer near pos {tr.pos}")

	if tr.end():
		# if tr.openParenth > 0:
		# 	return None, "unexpected: unclosed '('"
		return None, None

	c = tr.next()
	if tr.end():
		tr.addText(c)
		return None, None

	if c == "\\":
		return lexBackslash, None

	if c == "[":
		tr.resetBuf()
		return lexTag, None

	if c == "]":
		tr.next()
		if tr.follows("["):
			tr.next()
		tr.output += c
		tr.resetBuf()
		return lexRoot, None

	if c == "~":
		tr.addText(tr.currentKey)
		tr.resetBuf()
		return lexRoot, None

	if c == "\n":
		return lexRootNewline, None

	if c == "<" and tr.follows("<"):
		tr.next()
		return lexRefText, None

	tr.addText(c)
	tr.resetBuf()

	return lexRoot, None


def lexRootNewline(tr: TransformerType) -> tuple[LexType, ErrorType]:
	tr.skipAny(" \t")
	if not tr.follows("[m"):
		tr.addHtml("<br/>")
	tr.resetBuf()
	return lexRoot, None


def lexBackslash(tr: TransformerType) -> tuple[LexType, ErrorType]:
	c = tr.next()
	if c == " ":
		tr.addHtml("&nbsp;")
	elif c in "<>" and tr.follows(c):
		tr.next()
		tr.addText(2 * c)
	else:
		tr.addText(c)
	tr.resetBuf()
	return lexRoot, None


def lexTag(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.end():
		return None, f"'[' not closed near pos {tr.pos} in lexTag"
	c = tr.next()
	if c == "[":
		tr.output += c
		tr.resetBuf()
		return lexRoot, None
	if c in " \t":
		tr.skipAny(" \t")
		return lexTagAttr, None
	if c == "]":
		tag = tr.input[tr.start : tr.pos - 1]
		if not tag:
			return None, f"empty tag near pos {tr.pos}"
		return processTag(tr, tag)
	# if c == '\\':
	# 	return lexTagBackslash, None
	# do not advance tr.start
	return lexTag, None


def lexTagAttr(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.end():
		tr.attrs[tr.attrName] = None
		tr.resetBuf()
		return lexRoot, None
	c = tr.next()
	if c == "]":
		tr.attrs[tr.attrName] = None
		tr.move(-1)
		return lexTag, None
	if c == "=":
		tr.skipAny(" \t")
		return lexTagAttrValue, None
	tr.attrName += c
	return lexTagAttr, None


def lexTagAttrValue(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.end():
		return None, f"'[' not closed near pos {tr.pos} in lexTagAttrValue(1)"
	c = tr.next()
	quote = ""
	value = ""
	if c in "'\"":
		if tr.end():
			return None, f"'[' not closed near pos {tr.pos} in lexTagAttrValue(2)"
		quote = c
	else:
		value += c
	while True:
		if tr.end():
			return None, f"'[' not closed near pos {tr.pos} in lexTagAttrValue(3)"
		c = tr.next()
		if c == "\\":
			if tr.end():
				return None, f"'[' not closed near pos {tr.pos} in lexTagAttrValue(3)"
			c = tr.next()
			value += c
			continue
		if c == "]":
			tr.move(-1)
			break
		if c == quote:
			break
		if not quote and c in " \t":
			break
		value += c
	tr.attrs[tr.attrName] = value
	return lexTag, None


r"""
[m{}] => <p style="padding-left:{}em;margin:0">
[*]   => <span class="sec">
[ex]  => <span class="ex"><font color="{exampleColor}">
[c]   => <font color="green">
[p]   => <i class="p"><font color="green">

[']   => <u>
[b]   => <b>
[i]   => <i>
[u]   => <u>
[sup] => <sup>
[sub] => <sub>

[ref]   \
[url]    } => <a href={}>{}</a>
<<...>> /

[s] =>  <object type="audio/x-wav" data="{}" width="40" height="40">
			<param name="autoplay" value="false" />
		</object>
[s] =>  <img align="top" src="{}" alt="{}" />

[t] => <font face="Helvetica" class="dsl_t">

{{...}}   \
[trn]      |
[!trn]     |
[trs]      } => remove
[!trs]     |
[lang ...] |
[com]     /
"""


def lexRefText(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.end():
		return None, None

	text = ""
	while not tr.end():
		c = tr.next()
		if c == "\\":
			if tr.end():
				break
			text += tr.next()
			continue
		if c == "[":
			tr.move(-1)
			break
		if c == ">" and tr.follows(">"):
			tr.next()
			break
		text += c

	target = tr.attrs.get("target")
	if not target:
		target = text

	tr.addHtml(f'<a href={quoteattr("bword://" + target)}>{escape(text)}</a>')
	tr.resetBuf()
	return lexRoot, None


def lexUrlText(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.end():
		return None, None

	text = ""
	while not tr.end():
		c = tr.next()
		if c == "\\":
			if tr.end():
				break
			text += tr.next()
			continue
		if c == "[":
			tr.move(-1)
			break
		text += c

	target = tr.attrs.get("target")
	if not target:
		target = text

	if "://" not in target:
		target = "http://" + target

	tr.addHtml(f"<a href={quoteattr(target)}>{escape(text)}</a>")
	tr.resetBuf()
	return lexRoot, None


def lexTagS(tr: TransformerType) -> tuple[LexType, ErrorType]:
	if tr.end():
		return None, None

	fname = ""
	while not tr.end():
		c = tr.next()
		if c == "[":
			tr.move(-1)
			break
		fname += c

	_, ext = splitext(fname)
	ext = ext.lstrip(".")
	if ext in {"wav", "mp3"}:
		if tr.audio:
			tr.addHtml(
				rf'<object type="audio/x-wav" data="{fname}" '
				'width="40" height="40">'
				'<param name="autoplay" value="false" />'
				"</object>"
			)
	elif ext in {"jpg", "jpeg", "gif", "tif", "tiff", "png", "bmp"}:
		tr.addHtml(rf'<img align="top" src="{fname}" alt="{fname}" />')
	else:
		log.warning(f"unknown file extension in {fname!r}")

	tr.resFileSet.add(fname)

	tr.resetBuf()
	return lexRoot, None


def processTagM(tr: TransformerType, tag: str) -> tuple[LexType, ErrorType]:
	padding = "0.3"
	if len(tag) > 1:
		padding = tag[1:]
		if padding == "0":
			padding = "0.3"
	tr.addHtml(f'<p style="padding-left:{padding}em;margin:0">')
	tr.resetBuf()
	return lexRoot, None


def lexTagC(tr: TransformerType) -> tuple[LexType, ErrorType]:
	color = "green"
	for key, value in tr.attrs.items():
		if value is None:
			color = key
			break
	tr.addHtml(f'<font color="{color}">')
	tr.resetBuf()
	return lexRoot, None


# PLR0912 Too many branches (19 > 12)
def processTag(tr: TransformerType, tag: str) -> tuple[LexType, ErrorType]:  # noqa: PLR0912
	tr.attrName = ""
	if not tag:
		tr.resetBuf()
		return lexRoot, None

	if tag[0] == "/":
		tr.closeTag(tag[1:])
		return lexRoot, None

	tag = tag.split(" ")[0]

	if tag == "ref":
		return lexRefText(tr)

	if tag == "url":
		return lexUrlText(tr)

	if tag == "s":
		return lexTagS(tr)

	if tag == "c":
		return lexTagC(tr)

	if tag[0] == "m":
		return processTagM(tr, tag)

	if tag == "p":
		tr.labelOpen = True
		tr.resetBuf()
		return lexRoot, None

	if tag == "*":
		tr.addHtml('<span class="sec">')
	elif tag == "ex":
		tr.addHtml(f'<span class="ex"><font color="{tr.exampleColor}">')
	elif tag == "t":
		tr.addHtml('<font face="Helvetica" class="dsl_t">')
	elif tag == "i":
		tr.addHtml("<i>")
	elif tag == "b":
		tr.addHtml("<b>")
	elif tag == "u":
		tr.addHtml("<u>")
	elif tag == "'":
		tr.addHtml('<u class="accent">')
	elif tag == "sup":
		tr.addHtml("<sup>")
	elif tag == "sub":
		tr.addHtml("<sub>")
	elif tag in {
		"trn",
		"!trn",
		"trs",
		"!trs",
		"lang",
		"com",
	}:
		pass
	else:
		log.warning(f"unknown tag {tag!r}")

	tr.resetBuf()
	return lexRoot, None


# def lexTagBackslash(tr: TransformerType) -> tuple[LexType, ErrorType]:
