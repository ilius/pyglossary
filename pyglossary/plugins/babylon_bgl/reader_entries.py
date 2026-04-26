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

from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.text_utils import uintFromBytes

from .reader_data import Block, EntryWordData

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType

__all__ = ["_BglReaderEntries"]


class _BglReaderEntries:
	"""Entry iteration and per-block entry parsing."""

	def __iter__(self) -> Iterator[EntryType]:  # noqa: PLR0912
		if not self.file:
			raise RuntimeError("iterating over a reader while it's not open")

		for fname, iconData in self.iconDataList:
			yield self._glos.newDataEntry(fname, iconData)

		if self.aboutBytes:
			yield self._glos.newDataEntry(
				"about" + self.aboutExt,
				self.aboutBytes,
			)

		block = Block()
		while not self.isEndOfDictData():
			if not self.readBlock(block):
				break
			if not block.data:
				continue

			if block.type == 2:
				yield self.readType2(block)

			elif block.type == 11:
				succeed, u_word, u_alts, u_defi = self.readEntry_Type11(block)
				if not succeed:
					continue

				yield self._glos.newEntry(
					[u_word] + u_alts,
					u_defi,
				)

			elif block.type in {1, 7, 10, 11, 13}:
				pos = 0
				# word:
				wordData = self.readEntryWord(block, pos)
				if not wordData:
					continue
				pos = wordData.pos
				# defi:
				succeed, pos, u_defi, _b_defi = self.readEntryDefi(
					block,
					pos,
					wordData,
				)
				if not succeed:
					continue
				# now pos points to the first char after definition
				succeed, pos, u_alts = self.readEntryAlts(
					block,
					pos,
					wordData,
				)
				if not succeed:
					continue
				yield self._glos.newEntry(
					[wordData.u_word] + u_alts,
					u_defi,
				)

	def readType2(self, block: Block) -> EntryType | None:
		"""
		Process type 2 block.

		Type 2 block is an embedded file (mostly Image or HTML).
		pass_num - pass number, may be 1 or 2
		On the first pass self.sourceEncoding is not defined and we cannot
		decode file names.
		That is why the second pass is needed. The second pass is costly, it
		apparently increases total processing time. We should avoid the second
		pass if possible.
		Most of the dictionaries do not have valuable resources, and those
		that do, use file names consisting only of ASCII characters. We may
		process these resources on the second pass. If all files have been
		processed on the first pass, the second pass is not needed.

		All dictionaries I've processed so far use only ASCII chars in
		file names.
		Babylon glossary builder replaces names of files, like links to images,
		with what looks like a hash code of the file name,
		for example "8FFC5C68.png".

		returns: DataEntry instance if the resource was successfully processed
			and None if failed
		"""
		# Embedded File (mostly Image or HTML)
		pos = 0
		# name:
		Len = block.data[pos]
		pos += 1
		if pos + Len > len(block.data):
			log.warning("reading block type 2: name too long")
			return None
		b_name = block.data[pos : pos + Len]
		pos += Len
		b_data = block.data[pos:]
		# if b_name in (b"C2EEF3F6.html", b"8EAF66FD.bmp"):
		# 	log.debug(f"Skipping useless file {b_name!r}")
		# 	return
		u_name = b_name.decode(self.sourceEncoding)
		return self._glos.newDataEntry(
			u_name,
			b_data,
		)

	def readEntryWord(
		self,
		block: Block,
		pos: int,
	) -> EntryWordData | None:
		"""
		Read word part of entry.

		Return None on error
		"""
		if pos + 1 > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				", reading word size: pos + 1 > len(block.data)",
			)
			return None
		Len = block.data[pos]
		pos += 1
		if pos + Len > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				f", block.type={block.type}"
				", reading word: pos + Len > len(block.data)",
			)
			return None
		b_word = block.data[pos : pos + Len]
		u_word, u_word_html = self.processKey(b_word)

		# Entry keys may contain html text, for example:
		# ante<font face'Lucida Sans Unicode'>&lt; meridiem
		# arm und reich c=t&gt;2003;</charset>
		# </font>und<font face='Lucida Sans Unicode'>
		# etc.
		# Babylon does not process keys as html, it display them as is.
		# Html in keys is the problem of that particular dictionary.
		# We should not process keys as html, since Babylon do not process
		# them as such.

		pos += Len
		self.wordLenMax = max(self.wordLenMax, len(u_word))
		return EntryWordData(
			pos=pos,
			u_word=u_word.strip(),
			b_word=b_word.strip(),
			u_word_html=u_word_html,
		)

	def readEntryDefi(
		self,
		block: Block,
		pos: int,
		word: EntryWordData,
	) -> tuple[bool, int | None, bytes | None, bytes | None]:
		"""
		Read defi part of entry.

		Return value is a list.
		(False, None, None, None) if error
		(True, pos, u_defi, b_defi) if OK
			u_defi is a str instance (utf-8)
			b_defi is a bytes instance
		"""
		Err = (False, None, None, None)
		if pos + 2 > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				", reading defi size: pos + 2 > len(block.data)",
			)
			return Err
		Len = uintFromBytes(block.data[pos : pos + 2])
		pos += 2
		if pos + Len > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				f", block.type={block.type}"
				", reading defi: pos + Len > len(block.data)",
			)
			return Err
		b_defi = block.data[pos : pos + Len]
		u_defi = self.processDefi(b_defi, word.b_word)
		# I was going to add this u_word_html or "formatted headword" to defi,
		# so to lose this information, but after looking at the diff
		# for 8 such glossaries, I decided it's not useful enough!
		# if word.u_word_html:
		# 	u_defi = f"<div><b>{word.u_word_html}</b></div>" + u_defi

		self.defiMaxBytes = max(self.defiMaxBytes, len(b_defi))

		pos += Len
		return True, pos, u_defi, b_defi

	def readEntryAlts(
		self,
		block: Block,
		pos: int,
		word: EntryWordData,
	) -> tuple[bool, int | None, list[str] | None]:
		"""
		Returns
		-------
		(False, None, None) if error
		(True, pos, u_alts) if succeed
		u_alts is a sorted list, items are str (utf-8).

		"""
		Err = (False, None, None)
		# use set instead of list to prevent duplicates
		u_alts = set()
		while pos < len(block.data):
			if pos + 1 > len(block.data):
				log.error(
					f"reading block offset={block.offset:#02x}"
					", reading alt size: pos + 1 > len(block.data)",
				)
				return Err
			Len = block.data[pos]
			pos += 1
			if pos + Len > len(block.data):
				log.error(
					f"reading block offset={block.offset:#02x}"
					f", block.type={block.type}"
					", reading alt: pos + Len > len(block.data)",
				)
				return Err
			b_alt = block.data[pos : pos + Len]
			u_alt = self.processAlternativeKey(b_alt, word.b_word)
			# Like entry key, alt is not processed as html by babylon,
			# so do we.
			u_alts.add(u_alt)
			pos += Len
		u_alts.discard(word.u_word)
		return True, pos, sorted(u_alts)

	def readEntry_Type11(
		self,
		block: Block,
	) -> tuple[bool, str | None, list[str] | None, str | None]:
		"""Return (succeed, u_word, u_alts, u_defi)."""
		Err = (False, None, None, None)
		pos = 0

		# reading headword
		if pos + 5 > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				", reading word size: pos + 5 > len(block.data)",
			)
			return Err
		wordLen = uintFromBytes(block.data[pos : pos + 5])
		pos += 5
		if pos + wordLen > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				f", block.type={block.type}"
				", reading word: pos + wordLen > len(block.data)",
			)
			return Err
		b_word = block.data[pos : pos + wordLen]
		u_word, _u_word_html = self.processKey(b_word)
		pos += wordLen
		self.wordLenMax = max(self.wordLenMax, len(u_word))

		# reading alts and defi
		if pos + 4 > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				", reading defi size: pos + 4 > len(block.data)",
			)
			return Err
		altsCount = uintFromBytes(block.data[pos : pos + 4])
		pos += 4

		# reading alts
		# use set instead of list to prevent duplicates
		u_alts = set()
		for _ in range(altsCount):
			if pos + 4 > len(block.data):
				log.error(
					f"reading block offset={block.offset:#02x}"
					", reading alt size: pos + 4 > len(block.data)",
				)
				return Err
			altLen = uintFromBytes(block.data[pos : pos + 4])
			pos += 4
			if altLen == 0:
				if pos + altLen != len(block.data):
					# no evidence
					log.warning(
						f"reading block offset={block.offset:#02x}"
						", reading alt size: pos + altLen != len(block.data)",
					)
				break
			if pos + altLen > len(block.data):
				log.error(
					f"reading block offset={block.offset:#02x}"
					f", block.type={block.type}"
					", reading alt: pos + altLen > len(block.data)",
				)
				return Err
			b_alt = block.data[pos : pos + altLen]
			u_alt = self.processAlternativeKey(b_alt, b_word)
			# Like entry key, alt is not processed as html by babylon,
			# so do we.
			u_alts.add(u_alt)
			pos += altLen

		u_alts.discard(u_word)

		# reading defi
		defiLen = uintFromBytes(block.data[pos : pos + 4])
		pos += 4
		if pos + defiLen > len(block.data):
			log.error(
				f"reading block offset={block.offset:#02x}"
				f", block.type={block.type}"
				", reading defi: pos + defiLen > len(block.data)",
			)
			return Err
		b_defi = block.data[pos : pos + defiLen]
		u_defi = self.processDefi(b_defi, b_word)
		self.defiMaxBytes = max(self.defiMaxBytes, len(b_defi))
		pos += defiLen

		return True, u_word, sorted(u_alts), u_defi
