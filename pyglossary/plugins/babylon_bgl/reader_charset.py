# -*- coding: utf-8 -*-
# mypy: ignore-errors
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

from pyglossary.core import log
from pyglossary.text_utils import excMessage

from .bgl_text import (
	removeControlChars,
	removeNewlines,
	replaceAsciiCharRefs,
	replaceHtmlEntriesInKeys,
	stripDollarIndexes,
	stripHtmlTags,
)
from .reader_data import re_b_reference, re_charset_decode

__all__ = ["_BglReaderCharset"]


class _BglReaderCharset:
	"""Headword / charset-tag decoding."""

	def charReferencesStat(self, b_text: bytes, encoding: str) -> None:
		pass

	@staticmethod
	def decodeCharsetTagsBabylonReference(b_text: bytes, b_text2: bytes) -> str:
		b_refs = b_text2.split(b";")
		add_text = ""
		for i_ref, b_ref in enumerate(b_refs):
			if not b_ref:
				if i_ref != len(b_refs) - 1:
					log.debug(
						f"decoding charset tags, b_text={b_text!r}"
						"\nblank <charset c=t> character"
						f" reference ({b_text2!r})\n",
					)
				continue
			if not re_b_reference.match(b_ref):
				log.debug(
					f"decoding charset tags, b_text={b_text!r}"
					"\ninvalid <charset c=t> character"
					f" reference ({b_text2!r})\n",
				)
				continue
			add_text += chr(int(b_ref, 16))
		return add_text

	def decodeCharsetTagsTextBlock(
		self,
		encoding: str,
		b_text: bytes,
		b_part: bytes,
	) -> str:
		b_text2 = b_part
		if encoding == "babylon-reference":
			return self.decodeCharsetTagsBabylonReference(b_text, b_text2)

		self.charReferencesStat(b_text2, encoding)
		if encoding == "cp1252":
			b_text2 = replaceAsciiCharRefs(b_text2)
		if self._strict_string_conversion:
			try:
				u_text2 = b_text2.decode(encoding)
			except UnicodeError:
				log.debug(
					f"decoding charset tags, b_text={b_text!r}"
					f"\nfragment: {b_text2!r}"
					"\nconversion error:\n" + excMessage(),
				)
				u_text2 = b_text2.decode(encoding, "replace")
		else:
			u_text2 = b_text2.decode(encoding, "replace")

		return u_text2

	def decodeCharsetTags(  # noqa: PLR0912
		self,
		b_text: bytes,
		defaultEncoding: str,
	) -> tuple[str, str]:
		"""
		b_text is a bytes
		Decode html text taking into account charset tags and default encoding.

		Return value: (u_text, defaultEncodingOnly)
		u_text is str
		defaultEncodingOnly parameter is false if the text contains parts
		encoded with non-default encoding (babylon character references
		'<CHARSET c="T">00E6;</CHARSET>' do not count).
		"""
		b_parts = re_charset_decode.split(b_text)
		u_text = ""
		encodings: list[str] = []  # stack of encodings
		defaultEncodingOnly = True
		for i, b_part in enumerate(b_parts):
			if i % 3 == 0:  # text block
				encoding = encodings[-1] if encodings else defaultEncoding
				u_text += self.decodeCharsetTagsTextBlock(encoding, b_text, b_part)
				if encoding != defaultEncoding:
					defaultEncodingOnly = False
				continue

			if i % 3 == 1:  # <charset...> or </charset>
				if b_part.startswith(b"</"):
					# </charset>
					if encodings:
						encodings.pop()
					else:
						log.debug(
							f"decoding charset tags, b_text={b_text!r}"
							"\nunbalanced </charset> tag\n",
						)
					continue

				# <charset c="?">
				b_type = b_parts[i + 1].lower()
				# b_type is a bytes instance, with length 1
				if b_type == b"t":
					encodings.append("babylon-reference")
				elif b_type == b"u":
					encodings.append("utf-8")
				elif b_type == b"k":  # noqa: SIM114
					encodings.append(self.sourceEncoding)
				elif b_type == b"e":
					encodings.append(self.sourceEncoding)
				elif b_type == b"g":
					# gbk or gb18030 encoding
					# (not enough data to make distinction)
					encodings.append("gbk")
				else:
					log.debug(
						f"decoding charset tags, text = {b_text!r}"
						f"\nunknown charset code = {ord(b_type):#02x}\n",
					)
					# add any encoding to prevent
					# "unbalanced </charset> tag" error
					encodings.append(defaultEncoding)
				continue

			# c attribute of charset tag if the previous tag was charset

		if encodings:
			log.debug(
				f"decoding charset tags, text={b_text}\nunclosed <charset...> tag\n",
			)
		return u_text, defaultEncodingOnly

	def processKey(self, b_word: bytes) -> tuple[str, str]:
		"""
		b_word is a bytes instance
		returns (u_word: str, u_word_html: str)
		u_word_html is empty unless it's different from u_word.
		"""
		b_word, strip_count = stripDollarIndexes(b_word)
		if strip_count > 1:
			log.debug(
				f"processKey({b_word}):\nnumber of dollar indexes = {strip_count}",
			)
		# convert to unicode
		if self._strict_string_conversion:
			try:
				u_word = b_word.decode(self.sourceEncoding)
			except UnicodeError:
				log.debug(
					f"processKey({b_word}):\nconversion error:\n" + excMessage(),
				)
				u_word = b_word.decode(
					self.sourceEncoding,
					"ignore",
				)
		else:
			u_word = b_word.decode(self.sourceEncoding, "ignore")

		u_word_html = ""
		if self._process_html_in_key:
			u_word = replaceHtmlEntriesInKeys(u_word)
			# u_word = u_word.replace("<BR>", "").replace("<BR/>", "")\
			# 	.replace("<br>", "").replace("<br/>", "")
			u_word_copy = u_word
			u_word = stripHtmlTags(u_word)
			if u_word != u_word_copy:
				u_word_html = u_word_copy
			# if(re.match(".*[&<>].*", _u_word_copy)):
			# 	log.debug("original text: " + _u_word_copy + "\n" \
			# 			  + "new      text: " + u_word + "\n")
		u_word = removeControlChars(u_word)
		u_word = removeNewlines(u_word)
		u_word = u_word.lstrip()
		if self._key_rstrip_chars:
			u_word = u_word.rstrip(self._key_rstrip_chars)
		return u_word, u_word_html

	def processAlternativeKey(self, b_word: bytes, b_key: bytes) -> str:
		"""
		b_word is a bytes instance
		returns u_word_main, as str instance (utf-8 encoding).
		"""
		b_word_main, _strip_count = stripDollarIndexes(b_word)
		# convert to unicode
		if self._strict_string_conversion:
			try:
				u_word_main = b_word_main.decode(self.sourceEncoding)
			except UnicodeError:
				log.debug(
					f"processAlternativeKey({b_word})\nkey = {b_key}"
					":\nconversion error:\n" + excMessage(),
				)
				u_word_main = b_word_main.decode(self.sourceEncoding, "ignore")
		else:
			u_word_main = b_word_main.decode(self.sourceEncoding, "ignore")

		# strip "/" before words
		u_word_main = self.stripSlashAltKeyPattern.sub(
			r"\1\2",
			u_word_main,
		)

		if self._process_html_in_key:
			# u_word_main_orig = u_word_main
			u_word_main = stripHtmlTags(u_word_main)
			u_word_main = replaceHtmlEntriesInKeys(u_word_main)
			# if(re.match(".*[&<>].*", u_word_main_orig)):
			# 	log.debug("original text: " + u_word_main_orig + "\n" \
			# 			+ "new      text: " + u_word_main + "\n")
		u_word_main = removeControlChars(u_word_main)
		u_word_main = removeNewlines(u_word_main)
		u_word_main = u_word_main.lstrip()
		return u_word_main.rstrip(self._key_rstrip_chars)
