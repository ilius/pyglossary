from os.path import splitext
from typing import Tuple
from xml.sax.saxutils import escape, quoteattr

from pyglossary.core import log

from ._types import ErrorType, LexType, TransformerType


# rename to lexText?
def lexRoot(tr: TransformerType) -> Tuple[LexType, ErrorType]:
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
		# if tr.openBracket:
		# 	return None, "nested '['"
		# tr.openBracket = true
		tr.resetBuf()
		return lexTag, None

	if c == "~":
		tr.addText(tr.current_key)
		tr.resetBuf()
		return lexRoot, None

	if c == "\n":
		return lexRootNewline, None

	tr.addText(c)
	tr.resetBuf()
	return lexRoot, None


def lexRootNewline(tr: TransformerType) -> Tuple[LexType, ErrorType]:
	tr.skipChars(" \t")
	if not tr.followsString("[m"):
		tr.output += "<br/>"
	tr.resetBuf()
	return lexRoot, None


def lexBackslash(tr: TransformerType) -> Tuple[LexType, ErrorType]:
	c = tr.next()
	if c == " ":
		tr.output += "&nbsp;"
	else:
		tr.addText(c)
	tr.resetBuf()
	return lexRoot, None


def lexTag(tr: TransformerType) -> Tuple[LexType, ErrorType]:
	if tr.end():
		return None, f"'[' not closed near pos {tr.pos}"
	c = tr.next()
	if c == '[':
		return None, f"nested '[' near pos {tr.pos}"
	if c == ']':
		tag = tr.input[tr.start:tr.pos-1]
		if not tag:
			return None, f"empty tag near pos {tr.pos}"
		return processTag(tr, tag)
	# if c == '\\':
	# 	return lexTagBackslash, None
	# do not advance tr.start
	return lexTag, None


def processTagClose(tr: TransformerType, tag: str) -> Tuple[LexType, ErrorType]:
	if not tag:
		return None, f"empty close tag {tag!r}"
	if tag == "m":
		tr.output += "</p>"
	elif tag == "b":
		tr.output += "</b>"
	elif tag in ("u", "'"):
		tr.output += "</u>"
	elif tag == "i":
		tr.output += "</i>"
	elif tag == "sup":
		tr.output += "</sup>"
	elif tag == "sub":
		tr.output += "</sub>"
	elif tag == "c":
		tr.output += "</font>"
	elif tag == "t":
		tr.output += "</font>"
	elif tag == "p":
		tr.output += "</font></i>"
	elif tag == "*":
		tr.output += "</span>"
	elif tag == "ex":
		tr.output += "</font></span>"
	elif tag in ("ref", "url", "s"):
		pass
	elif tag in (
		"trn",
		"!trn",
		"trs",
		"!trs",
		"lang",
		"com",
	):
		pass
	else:
		print(f"unknown close tag {tag!r}")
	return lexRoot, None


r"""
[m{}] => <p style="padding-left:{}em;margin:0">
[*]   => <span class="sec">
[ex]  => <span class="ex"><font color="{example_color}">
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

def lexRef(tr: TransformerType) -> Tuple[LexType, ErrorType]:
	if tr.end():
		return None, None

	target = ""
	while not tr.end():
		c = tr.next()
		if c == "\\":
			if tr.end():
				break
			target += tr.next()
			continue
		if c == "[":
			tr.move(-1)
			break
		target += c

	tr.output += f'<a href={quoteattr("bword://"+target)}>{escape(target)}</a>'
	tr.resetBuf()
	return lexRoot, None


def lexUrl(tr: TransformerType) -> Tuple[LexType, ErrorType]:
	if tr.end():
		return None, None

	target = ""
	while not tr.end():
		c = tr.next()
		if c == "\\":
			if tr.end():
				break
			target += tr.next()
			continue
		if c == "[":
			tr.move(-1)
			break
		target += c

	if "://" not in target:
		target = "http://" + target

	tr.output += f'<a href={quoteattr(target)}>{escape(target)}</a>'
	tr.resetBuf()
	return lexRoot, None


def lexS(tr: TransformerType) -> Tuple[LexType, ErrorType]:
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
	if ext in ("wav", "mp3"):
		if tr.audio:
			tr.output += (
				rf'<object type="audio/x-wav" data="{fname}" '
				"width=\"40\" height=\"40\">"
				"<param name=\"autoplay\" value=\"false\" />"
				"</object>"
			)
	elif ext in ("jpg", "jpeg", "gif", "tif", "tiff", "png", "bmp"):
		tr.output += rf'<img align="top" src="{fname}" alt="{fname}" />'
	else:
		print(f"unknown file extension in {fname!r}")

	tr.resFileSet.add(fname)

	tr.resetBuf()
	return lexRoot, None


def processTag(tr: TransformerType, tag: str) -> Tuple[LexType, ErrorType]:
	if not tag:
		tr.resetBuf()
		return lexRoot, None
	if tag[0] == "/":
		lex, err = processTagClose(tr, tag[1:])
		if err:
			return None, err
		tr.resetBuf()
		return lex, None

	tagFull = tag
	tagParts = tag.split(" ")
	tag = tagParts[0]

	if tag == "ref":
		return lexRef(tr)

	if tag == "url":
		return lexUrl(tr)

	if tag == "s":
		return lexS(tr)

	if tag[0] == "m":
		padding = "0.3"
		if len(tag) > 1:
			padding = tag[1:]
			if padding == "0":
				padding = "0.3"
		tr.output += f'<p style="padding-left:{padding}em;margin:0">'

	elif tag == "*":
		tr.output += '<span class="sec">'

	elif tag == "ex":
		tr.output += f'<span class="ex"><font color="{tr.example_color}">'

	elif tag == "c":
		if len(tagParts) > 1:
			tr.output += f'<font color="{tagFull[2:]}">'
		else:
			tr.output += '<font color="green">'

	elif tag == "t":
		tr.output += '<font face="Helvetica" class="dsl_t">'

	elif tag == "p":
		tr.output += '<i class="p"><font color="green">'
	elif tag == "i":
		tr.output += "<i>"
	elif tag == "b":
		tr.output += "<b>"
	elif tag == "u":
		tr.output += "<u>"
	elif tag == "'":
		tr.output += '<u class="accent">'
	elif tag == "sup":
		tr.output += "<sup>"
	elif tag == "sub":
		tr.output += "<sub>"
	elif tag in (
		"trn",
		"!trn",
		"trs",
		"!trs",
		"lang",
		"com",
	):
		pass
	else:
		print(f"unknown tag {tag!r}")

	tr.resetBuf()
	return lexRoot, None


# def lexTagBackslash(tr: TransformerType) -> Tuple[LexType, ErrorType]:
