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
from typing import TYPE_CHECKING, Any

from pyglossary.core import log
from pyglossary.text_utils import uintFromBytes

from .bgl_gzip import GzipFile
from .bgl_text import unknownHtmlEntries

if TYPE_CHECKING:
	from .reader_data import Block

__all__ = ["BGLGzipFile", "FileOffS", "_BglReaderIO"]

file = io.BufferedReader


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


class _BglReaderIO:
	"""Low-level BGL stream I/O."""

	def open(
		self,
		filename: str,
	) -> None:
		self._filename = filename

		if not self.openGzip():
			raise OSError("BGL: failed to read gzip header")

		self.readInfo()
		self.setGlossaryInfo()

	def openGzip(self) -> bool:
		with open(self._filename, "rb") as bglFile:
			if not bglFile:
				log.error(f"file pointer empty: {bglFile}")
				return False
			b_head = bglFile.read(6)

		if len(b_head) < 6 or b_head[:4] not in {
			b"\x12\x34\x00\x01",
			b"\x12\x34\x00\x02",
		}:
			log.error(f"invalid header: {b_head[:6]!r}")
			return False

		self.gzipOffset = gzipOffset = uintFromBytes(b_head[4:6])
		log.debug(f"Position of gz header: {gzipOffset}")

		if gzipOffset < 6:
			log.error(f"invalid gzip header position: {gzipOffset}")
			return False

		self.file = BGLGzipFile(
			fileobj=FileOffS(self._filename, gzipOffset),
			closeFileobj=True,
		)

		return True

	def close(self) -> None:
		if self.file:
			self.file.close()
			self.file = None

	def __del__(self) -> None:
		self.close()
		while unknownHtmlEntries:
			entity = unknownHtmlEntries.pop()
			log.debug(f"BGL: unknown html entity: {entity}")

	def isEndOfDictData(self) -> bool:  # noqa: PLR6301
		"""
		Test for end of dictionary data.

		A bgl file stores dictionary data as a gzip compressed block.
		In other words, a bgl file stores a gzip data file inside.
		A gzip file consists of a series of "members".
		gzip data block in bgl consists of one member (I guess).
		Testing for block type returned by self.readBlock is not a
		reliable way to detect the end of gzip member.
		For example, consider "Airport Code Dictionary.BGL" dictionary.
		To reliably test for end of gzip member block we must use a number
		of undocumented variables of gzip.GzipFile class.
		self.file._new_member - true if the current member has been
		completely read from the input file
		self.file.extrasize - size of buffered data
		self.file.offset - offset in the input file

		after reading one gzip member current position in the input file
		is set to the first byte after gzip data
		We may get this offset: self.file_bgl.tell()
		The last 4 bytes of gzip block contains the size of the original
		(uncompressed) input data modulo 2^32
		"""
		return False

	# returns False if error
	def readBlock(self, block: Block) -> bool:
		block.offset = self.file.tell()
		length = self.readBytes(1)
		if length == -1:
			log.debug("readBlock: length = -1")
			return False
		block.type = length & 0xF
		length >>= 4
		if length < 4:
			length = self.readBytes(length + 1)
			if length == -1:
				log.error("readBlock: length = -1")
				return False
		else:
			length -= 4
		self.file.flush()
		if length > 0:
			try:
				block.data = self.file.read(length)
			except Exception:
				# struct.error: unpack requires a string argument of length 4
				# FIXME
				log.exception(
					"failed to read block data"
					f": numBlocks={self.numBlocks}"
					f", length={length}"
					f", filePos={self.file.tell()}",
				)
				block.data = b""
				return False
		else:
			block.data = b""
		return True

	def readBytes(self, num: int) -> int:
		"""Return -1 if error."""
		if num < 1 or num > 4:
			log.error(f"invalid argument num={num}")
			return -1
		self.file.flush()
		buf = self.file.read(num)
		if len(buf) == 0:
			log.debug("readBytes: end of file: len(buf)==0")
			return -1
		if len(buf) != num:
			log.error(
				f"readBytes: expected to read {num} bytes, but found {len(buf)} bytes",
			)
			return -1
		return uintFromBytes(buf)
