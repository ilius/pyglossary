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
from pyglossary.text_utils import uintFromBytes
from pyglossary.xml_utils import xml_escape

from .bgl_pos import partOfSpeechByCode
from .bgl_text import (
	fixImgLinks,
	normalizeNewlines,
	removeControlChars,
	replaceHtmlEntries,
)
from .reader_data import DefinitionFields


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

	# TODO: break it down
	# PLR0912 Too many branches (41 > 12)
	# PLR0915 Too many statements (121 > 50)
	def collectDefiFields(  # noqa: PLR0912, PLR0915
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

			if b_defi[i] == 0x02:
				# part of speech # "\x02" <one char - part of speech>
				if fields.partOfSpeech:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}"
						":\nduplicate part of speech item",
					)
				if i + 1 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nb_defi ends after \\x02",
					)
					return

				posCode = b_defi[i + 1]

				try:
					fields.partOfSpeech = partOfSpeechByCode[posCode]
				except KeyError:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}"
						f":\nunknown part of speech code = {posCode:#02x}",
					)
					return
				i += 2
			elif b_defi[i] == 0x06:  # \x06<one byte>
				if fields.b_field_06:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nduplicate type 6",
					)
				if i + 1 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nb_defi ends after \\x06",
					)
					return
				fields.b_field_06 = b_defi[i + 1]
				i += 2
			elif b_defi[i] == 0x07:  # \x07<two bytes>
				# Found in 4 Hebrew dictionaries. I do not understand.
				if i + 3 > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x07",
					)
					return
				fields.b_field_07 = b_defi[i + 1 : i + 3]
				i += 3
			elif b_defi[i] == 0x13:  # "\x13"<one byte - length><data>
				# known values:
				# 03 06 0D C7
				# 04 00 00 00 44
				# ...
				# 04 00 00 00 5F
				if i + 1 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x13",
					)
					return
				Len = b_defi[i + 1]
				i += 2
				if Len == 0:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}\n"
						f"b_key = {b_key!r}:\nblank data after \\x13",
					)
					continue
				if i + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}\n"
						f"b_key = {b_key!r}:\ntoo few data after \\x13",
					)
					return
				fields.b_field_13 = b_defi[i : i + Len]
				i += Len
			elif b_defi[i] == 0x18:
				# \x18<one byte - title length><entry title>
				if fields.b_title:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"b_key = {b_key!r}:\nduplicate entry title item",
					)
				if i + 1 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}\n"
						f"b_key = {b_key!r}:\nb_defi ends after \\x18",
					)
					return
				i += 1
				Len = b_defi[i]
				i += 1
				if Len == 0:
					# log.debug(
					# 	f"collecting definition fields, b_defi = {b_defi!r}\n"
					# 	f"b_key = {b_key!r}:\nblank entry title"
					# )
					continue
				if i + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}\n"
						f"b_key = {b_key!r}:\ntitle is too long",
					)
					return
				fields.b_title = b_defi[i : i + Len]
				i += Len
			elif b_defi[i] == 0x1A:  # "\x1a"<one byte - length><text>
				# found only in Hebrew dictionaries, I do not understand.
				if i + 1 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key}:\ntoo few data after \\x1a",
					)
					return
				Len = b_defi[i + 1]
				i += 2
				if Len == 0:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nblank data after \\x1a",
					)
					continue
				if i + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x1a",
					)
					return
				fields.b_field_1a = b_defi[i : i + Len]
				i += Len
			elif b_defi[i] == 0x28:  # "\x28" <two bytes - length><html text>
				# title with transcription?
				if i + 2 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x28",
					)
					return
				i += 1
				Len = uintFromBytes(b_defi[i : i + 2])
				i += 2
				if Len == 0:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nblank data after \\x28",
					)
					continue
				if i + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x28",
					)
					return
				fields.b_title_trans = b_defi[i : i + Len]
				i += Len
			elif 0x40 <= b_defi[i] <= 0x4F:  # [\x41-\x4f] <one byte> <text>
				# often contains digits as text:
				# 56
				# &#0230;lps - key Alps
				# 48@i
				# has no apparent influence on the article
				code = b_defi[i]
				Len = b_defi[i] - 0x3F
				if i + 2 + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x40+",
					)
					return
				i += 2
				b_text = b_defi[i : i + Len]
				i += Len
				log.debug(
					f"unknown definition field {code:#02x}, b_text={b_text!r}",
				)
			elif b_defi[i] == 0x50:
				# \x50 <one byte> <one byte - length><data>
				if i + 2 >= len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x50",
					)
					return
				fields.code_transcription_50 = b_defi[i + 1]
				Len = b_defi[i + 2]
				i += 3
				if Len == 0:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nblank data after \\x50",
					)
					continue
				if i + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x50",
					)
					return
				fields.b_transcription_50 = b_defi[i : i + Len]
				i += Len
			elif b_defi[i] == 0x60:
				# "\x60" <one byte> <two bytes - length> <text>
				if i + 4 > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x60",
					)
					return
				fields.code_transcription_60 = b_defi[i + 1]
				i += 2
				Len = uintFromBytes(b_defi[i : i + 2])
				i += 2
				if Len == 0:
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\nblank data after \\x60",
					)
					continue
				if i + Len > len(b_defi):
					log.debug(
						f"collecting definition fields, b_defi = {b_defi!r}"
						f"\nb_key = {b_key!r}:\ntoo few data after \\x60",
					)
					return
				fields.b_transcription_60 = b_defi[i : i + Len]
				i += Len
			else:
				log.debug(
					f"collecting definition fields, b_defi = {b_defi!r}"
					f"\nb_key = {b_key!r}"
					f":\nunknown control char. Char code = {b_defi[i]:#02x}",
				)
				return
