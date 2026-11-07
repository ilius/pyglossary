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
"""
Babylon BGL definition-body reader mixin.

Parses rich-text and control sequences inside BGL definition records (fonts,
colors, images, links) into HTML.
"""

from __future__ import annotations

from pyglossary.core import log
from pyglossary.utils.text_utils import uintFromBytes
from pyglossary.utils.xml_utils import xml_escape

from .bgl_pos import partOfSpeechByCode
from .bgl_text import (
	fixImgLinks,
	normalizeNewlines,
	removeControlChars,
	replaceHtmlEntries,
)
from .reader_data import DefinitionFields

__all__ = ["_BglReaderDefi"]


class _BglReaderDefi:
	"""Definition body parsing and HTML assembly."""

	# TODO: break it down
	# PLR0912 Too many branches (20 > 12)
	# PLR0915 Too many statements (60 > 50)
	def processDefi(self, b_defi: bytes, b_key: bytes) -> str:  # noqa: PLR0912, PLR0915
		"""
		b_defi: bytes
		b_key: bytes.

		return: u_defi_format
		"""
		fields = DefinitionFields()
		self.collectDefiFields(b_defi, b_key, fields)

		fields.u_defi, fields.singleEncoding = self.decodeCharsetTags(
			fields.b_defi,
			self.targetEncoding,
		)
		if fields.singleEncoding:
			fields.encoding = self.targetEncoding
		fields.u_defi = fixImgLinks(fields.u_defi)
		fields.u_defi = replaceHtmlEntries(fields.u_defi)
		fields.u_defi = removeControlChars(fields.u_defi)
		fields.u_defi = normalizeNewlines(fields.u_defi)
		fields.u_defi = fields.u_defi.strip()

		if fields.b_title:
			fields.u_title, _singleEncoding = self.decodeCharsetTags(
				fields.b_title,
				self.sourceEncoding,
			)
			fields.u_title = replaceHtmlEntries(fields.u_title)
			fields.u_title = removeControlChars(fields.u_title)

		if fields.b_title_trans:
			# sourceEncoding or targetEncoding ?
			fields.u_title_trans, _singleEncoding = self.decodeCharsetTags(
				fields.b_title_trans,
				self.sourceEncoding,
			)
			fields.u_title_trans = replaceHtmlEntries(fields.u_title_trans)
			fields.u_title_trans = removeControlChars(fields.u_title_trans)

		if fields.b_transcription_50:
			if fields.code_transcription_50 == 0x10:
				# contains values like this (char codes):
				# 00 18 00 19 00 1A 00 1B 00 1C 00 1D 00 1E 00 40 00 07
				# this is not utf-16
				# what is this?
				pass
			elif fields.code_transcription_50 == 0x1B:
				fields.u_transcription_50, _singleEncoding = self.decodeCharsetTags(
					fields.b_transcription_50,
					self.sourceEncoding,
				)
				fields.u_transcription_50 = replaceHtmlEntries(
					fields.u_transcription_50,
				)
				fields.u_transcription_50 = removeControlChars(
					fields.u_transcription_50,
				)
			elif fields.code_transcription_50 == 0x18:
				# incomplete text like:
				# t c=T>02D0;</charset>g<charset c=T>0259;</charset>-
				# This defi normally contains fields.b_transcription_60
				# in this case.
				pass
			else:
				log.debug(
					f"processDefi({b_defi})\nb_key = {b_key}"
					":\ndefi field 50"
					f", unknown code: {fields.code_transcription_50:#02x}",
				)

		if fields.b_transcription_60:
			if fields.code_transcription_60 == 0x1B:
				fields.u_transcription_60, _singleEncoding = self.decodeCharsetTags(
					fields.b_transcription_60,
					self.sourceEncoding,
				)
				fields.u_transcription_60 = replaceHtmlEntries(
					fields.u_transcription_60,
				)
				fields.u_transcription_60 = removeControlChars(
					fields.u_transcription_60,
				)
			else:
				log.debug(
					f"processDefi({b_defi})\nb_key = {b_key}"
					":\ndefi field 60"
					f", unknown code: {fields.code_transcription_60:#02x}",
				)

		if fields.b_field_1a:
			fields.u_field_1a, _singleEncoding = self.decodeCharsetTags(
				fields.b_field_1a,
				self.sourceEncoding,
			)
			log.info(f"------- u_field_1a = {fields.u_field_1a}")

		self.processDefiStat(fields, b_defi, b_key)

		u_defi_format = ""
		if fields.partOfSpeech or fields.u_title:
			if fields.partOfSpeech:
				pos = xml_escape(fields.partOfSpeech)
				posColor = self._part_of_speech_color
				u_defi_format += f'<font color="#{posColor}">{pos}</font>'
			if fields.u_title:
				if u_defi_format:
					u_defi_format += " "
				u_defi_format += fields.u_title
			u_defi_format += "<br>\n"
		if fields.u_title_trans:
			u_defi_format += fields.u_title_trans + "<br>\n"
		if fields.u_transcription_50:
			u_defi_format += f"[{fields.u_transcription_50}]<br>\n"
		if fields.u_transcription_60:
			u_defi_format += f"[{fields.u_transcription_60}]<br>\n"
		if fields.u_defi:
			u_defi_format += fields.u_defi

		return u_defi_format.removesuffix("<br>").removesuffix("<BR>")

	def processDefiStat(
		self,
		fields: DefinitionFields,
		b_defi: bytes,
		b_key: bytes,
	) -> None:
		pass

	def findDefiFieldsStart(self, b_defi: bytes) -> int:
		r"""
		Find the beginning of the definition trailing fields.

		Return value is the index of the first chars of the field set,
		or -1 if the field set is not found.

		Normally "\x14" should signal the beginning of the definition fields,
		but some articles may contain this characters inside, so we get false
		match.
		As a workaround we may check the following chars. If "\x14" is followed
		by space, we assume this is part of the article and continue search.
		Unfortunately this does no help in many cases...
		"""
		if self._no_control_sequence_in_defi:
			return -1
		index = -1
		while True:
			index = b_defi.find(
				0x14,
				index + 1,  # starting from next character
				-1,  # not the last character
			)
			if index == -1:
				break
			if b_defi[index + 1] != 0x20:  # b" "[0] == 0x20
				break
		return index

	def _logDefiField(self, b_defi: bytes, b_key: bytes, message: str) -> None:
		log.debug(
			f"collecting definition fields, b_defi = {b_defi!r}\n"
			f"b_key = {b_key!r}:\n{message}",
		)

	def collectDefiFields(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
	) -> None:
		r"""
		Entry definition structure:
		<main definition>['\x14'[{field_code}{field_data}]*]
		{field_code} is one character
		{field_data} has arbitrary length.
		"""
		# d0 is index of the '\x14 char in b_defi
		# d0 may be the last char of the string
		d0 = self.findDefiFieldsStart(b_defi)
		if d0 == -1:
			fields.b_defi = b_defi
			return

		fields.b_defi = b_defi[:d0]

		i = d0 + 1
		while i < len(b_defi):
			if self.metadata2:
				self.metadata2.defiTrailingFields[b_defi[i]] += 1

			code = b_defi[i]
			if 0x40 <= code <= 0x4F:
				next_i = self._collectField40(b_defi, b_key, fields, i)
			else:
				handler = self._defiFieldHandlers.get(code)
				if handler is None:
					self._logDefiField(
						b_defi,
						b_key,
						f"unknown control char. Char code = {code:#02x}",
					)
					return
				next_i = handler(self, b_defi, b_key, fields, i)

			if next_i is None:
				return
			i = next_i

	def _collectPartOfSpeech(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# "\x02" <one char - part of speech>
		if fields.partOfSpeech:
			self._logDefiField(b_defi, b_key, "duplicate part of speech item")
		if i + 1 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "b_defi ends after \\x02")
			return None

		posCode = b_defi[i + 1]

		try:
			fields.partOfSpeech = partOfSpeechByCode[posCode]
		except KeyError:
			self._logDefiField(
				b_defi,
				b_key,
				f"unknown part of speech code = {posCode:#02x}",
			)
			return None
		return i + 2

	def _collectField06(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# \x06<one byte>
		if fields.b_field_06:
			self._logDefiField(b_defi, b_key, "duplicate type 6")
		if i + 1 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "b_defi ends after \\x06")
			return None
		fields.b_field_06 = b_defi[i + 1]
		return i + 2

	def _collectField07(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# \x07<two bytes>
		# Found in 4 Hebrew dictionaries. I do not understand.
		if i + 3 > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x07")
			return None
		fields.b_field_07 = b_defi[i + 1 : i + 3]
		return i + 3

	def _collectField13(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# "\x13"<one byte - length><data>
		# known values:
		# 03 06 0D C7
		# 04 00 00 00 44
		# ...
		# 04 00 00 00 5F
		if i + 1 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x13")
			return None
		length = b_defi[i + 1]
		i += 2
		if length == 0:
			self._logDefiField(b_defi, b_key, "blank data after \\x13")
			return i
		if i + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x13")
			return None
		fields.b_field_13 = b_defi[i : i + length]
		return i + length

	def _collectTitle(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# \x18<one byte - title length><entry title>
		if fields.b_title:
			self._logDefiField(b_defi, b_key, "duplicate entry title item")
		if i + 1 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "b_defi ends after \\x18")
			return None
		i += 1
		length = b_defi[i]
		i += 1
		if length == 0:
			return i
		if i + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "title is too long")
			return None
		fields.b_title = b_defi[i : i + length]
		return i + length

	def _collectField1a(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# "\x1a"<one byte - length><text>
		# found only in Hebrew dictionaries, I do not understand.
		if i + 1 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x1a")
			return None
		length = b_defi[i + 1]
		i += 2
		if length == 0:
			self._logDefiField(b_defi, b_key, "blank data after \\x1a")
			return i
		if i + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x1a")
			return None
		fields.b_field_1a = b_defi[i : i + length]
		return i + length

	def _collectTitleTrans(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# "\x28" <two bytes - length><html text>
		# title with transcription?
		if i + 2 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x28")
			return None
		i += 1
		length = uintFromBytes(b_defi[i : i + 2])
		i += 2
		if length == 0:
			self._logDefiField(b_defi, b_key, "blank data after \\x28")
			return i
		if i + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x28")
			return None
		fields.b_title_trans = b_defi[i : i + length]
		return i + length

	def _collectField40(
		self,
		b_defi: bytes,
		b_key: bytes,
		_fields: DefinitionFields,
		i: int,
	) -> int | None:
		# [\x41-\x4f] <one byte> <text>
		# often contains digits as text:
		# 56
		# &#0230;lps - key Alps
		# 48@i
		# has no apparent influence on the article
		code = b_defi[i]
		length = code - 0x3F
		if i + 2 + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x40+")
			return None
		i += 2
		b_text = b_defi[i : i + length]
		i += length
		log.debug(f"unknown definition field {code:#02x}, b_text={b_text!r}")
		return i

	def _collectTranscription50(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# \x50 <one byte> <one byte - length><data>
		if i + 2 >= len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x50")
			return None
		fields.code_transcription_50 = b_defi[i + 1]
		length = b_defi[i + 2]
		i += 3
		if length == 0:
			self._logDefiField(b_defi, b_key, "blank data after \\x50")
			return i
		if i + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x50")
			return None
		fields.b_transcription_50 = b_defi[i : i + length]
		return i + length

	def _collectTranscription60(
		self,
		b_defi: bytes,
		b_key: bytes,
		fields: DefinitionFields,
		i: int,
	) -> int | None:
		# "\x60" <one byte> <two bytes - length> <text>
		if i + 4 > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x60")
			return None
		fields.code_transcription_60 = b_defi[i + 1]
		i += 2
		length = uintFromBytes(b_defi[i : i + 2])
		i += 2
		if length == 0:
			self._logDefiField(b_defi, b_key, "blank data after \\x60")
			return i
		if i + length > len(b_defi):
			self._logDefiField(b_defi, b_key, "too few data after \\x60")
			return None
		fields.b_transcription_60 = b_defi[i : i + length]
		return i + length

	_defiFieldHandlers = {
		0x02: _collectPartOfSpeech,
		0x06: _collectField06,
		0x07: _collectField07,
		0x13: _collectField13,
		0x18: _collectTitle,
		0x1A: _collectField1a,
		0x28: _collectTitleTrans,
		0x50: _collectTranscription50,
		0x60: _collectTranscription60,
	}
