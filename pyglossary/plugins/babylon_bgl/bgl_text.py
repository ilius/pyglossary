# -*- coding: utf-8 -*-
#
# Copyright © 2008-2021 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2011-2012 kubtek <kubtek@gmail.com>
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
# Thanks to Raul Fernandes <rgfbr@yahoo.com.br> and Karl Grill for reverse
# engineering as part of https://sourceforge.net/projects/ktranslator/
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from __future__ import annotations

import re

from pyglossary import core
from pyglossary.core import log
from pyglossary.xml_utils import xml_escape

__all__ = [
	"fixImgLinks",
	"normalizeNewlines",
	"removeControlChars",
	"removeNewlines",
	"replaceAsciiCharRefs",
	"replaceHtmlEntries",
	"replaceHtmlEntriesInKeys",
	"stripDollarIndexes",
	"stripHtmlTags",
	"unknownHtmlEntries",
]


u_pat_html_entry = re.compile("(?:&#x|&#|&)(\\w+);?", re.IGNORECASE)
u_pat_html_entry_key = re.compile("(?:&#x|&#|&)(\\w+);", re.IGNORECASE)
b_pat_ascii_char_ref = re.compile(b"(&#\\w+;)", re.IGNORECASE)
u_pat_newline_escape = re.compile("[\\r\\n\\\\]")
u_pat_strip_tags = re.compile("(?:<[/a-zA-Z].*?(?:>|$))+")
u_pat_control_chars = re.compile("[\x00-\x08\x0c\x0e-\x1f]")
u_pat_newline = re.compile("[\r\n]+")

unknownHtmlEntries = set()


def replaceHtmlEntryNoEscapeCB(u_match: re.Match) -> str:
	"""
	u_match: instance of _sre.SRE_Match
	Replace character entity with the corresponding character.

	Return the original string if conversion fails.
	Use this as a replace function of re.sub.
	"""
	from pyglossary.html_utils import name2codepoint

	u_text = u_match.group(0)
	u_name = u_match.group(1)
	if core.isDebug():
		assert isinstance(u_text, str)
		assert isinstance(u_name, str)

	if u_text[:2] == "&#":
		# character reference
		try:
			code = int(u_name, 16) if u_text[:3].lower() == "&#x" else int(u_name)
			if code <= 0:
				raise ValueError(f"{code = }")
			return chr(code)
		except (ValueError, OverflowError):
			return chr(0xFFFD)  # replacement character
	elif u_text[0] == "&":
		"""
		Babylon dictionaries contain a lot of non-standard entity,
		references for example, csdot, fllig, nsm, cancer, thlig,
		tsdot, upslur...
		This not just a typo. These entries repeat over and over again.
		Perhaps they had meaning in the source dictionary that was
		converted to Babylon, but now the meaning is lost. Babylon
		does render them as is, that is, for example, &csdot; despite
		other references like &amp; are replaced with corresponding
		characters.
		"""
		# named entity
		try:
			return chr(name2codepoint[u_name.lower()])
		except KeyError:
			unknownHtmlEntries.add(u_text)
			return u_text

	raise ValueError(f"{u_text[0] =}")


def replaceHtmlEntryCB(u_match: re.Match) -> str:
	"""
	u_match: instance of _sre.SRE_Match
	Same as replaceHtmlEntryNoEscapeCB, but escapes result string.

	Only <, >, & characters are escaped.
	"""
	u_res = replaceHtmlEntryNoEscapeCB(u_match)
	if u_match.group(0) == u_res:  # conversion failed
		return u_res
	# FIXME: should " and ' be escaped?
	return xml_escape(u_res, quotation=False)


# def replaceDingbat(u_match: "re.Match") -> str:
# 	r"""Replace chars \\u008c-\\u0095 with \\u2776-\\u277f."""
# 	ch = u_match.group(0)
# 	code = ch + 0x2776 - 0x8C
# 	return chr(code)


def escapeNewlinesCallback(u_match: re.Match) -> str:
	"""u_match: instance of _sre.SRE_Match."""
	ch = u_match.group(0)
	if ch == "\n":
		return "\\n"
	if ch == "\r":
		return "\\r"
	if ch == "\\":
		return "\\\\"
	return ch


def replaceHtmlEntries(u_text: str) -> str:
	# &ldash;
	# &#0147;
	# &#x010b;
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_html_entry.sub(
		replaceHtmlEntryCB,
		u_text,
	)


def replaceHtmlEntriesInKeys(u_text: str) -> str:
	# &ldash;
	# &#0147;
	# &#x010b;
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_html_entry_key.sub(
		replaceHtmlEntryNoEscapeCB,
		u_text,
	)


def escapeNewlines(u_text: str) -> str:
	r"""
	Convert text to c-escaped string:
	\ -> \\
	new line -> \n or \r.
	"""
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_newline_escape.sub(
		escapeNewlinesCallback,
		u_text,
	)


def stripHtmlTags(u_text: str) -> str:
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_strip_tags.sub(
		" ",
		u_text,
	)


def removeControlChars(u_text: str) -> str:
	# \x09 - tab
	# \x0a - line feed
	# \x0b - vertical tab
	# \x0d - carriage return
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_control_chars.sub(
		"",
		u_text,
	)


def removeNewlines(u_text: str) -> str:
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_newline.sub(
		" ",
		u_text,
	)


def normalizeNewlines(u_text: str) -> str:
	"""Convert new lines to unix style and remove consecutive new lines."""
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_pat_newline.sub(
		"\n",
		u_text,
	)


def replaceAsciiCharRefs(b_text: bytes) -> bytes:
	# &#0147;
	# &#x010b;
	if core.isDebug():
		assert isinstance(b_text, bytes)
	b_parts = b_pat_ascii_char_ref.split(b_text)
	for i_part, b_part in enumerate(b_parts):
		if i_part % 2 != 1:
			continue
		# reference
		try:
			code = (
				int(b_part[3:-1], 16)
				if b_part[:3].lower() == "&#x"
				else int(b_part[2:-1])
			)
			if code <= 0:
				raise ValueError(f"{code = }")
		except (ValueError, OverflowError):
			code = -1
		if code < 128 or code > 255:
			continue
		# no need to escape "<", ">", "&"
		b_parts[i_part] = bytes([code])
	return b"".join(b_parts)


def fixImgLinks(u_text: str) -> str:
	r"""
	Fix img tag links.

	src attribute value of image tag is often enclosed in \x1e - \x1f
	characters.
	For example:
		<IMG border='0' src='\x1e6B6C56EC.png\x1f' width='9' height='8'>.
	Naturally the control characters are not part of the image source name.
	They may be used to quickly find all names of resources.
	This function strips all such characters.
	Control characters \x1e and \x1f are useless in html text, so we may
	safely remove all of them, irrespective of context.
	"""
	if core.isDebug():
		assert isinstance(u_text, str)
	return u_text.replace("\x1e", "").replace("\x1f", "")


def stripDollarIndexes(b_word: bytes) -> tuple[bytes, int]:
	if core.isDebug():
		assert isinstance(b_word, bytes)
	i = 0
	b_word_main = b""
	strip_count = 0  # number of sequences found
	# strip $<index>$ sequences
	while True:
		d0 = b_word.find(b"$", i)
		if d0 == -1:
			b_word_main += b_word[i:]
			break
		d1 = b_word.find(b"$", d0 + 1)
		if d1 == -1:
			# log.debug(
			# 	f"stripDollarIndexes({b_word}):\npaired $ is not found",
			# )
			b_word_main += b_word[i:]
			break

		# You may find keys (or alternative keys) like these:
		# sur l'arbre$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
		# obscurantiste$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
		# They all end on a sequence of b'$', key length including dollars
		# is always 60 chars.
		# You may find keys like these:
		# extremidade-$$$-$$$-linha
		# .FIRM$$$$$$$$$$$$$
		# etc
		# summary: we must remove any sequence of dollar signs longer
		# than 1 chars
		if d1 == d0 + 1:
			# log.debug(f"stripDollarIndexes({b_word}):\nfound $$")
			b_word_main += b_word[i:d0]
			i = d1 + 1
			while i < len(b_word) and b_word[i] == ord(b"$"):
				i += 1
			if i >= len(b_word):
				break
			continue

		if b_word[d0 + 1 : d1].strip(b"0123456789"):
			# if has at least one non-digit char
			# log.debug(f"stripDollarIndexes({b_word}):\nnon-digit between $$")
			b_word_main += b_word[i:d1]
			i = d1
			continue

		# Examples:
		# make do$4$/make /do
		# potere$1$<BR><BR>
		# See also <a href='file://ITAL-ENG POTERE 1249-1250.pdf'>notes...</A>
		# volere$1$<BR><BR>
		# See also <a href='file://ITAL-ENG VOLERE 1469-1470.pdf'>notes...</A>
		# Ihre$1$Ihres
		if d1 + 1 < len(b_word) and b_word[d1 + 1] != 0x20:
			log.debug(
				f"stripDollarIndexes({b_word!r}):\n"
				"second $ is followed by non-space",
			)
		b_word_main += b_word[i:d0]
		i = d1 + 1
		strip_count += 1

	return b_word_main, strip_count
