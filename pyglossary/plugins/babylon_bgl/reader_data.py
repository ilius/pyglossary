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

import io
import re
from typing import Any, NamedTuple

from .bgl_gzip import GzipFile

file = io.BufferedReader

re_charset_decode = re.compile(
	b'(<charset\\s+c\\=[\'"]?(\\w)[""]?>|</charset>)',
	re.IGNORECASE,
)
re_b_reference = re.compile(b"^[0-9a-fA-F]{4}$")


class EntryWordData(NamedTuple):
	pos: int
	b_word: bytes
	u_word: str
	u_word_html: str


class BGLGzipFile(GzipFile):
	"""
	gzip_no_crc.py contains GzipFile class without CRC check.

	It prints a warning when CRC code does not match.
	The original method raises an exception in this case.
	Some dictionaries do not use CRC code, it is set to 0.
	"""

	def __init__(
		self,
		fileobj: io.IOBase | None = None,
		closeFileobj: bool = False,
		**kwargs: Any,
	) -> None:
		GzipFile.__init__(self, fileobj=fileobj, **kwargs)
		self.closeFileobj = closeFileobj

	def close(self) -> None:
		if self.closeFileobj:
			self.fileobj.close()


class Block:
	def __init__(self) -> None:
		self.data = b""
		self.type = ""
		# block offset in the gzip stream, for debugging
		self.offset = -1

	def __str__(self) -> str:
		return f"Block type={self.type}, length={self.length}, len(data)={len(self.data)}"


class FileOffS(file):
	"""
	A file class with an offset.

	This class provides an interface to a part of a file starting at specified
	offset and ending at the end of the file, making it appear an independent
	file. offset parameter of the constructor specifies the offset of the first
	byte of the modeled file.
	"""

	def __init__(self, filename: str, offset: int = 0) -> None:
		fileObj = open(filename, "rb")  # noqa: SIM115
		file.__init__(self, fileObj)
		self._fileObj = fileObj
		self.offset = offset
		file.seek(self, offset)  # OR self.seek(0)

	def close(self) -> None:
		self._fileObj.close()

	def seek(self, pos: int, whence: int = 0) -> None:
		if whence == 0:  # relative to start of file
			file.seek(
				self,
				max(0, pos) + self.offset,
				0,
			)
		elif whence == 1:  # relative to current position
			file.seek(
				self,
				max(
					self.offset,
					self.tell() + pos,
				),
				0,
			)
		elif whence == 2:  # relative to end of file
			file.seek(self, pos, 2)
		else:
			raise ValueError(f"FileOffS.seek: bad whence={whence}")

	def tell(self) -> int:
		return file.tell(self) - self.offset


class DefinitionFields:
	"""
	Fields of entry definition.

	Entry definition consists of a number of fields.
	The most important of them are:
	defi - the main definition, mandatory, comes first.
	part of speech
	title
	"""

	# nameByCode = {
	# }
	def __init__(self) -> None:
		# self.bytesByCode = {}
		# self.strByCode = {}

		self.encoding = None  # encoding of the definition
		self.singleEncoding = True
		# singleEncoding=True if the definition was encoded with
		# a single encoding

		self.b_defi = None  # bytes, main definition part of defi
		self.u_defi = None  # str, main part of definition

		self.partOfSpeech = None
		# string representation of the part of speech, utf-8

		self.b_title = None  # bytes
		self.u_title = None  # str

		self.b_title_trans = None  # bytes
		self.u_title_trans = None  # str

		self.b_transcription_50 = None  # bytes
		self.u_transcription_50 = None  # str
		self.code_transcription_50 = None

		self.b_transcription_60 = None  # bytes
		self.u_transcription_60 = None  # str
		self.code_transcription_60 = None

		self.b_field_1a = None  # bytes
		self.u_field_1a = None  # str

		self.b_field_07 = None  # bytes
		self.b_field_06 = None  # bytes
		self.b_field_13 = None  # bytes
