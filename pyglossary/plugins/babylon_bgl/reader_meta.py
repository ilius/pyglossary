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

from .bgl_info import (
	charsetInfoDecode,
	infoType3ByCode,
)
from .reader_data import Block


class _BglReaderMeta:
	"""Dictionary metadata (first pass) and glossary info."""

	# TODO: PLR0912 Too many branches (14 > 12)
	def readInfo(self) -> None:  # noqa: PLR0912
		"""
		Read meta information about the dictionary: author, description,
		source and target languages, etc (articles are not read).
		"""
		self.numEntries = 0
		self.numBlocks = 0
		self.numResources = 0
		block = Block()
		while not self.isEndOfDictData():
			if not self.readBlock(block):
				break
			self.numBlocks += 1
			if not block.data:
				continue
			if block.type == 0:
				self.readType0(block)
			elif block.type in {1, 7, 10, 11, 13}:
				self.numEntries += 1
			elif block.type == 2:
				self.numResources += 1
			elif block.type == 3:
				self.readType3(block)
			else:  # Unknown block.type
				log.debug(
					f"Unknown Block type {block.type!r}"
					f", data_length = {len(block.data)}"
					f", number = {self.numBlocks}",
				)
		self.file.seek(0)

		self.detectEncoding()

		log.debug(f"numEntries = {self.numEntries}")
		if self.bgl_numEntries and self.bgl_numEntries != self.numEntries:
			# There are a number of cases when these numbers do not match.
			# The dictionary is OK, and these is no doubt that we might missed
			# an entry.
			# self.bgl_numEntries may be less than the number of entries
			# we've read.
			log.warning(
				f"bgl_numEntries={self.bgl_numEntries}, numEntries={self.numEntries}",
			)

		self.numBlocks = 0

		encoding = self.targetEncoding  # FIXME: confirm this is correct
		for key, value in self.info.items():
			if isinstance(value, bytes):
				try:
					value = value.decode(encoding)  # noqa: PLW2901
				except Exception:
					log.warning(f"failed to decode info value: {key} = {value}")
				else:
					self.info[key] = value

	def setGlossaryInfo(self) -> None:
		glos = self._glos
		###
		if self.sourceLang:
			glos.sourceLangName = self.sourceLang.name
			if self.sourceLang.name2:
				glos.setInfo("sourceLang2", self.sourceLang.name2)
		if self.targetLang:
			glos.targetLangName = self.targetLang.name
			if self.targetLang.name2:
				glos.setInfo("targetLang2", self.targetLang.name2)
		###
		glos.setInfo("bgl_defaultCharset", self.defaultCharset)
		glos.setInfo("bgl_sourceCharset", self.sourceCharset)
		glos.setInfo("bgl_targetCharset", self.targetCharset)
		glos.setInfo("bgl_defaultEncoding", self.defaultEncoding)
		glos.setInfo("bgl_sourceEncoding", self.sourceEncoding)
		glos.setInfo("bgl_targetEncoding", self.targetEncoding)
		###
		glos.setInfo("sourceCharset", "UTF-8")
		glos.setInfo("targetCharset", "UTF-8")
		###
		if "lastUpdated" not in self.info and "bgl_firstUpdated" in self.info:
			log.debug("replacing bgl_firstUpdated with lastUpdated")
			self.info["lastUpdated"] = self.info.pop("bgl_firstUpdated")
		###
		for key, value in self.info.items():
			s_value = str(value).strip("\x00")
			if not s_value:
				continue
				# TODO: a bool flag to add empty value infos?
			# leave "creationTime" and "lastUpdated" as is
			if key == "utf8Encoding":
				key = "bgl_" + key  # noqa: PLW2901
			try:
				glos.setInfo(key, s_value)
			except Exception:
				log.exception(f"key = {key}")

	def readType0(self, block: Block) -> bool:
		code = block.data[0]
		if code == 2:
			# this number is vary close to self.bgl_numEntries,
			# but does not always equal to the number of entries
			# see self.readType3, code == 12 as well
			# num = uintFromBytes(block.data[1:])
			pass
		elif code == 8:
			self.defaultCharset = charsetInfoDecode(block.data[1:])
			if not self.defaultCharset:
				log.warning("defaultCharset is not valid")
		else:
			self.logUnknownBlock(block)
			return False
		return True

	def readType3(self, block: Block) -> None:
		"""
		Reads block with type 3, and updates self.info
		returns None.
		"""
		code, b_value = uintFromBytes(block.data[:2]), block.data[2:]
		if not b_value:
			return
		# if not b_value.strip(b"\x00"): return  # FIXME

		try:
			item = infoType3ByCode[code]
		except KeyError:
			if b_value.strip(b"\x00"):
				log.debug(
					f"Unknown info type code={code:#02x}, b_value={b_value!r}",
				)
			return

		key = item.name
		decode = item.decode

		if key.endswith(".ico"):
			self.iconDataList.append((key, b_value))
			return

		value = b_value if decode is None else decode(b_value)

		# `value` can be None, str, bytes or dict

		if not value:
			return

		if key == "bgl_about":
			self.aboutBytes = value["about"]
			self.aboutExt = value["about_extension"]
			return

		if isinstance(value, dict):
			self.info.update(value)
			return

		if item.attr:
			setattr(self, key, value)
			return

		self.info[key] = value

	def detectEncoding(self) -> None:  # noqa: PLR0912
		"""Assign self.sourceEncoding and self.targetEncoding."""
		utf8Encoding = self.info.get("utf8Encoding", False)

		if self._default_encoding_overwrite:
			self.defaultEncoding = self._default_encoding_overwrite
		elif self.defaultCharset:
			self.defaultEncoding = self.defaultCharset
		else:
			self.defaultEncoding = "cp1252"

		if self._source_encoding_overwrite:
			self.sourceEncoding = self._source_encoding_overwrite
		elif utf8Encoding:
			self.sourceEncoding = "utf-8"
		elif self.sourceCharset:
			self.sourceEncoding = self.sourceCharset
		elif self.sourceLang:
			self.sourceEncoding = self.sourceLang.encoding
		else:
			self.sourceEncoding = self.defaultEncoding

		if self._target_encoding_overwrite:
			self.targetEncoding = self._target_encoding_overwrite
		elif utf8Encoding:
			self.targetEncoding = "utf-8"
		elif self.targetCharset:
			self.targetEncoding = self.targetCharset
		elif self.targetLang:
			self.targetEncoding = self.targetLang.encoding
		else:
			self.targetEncoding = self.defaultEncoding

	def logUnknownBlock(self, block: Block) -> None:
		log.debug(
			f"Unknown block: type={block.type}"
			f", number={self.numBlocks}"
			f", data={block.data!r}",
		)
