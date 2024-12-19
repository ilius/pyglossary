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
import os
import re
from typing import TYPE_CHECKING, NamedTuple

from pyglossary.core import log
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	HtmlColorOption,
	Option,
	StrOption,
)
from pyglossary.text_utils import (
	excMessage,
	uintFromBytes,
)
from pyglossary.xml_utils import xml_escape

from .bgl_gzip import GzipFile
from .bgl_info import (
	charsetInfoDecode,
	infoType3ByCode,
)
from .bgl_pos import partOfSpeechByCode
from .bgl_text import (
	fixImgLinks,
	normalizeNewlines,
	removeControlChars,
	removeNewlines,
	replaceAsciiCharRefs,
	replaceHtmlEntries,
	replaceHtmlEntriesInKeys,
	stripDollarIndexes,
	stripHtmlTags,
	unknownHtmlEntries,
)

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = ["BGLGzipFile", "BglReader", "Block", "FileOffS", "optionsProp", "tmpDir"]


file = io.BufferedReader

debugReadOptions = {
	"search_char_samples",  # bool
	"collect_metadata2",  # bool
	"write_gz",  # bool
	"char_samples_path",  # str, file path
	"msg_log_path",  # str, file path
	"raw_dump_path",  # str, file path
	"unpacked_gzip_path",  # str, file path
}

optionsProp: dict[str, Option] = {
	"default_encoding_overwrite": EncodingOption(
		comment="Default encoding (overwrite)",
	),
	"source_encoding_overwrite": EncodingOption(
		comment="Source encoding (overwrite)",
	),
	"target_encoding_overwrite": EncodingOption(
		comment="Target encoding (overwrite)",
	),
	"part_of_speech_color": HtmlColorOption(
		comment="Color for Part of Speech",
	),
	"no_control_sequence_in_defi": BoolOption(
		comment="No control sequence in definitions",
	),
	"strict_string_conversion": BoolOption(
		comment="Strict string conversion",
	),
	"process_html_in_key": BoolOption(
		comment="Process HTML in (entry or info) key",
	),
	"key_rstrip_chars": StrOption(
		multiline=True,
		comment="Characters to strip from right-side of keys",
	),
	# debug read options:
	"search_char_samples": BoolOption(
		comment="(debug) Search character samples",
	),
	"collect_metadata2": BoolOption(
		comment="(debug) Collect second pass metadata from definitions",
	),
	"write_gz": BoolOption(
		comment="(debug) Create a file named *-data.gz",
	),
	"char_samples_path": StrOption(
		# file path
		comment="(debug) File path for character samples",
	),
	"msg_log_path": StrOption(
		# file path
		comment="(debug) File path for message log",
	),
	"raw_dump_path": StrOption(
		# file path
		comment="(debug) File path for writing raw blocks",
	),
	"unpacked_gzip_path": StrOption(
		# file path
		comment="(debug) Path to create unzipped file",
	),
}


if os.sep == "/":  # Operating system is Unix-like
	tmpDir = "/tmp"  # noqa: S108
elif os.sep == "\\":  # Operating system is ms-windows
	tmpDir = os.getenv("TEMP")
else:
	raise RuntimeError(
		f"Unknown path separator(os.sep=={os.sep!r}). What is your operating system?",
	)

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
		**kwargs,  # noqa: ANN003
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
		return (
			f"Block type={self.type}, length={self.length}, "
			f"len(data)={len(self.data)}"
		)


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


class BglReader:
	_default_encoding_overwrite: str = ""
	_source_encoding_overwrite: str = ""
	_target_encoding_overwrite: str = ""
	_part_of_speech_color: str = "007000"
	_no_control_sequence_in_defi: bool = False
	_strict_string_conversion: bool = False
	# process keys and alternates as HTML
	# Babylon does not interpret keys and alternates as HTML text,
	# however you may encounter many keys containing character references
	# and html tags. That is clearly a bug of the dictionary.
	# We must be very careful processing HTML tags in keys, not damage
	# normal keys. This option should be disabled by default, enabled
	# explicitly by user. Namely this option does the following:
	# - resolve character references
	# - strip HTML tags
	_process_html_in_key: bool = True
	# a string of characters that will be stripped from the end of the
	# key (and alternate), see str.rstrip function
	_key_rstrip_chars: str = ""

	##########################################################################
	"""
	Dictionary properties
	---------------------

	Dictionary (or glossary) properties are textual data like glossary name,
	glossary author name, glossary author e-mail, copyright message and
	glossary description. Most of the dictionaries have these properties set.
	Since they contain textual data we need to know the encoding.
	There may be other properties not listed here. I've enumerated only those
	that are available in Babylon Glossary builder.

	Playing with Babylon builder allows us detect how encoding is selected.
	If global utf-8 flag is set, utf-8 encoding is used for all properties.
	Otherwise the target encoding is used, that is the encoding corresponding
	to the target language. The chars that cannot be represented in the target
	encoding are replaced with question marks.

	Using this algorithm to decode dictionary properties you may encounter that
	some of them are decoded incorrectly. For example, it is clear that the
	property is in cp1251 encoding while the algorithm says we must use cp1252,
	and we get garbage after decoding. That is OK, the algorithm is correct.
	You may install that dictionary in Babylon and check dictionary properties.
	It shows the same garbage. Unfortunately, we cannot detect correct encoding
	in this case automatically. We may add a parameter the will overwrite the
	selected encoding, so the user may fix the encoding if needed.
	"""

	def __init__(self, glos: GlossaryType) -> None:  # no more arguments
		self._glos = glos
		self._filename = ""
		self.info = {}
		self.numEntries = None
		####
		self.sourceLang = ""
		self.targetLang = ""
		##
		self.defaultCharset = ""
		self.sourceCharset = ""
		self.targetCharset = ""
		##
		self.sourceEncoding = None
		self.targetEncoding = None
		####
		self.bgl_numEntries = None
		self.wordLenMax = 0
		self.defiMaxBytes = 0
		##
		self.metadata2 = None
		self.rawDumpFile = None
		self.msgLogFile = None
		self.samplesDumpFile = None
		##
		self.stripSlashAltKeyPattern = re.compile(r"(^|\s)/(\w)", re.UNICODE)
		self.specialCharPattern = re.compile(r"[^\s\w.]", re.UNICODE)
		###
		self.file = None
		# offset of gzip header, set in self.open()
		self.gzipOffset = None
		# must be a in RRGGBB format
		self.iconDataList = []
		self.aboutBytes: bytes | None = None
		self.aboutExt = ""

	def __len__(self) -> int:
		if self.numEntries is None:
			log.warning("len(reader) called while numEntries=None")
			return 0
		return self.numEntries + self.numResources

	# open .bgl file, read signature, find and open gzipped content
	# self.file - ungzipped content
	def open(
		self,
		filename: str,
	) -> None:
		self._filename = filename

		if not self.openGzip():
			raise OSError("BGL: failed to read gzip header")

		self.readInfo()
		self.setGlossaryInfo()

	def openGzip(self) -> None:
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
				f"bgl_numEntries={self.bgl_numEntries}"
				f", numEntries={self.numEntries}",
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
		for attr in (
			"defaultCharset",
			"sourceCharset",
			"targetCharset",
			"defaultEncoding",
			"sourceEncoding",
			"targetEncoding",
		):
			value = getattr(self, attr, None)
			if value:
				glos.setInfo("bgl_" + attr, value)
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

	def close(self) -> None:
		if self.file:
			self.file.close()
			self.file = None

	def __del__(self) -> None:
		self.close()
		while unknownHtmlEntries:
			entity = unknownHtmlEntries.pop()
			log.debug(f"BGL: unknown html entity: {entity}")

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
				f"readBytes: expected to read {num} bytes"
				f", but found {len(buf)} bytes",
			)
			return -1
		return uintFromBytes(buf)

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
		"""
		Entry keys may contain html text, for example:
		ante<font face'Lucida Sans Unicode'>&lt; meridiem
		arm und reich c=t&gt;2003;</charset>
		</font>und<font face='Lucida Sans Unicode'>
		etc.

		Babylon does not process keys as html, it display them as is.
		Html in keys is the problem of that particular dictionary.
		We should not process keys as html, since Babylon do not process
		them as such.
		"""
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

	# TODO: break it down
	# PLR0912 Too many branches (20 > 12)
	def processDefi(self, b_defi: bytes, b_key: bytes) -> str:  # noqa: PLR0912
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
	def collectDefiFields(  # noqa: PLR0912
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
