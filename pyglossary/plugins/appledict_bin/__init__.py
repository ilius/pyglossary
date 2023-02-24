# -*- coding: utf-8 -*-

# Copyright © 2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import re
from datetime import datetime
from io import BytesIO
from os.path import isdir, isfile, join, split
from struct import unpack
from typing import (
	TYPE_CHECKING,
	Any,
	Dict,
	Iterator,
	List,
	Match,
	Optional,
	Tuple,
)

from lxml import etree

from .appledict_file_tools import (
	APPLEDICT_FILE_OFFSET,
	guessFileOffsetLimit,
	read_2_bytes_here,
	read_x_bytes_as_word,
	readInt,
)
from .appledict_properties import from_metadata
from .article_address import ArticleAddress
from .key_data import KeyData, RawKeyData

if TYPE_CHECKING:
	from io import BufferedReader

	import lxml

	from .appledict_properties import AppleDictProperties

from zlib import decompress

from pyglossary.core import log, pip
from pyglossary.glossary_type import EntryType, GlossaryType
from pyglossary.option import BoolOption

enable = True
lname = "appledict_bin"
format = "AppleDictBin"
description = "AppleDict Binary"
extensions = (".dictionary", ".data")
extensionCreate = ""
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://support.apple.com/en-gu/guide/dictionary/welcome/mac",
	"Dictionary User Guide for Mac",
)
optionsProp = {
	"html": BoolOption(comment="Entries are HTML"),
	"html_full": BoolOption(
		comment="Turn every entry's definition into an HTML document",
	),
}


class Reader(object):
	depends = {
		"lxml": "lxml",
		"biplist": "biplist",
		"plistlib": "plistlib",
	}

	_html: bool = True
	_html_full: bool = False

	def __init__(self, glos: GlossaryType) -> None:
		self._glos: GlossaryType = glos
		self._filename = ""
		self._file = None
		self._encoding = "utf-8"
		self._defiFormat = "m"
		self._re_link = re.compile('<a [^<>]*>')
		self._re_xmlns = re.compile(' xmlns:d="[^"<>]+"')
		self._titleById = {}
		self._wordCount = 0
		self._keyTextData: "Dict[ArticleAddress, List[RawKeyData]]"

	def sub_link(self, m: "Match") -> str:
		from lxml.html import fromstring, tostring

		a_raw = m.group(0)
		a = fromstring(a_raw)

		href = a.attrib.get("href", "")

		if href.startswith("x-dictionary:d:"):
			word = href[len("x-dictionary:d:"):]
			a.attrib["href"] = href = f"bword://{word}"

		elif href.startswith("x-dictionary:r:"):
			# https://github.com/ilius/pyglossary/issues/343
			id_i = len("x-dictionary:r:")
			id_j = href.find(":", id_i)
			_id = href[id_i:id_j]
			title = self._titleById.get(_id)
			if title:
				a.attrib["href"] = href = f"bword://{title}"
			else:
				title = a.attrib.get("title")
				if title:
					a.attrib["href"] = href = f"bword://{title}"
		elif href.startswith(("http://", "https://")):
			pass
		else:
			a.attrib["href"] = href = f"bword://{href}"

		a_new = tostring(a).decode("utf-8")
		a_new = a_new[:-4]  # remove '</a>'

		return a_new  # noqa: RET504

	def fixLinksInDefi(self, defi: str) -> str:
		return self._re_link.sub(self.sub_link, defi)

	def open(self, filename: str) -> None:
		from os.path import dirname
		try:
			from lxml import etree  # noqa: F401
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e
		try:
			import biplist  # noqa: F401
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install biplist` to install"
			raise e

		self._defiFormat = "h" if self._html else "m"

		contentsPath: str
		infoPlistPath: str
		bodyDataPath: str
		keyTextDataPath: str

		if isdir(filename):
			if split(filename)[-1] == "Contents":
				contentsPath = filename
			elif isdir(join(filename, "Contents")):
				contentsPath = join(filename, "Contents")
			else:
				raise IOError(f"invalid directory {filename}")
		elif split(filename)[-1] == "Body.data":
			contentsPath = dirname(filename)
		else:
			raise IOError(f"invalid file path {filename}")

		if not isdir(contentsPath):
			raise IOError(
				f"{contentsPath} is not a folder, "
				"Please provide 'Contents/' folder of the dictionary",
			)

		infoPlistPath = join(contentsPath, "Info.plist")
		if isfile(join(contentsPath, "Body.data")):
			bodyDataPath = join(contentsPath, "Body.data")
			keyTextDataPath = join(contentsPath, "KeyText.data")
		elif isfile(join(contentsPath, "Resources/Body.data")):
			bodyDataPath = join(contentsPath, "Resources/Body.data")
			keyTextDataPath = join(contentsPath, "Resources/KeyText.data")
		else:
			raise IOError(
				"could not find Body.data file, "
				"Please provide 'Contents/' folder of the dictionary",
			)

		metadata = self.parseMetadata(infoPlistPath)
		self.setMetadata(metadata)

		# KeyText.data contains:
		# 1. morphological data (opens article "make" when user enters "making")
		# and data that shows
		# 2. data that encodes that searching "2 per cent", "2 percent",
		# or "2%" returns the same article
		# EXAMPLE: <d:index d:value="made" d:title="made (make)"/>
		# If the entry for "make" contains these <d:index> definitions,
		# the entry can be searched not only by "make" but also by "makes" or "made".
		# On the search result list, title value texts like "made" are displayed.
		# EXAMPLE: <d:index d:value="make it" d:title="make it" d:parental-control="1"
		# d:anchor="xpointer(//*[@id='make_it'])"/>
		# EXAMPLE: <d:index d:value="工夫する" d:title="工夫する" 
		# d:yomi="くふうする" d:anchor="xpointer(//*[@id='kufuu-suru'])" />
		# EXAMPLE: <d:index d:value="'s finest" d:title="—'s finest"
		# d:DCSEntryTitle="fine" d:anchor="xpointer(//*[@id='m_en_gbus0362750.070'])"/>
		#     user entered "'s finest", search list we show "—'s finest",
		# show article with title "fine" and point to element id = 'm_en_gbus0362750.070'

		# RawKeyData: tuple(priority, parental_control, key_text_fields)
		self._keyTextData = self.getKeyTextDataFromFile(
			keyTextDataPath,
			self._properties,
		)

		self._filename = bodyDataPath
		self._file = open(bodyDataPath, "rb")

		_, self._limit = guessFileOffsetLimit(self._file)

		t0 = datetime.now()
		self.readEntryIds()
		dt = datetime.now() - t0
		log.info(
			f"Reading entry IDs took {int(dt.total_seconds() * 1000)} ms, "
			f"number of entries: {self._wordCount}",
		)

	def parseMetadata(self, infoPlistPath: str) -> Dict:
		import biplist

		if not isfile(infoPlistPath):
			raise IOError(
				"Could not find 'Info.plist' file, "
				"Please provide 'Contents/' folder of the dictionary",
			)

		metadata: "Dict[str, Any]"
		try:
			metadata = biplist.readPlist(infoPlistPath)
		except (biplist.InvalidPlistException, biplist.NotBinaryPlistException):
			try:
				import plistlib
				with open(infoPlistPath, "rb") as plist_file:
					metadata = plistlib.loads(plist_file.read())
			except Exception as e:
				raise IOError(
					"'Info.plist' file is malformed, "
					f"Please provide 'Contents/' with a correct 'Info.plist'. {e}",
				) from e
		return metadata

	def setMetadata(self, metadata: "Dict[str, Any]"):
		name = metadata.get("CFBundleDisplayName")
		if not name:
			name = metadata.get("CFBundleIdentifier")
		if name:
			self._glos.setInfo("name", name)

		identifier = metadata.get("CFBundleIdentifier")
		if identifier and identifier != name:
			self._glos.setInfo("CFBundleIdentifier", identifier)

		copyright = metadata.get("DCSDictionaryCopyright")
		if copyright:
			self._glos.setInfo("copyright", copyright)

		author = metadata.get("DCSDictionaryManufacturerName")
		if author:
			self._glos.setInfo("author", author)

		edition = metadata.get("CFBundleInfoDictionaryVersion")
		if edition:
			self._glos.setInfo("edition", edition)

		if "DCSDictionaryLanguages" in metadata:
			self.setLangs(metadata)

		self._properties = from_metadata(metadata)

	def setLangs(self, metadata: "Dict[str, Any]") -> None:
		import locale

		langsList = metadata.get("DCSDictionaryLanguages")
		if not langsList:
			return

		langs = langsList[0]

		sourceLocale = langs["DCSDictionaryDescriptionLanguage"]
		self._glos.sourceLangName = locale.normalize(sourceLocale).split("_")[0]

		targetLocale = langs["DCSDictionaryIndexLanguage"]
		self._glos.targetLangName = locale.normalize(targetLocale).split("_")[0]

	def __len__(self) -> int:
		return self._wordCount

	def close(self) -> None:
		if self._file is not None:
			self._file.close()
			self._file = None

	def getChunkSize(self, pos: int) -> "Tuple[int, int]":
		plus = self._buf[pos:pos + 12].find(b"<d:entry")
		if plus < 1:
			return 0, 0
		bs = self._buf[pos:pos + plus]
		if plus < 4:
			bs = b"\x00" * (4 - plus) + bs
		try:
			chunkSize, = unpack("i", bs)
		except Exception as e:
			log.error(f"{self._buf[pos:pos + 100]}")
			raise e
		return chunkSize, plus

	def _getDefi(
		self,
		entryElem: "lxml.etree.Element",
	) -> str:
		from lxml import etree

		if not self._html:
			# FIXME: this produces duplicate text for Idioms.dictionary, see #301
			return "".join([
				etree.tostring(
					child,
					encoding="utf-8",
				).decode("utf-8")
				for child in entryElem.iterdescendants()
			])

		entryElem.tag = "div"
		for attr in entryElem.attrib.keys():
			# if attr == "id" or attr.endswith("title"):
			del entryElem.attrib[attr]

		defi = etree.tostring(
			entryElem,
			encoding="utf-8",
			method="html",
		).decode("utf-8")
		defi = self.fixLinksInDefi(defi)
		defi = self._re_xmlns.sub("", defi)

		if self._html_full:
			defi = (
				f'<!DOCTYPE html><html><head>'
				f'<link rel="stylesheet" href="style.css">'
				f'</head><body>{defi}</body></html>'
			)

		return defi

	def getChunkLenOffset(self, pos, buffer: bytes):
		"""
		@return chunk byte length and offset

		offset is usually 4 bytes integer, that contains chunk/entry byte length
		"""
		offset = buffer[pos:pos + 12].find(b"<d:entry")
		if offset == -1:
			print(buffer[pos:])
			raise IOError('Could not find entry tag <d:entry>')
		if offset == 0:
			# when no such info (offset equals 0) provided,
			# we take all bytes till the closing tag or till section end
			endI = buffer[pos:].find(b"</d:entry>\n")
			if endI == -1:
				chunkLen = len(buffer) - pos
			else:
				chunkLen = endI + 11
		else:
			bs = buffer[pos:pos + offset]
			if offset < 4:
				bs = b"\x00" * (4 - offset) + bs
			try:
				chunkLen, = unpack("i", bs)
			except Exception as e:
				log.error(f"{buffer[pos:pos + 100]}")
				raise e
		return chunkLen, offset

	def createEntry(
		self,
		entryBytes: bytes,
		articleAddress: "ArticleAddress",
	) -> Optional[EntryType]:
		# 1. create and validate XML of the entry's body
		entryRoot = self.convertEntryBytesToXml(entryBytes)
		if entryRoot is None:
			return None
		entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
		if not entryElems:
			return None
		word = entryElems[0].xpath("./@d:title", namespaces=entryRoot.nsmap)[0]
		defi = self._getDefi(entryElems[0])

		# 2. add alts
		keyTextFieldOrder = self._properties.key_text_field_order
		keyDataList: List[KeyData] = []
		if articleAddress in self._keyTextData:
			raw_keyDataList = self._keyTextData[articleAddress]
			for raw_key_data in raw_keyDataList:
				keyDataList.append(KeyData.from_raw_key_data(raw_key_data, keyTextFieldOrder))

		if keyDataList:
			word = [word] + [keyData.keyword for keyData in keyDataList]

		return self._glos.newEntry(
			word=word,
			defi=defi,
			defiFormat=self._defiFormat,
			byteProgress=(self._absPos, self._limit),
		)

	def convertEntryBytesToXml(self, entryBytes: bytes) -> Optional[etree.Element]:
		# etree.register_namespace("d", "http://www.apple.com/DTDs/DictionaryService-1.0.rng")
		entryFull = entryBytes.decode(self._encoding, errors="replace")
		entryFull = entryFull.strip()
		if not entryFull:
			return None
		try:
			entryRoot = etree.fromstring(entryFull)
		except etree.XMLSyntaxError as e:
			log.error(
				f"len(buf)={len(self._buf)}, {entryFull=}",
			)
			raise e
		if self._limit <= 0:
			raise ValueError(f"self._limit = {self._limit}")
		return entryRoot

	def readEntryIds(self) -> None:
		titleById = {}
		for entryBytes, _ in self.yieldEntryBytes(
			self._file,
			self._properties,
		):
			entryBytes = entryBytes.strip()
			if not entryBytes:
				continue
			id_i = entryBytes.find(b'id="')
			if id_i < 0:
				log.error(f"id not found: {entryBytes}")
				continue
			id_j = entryBytes.find(b'"', id_i + 4)
			if id_j < 0:
				log.error(f"id closing not found: {entryBytes.decode(self._encoding)}")
				continue
			_id = entryBytes[id_i + 4: id_j].decode(self._encoding)
			title_i = entryBytes.find(b'd:title="')
			if title_i < 0:
				log.error(f"title not found: {entryBytes.decode(self._encoding)}")
				continue
			title_j = entryBytes.find(b'"', title_i + 9)
			if title_j < 0:
				log.error(f"title closing not found: {entryBytes.decode(self._encoding)}")
				continue
			titleById[_id] = entryBytes[title_i + 9: title_j].decode(self._encoding)

		self._titleById = titleById
		self._wordCount = len(titleById)

	def getKeyTextDataFromFile(
		self,
		morphoFilePath: str,
		properties: "AppleDictProperties",
	) -> "Dict[ArticleAddress, List[RawKeyData]]" :
		"""
			Prepare `KeyText.data` file for extracting morphological data
		"""
		with open(morphoFilePath, 'rb') as keyTextFile:
			fileDataOffset, fileLimit = guessFileOffsetLimit(keyTextFile)

			buff = BytesIO()
			if properties.key_text_compression_type > 0:
				keyTextFile.seek(fileDataOffset + APPLEDICT_FILE_OFFSET)
				sectionLength = readInt(keyTextFile)
				sectionOffset = keyTextFile.tell()
				fileLimitDecompressed = 0
				while keyTextFile.tell() < fileLimit + APPLEDICT_FILE_OFFSET:
					compressedSectionByteLen = readInt(keyTextFile)
					decompressedSectionByteLen = readInt(keyTextFile)
					chunksection_bytes = decompress(
						keyTextFile.read(compressedSectionByteLen - 4),
					)
					buff.write(chunksection_bytes)
					fileLimitDecompressed += decompressedSectionByteLen
					sectionOffset += sectionLength
					keyTextFile.seek(sectionOffset)
				bufferOffset = 0
				bufferLimit = fileLimitDecompressed
			else:
				keyTextFile.seek(APPLEDICT_FILE_OFFSET)
				buff.write(keyTextFile.read())
				bufferOffset = fileDataOffset
				bufferLimit = fileLimit

		return self.readKeyTextData(
			buff=buff,
			bufferOffset=bufferOffset,
			bufferLimit=bufferLimit,
			properties=properties,
		)

	def readKeyTextData(
		self,
		buff: "BufferedReader",
		bufferOffset: int,
		bufferLimit: int,
		properties: "AppleDictProperties",
	) -> "Dict[ArticleAddress, List[RawKeyData]]":
		buff.seek(bufferOffset)
		keyTextData: "Dict[ArticleAddress, List[RawKeyData]]" = {}
		while bufferOffset < bufferLimit:
			buff.seek(bufferOffset)
			next_section_jump = readInt(buff)
			if properties.key_text_compression_type == 0:
				big_len = readInt(buff)  # noqa: F841
			# number of lexemes
			wordFormCount = read_2_bytes_here(buff)  # 0x01
			next_lexeme_offset: int = 0
			for _ in range(wordFormCount):
				_ = read_2_bytes_here(buff)  # 0x00
				# TODO might be 1 or 2 or more zeros
				if next_lexeme_offset != 0:
					buff.seek(next_lexeme_offset)
				small_len = 0
				while small_len == 0:
					curr_offset = buff.tell()
					small_len = read_2_bytes_here(buff)  # 0x2c
				next_lexeme_offset = curr_offset + small_len
				# the resulting number must match with Contents/Body.data address of the entry
				articleAddress: ArticleAddress
				if properties.body_has_sections:
					chunkOffset = readInt(buff)
					sectionOffset = readInt(buff)
					articleAddress = ArticleAddress(
						sectionOffset=sectionOffset,
						chunkOffset=chunkOffset,
					)
				else:
					chunkOffset = 0x0
					sectionOffset = readInt(buff)
					articleAddress = ArticleAddress(
						sectionOffset=sectionOffset,
						chunkOffset=chunkOffset,
					)

				priorityAndParentalControl = read_2_bytes_here(buff)  # 0x13
				if priorityAndParentalControl > 0x20:
					raise RuntimeError(
						"WRONG priority or parental control:"
						f"{priorityAndParentalControl} (section: {hex(bufferOffset)})"
					)
				# d:parental-control="1"
				parental_control = priorityAndParentalControl % 2
				# d:priority=".." between 0x00..0x12, priority = [0..9]
				priority = int((priorityAndParentalControl - parental_control) / 2)

				key_text_fields = []
				while True:
					word_form_len = read_2_bytes_here(buff)
					if word_form_len == 0:
						break
					word_form = read_x_bytes_as_word(buff, word_form_len)
					key_text_fields.append(word_form)
				entryKeyTextData: RawKeyData = (
					priority,
					parental_control,
					key_text_fields,
				)
				if articleAddress in keyTextData:
					keyTextData[articleAddress].append(entryKeyTextData)
				else:
					keyTextData[articleAddress] = [entryKeyTextData]
			bufferOffset += next_section_jump + 4

		return keyTextData

	def __iter__(self) -> Iterator[EntryType]:
		from os.path import dirname

		if self._file is None:
			raise RuntimeError("iterating over a reader while it's not open")
		glos = self._glos

		cssFilename = join(dirname(self._filename), "DefaultStyle.css")
		if isfile(cssFilename):
			with open(cssFilename, mode="rb") as cssFile:
				cssBytes = cssFile.read()
			yield glos.newDataEntry("style.css", cssBytes)

		for entryBytes, articleAddress in self.yieldEntryBytes(
			self._file,
			self._properties,
		):
			entry = self.createEntry(entryBytes, articleAddress)
			if entry is not None:
				yield entry

	def yieldEntryBytes(
		self,
		body_file,
		properties: "AppleDictProperties",
	) -> "Iterator[Tuple[bytes, ArticleAddress]]":
		fileDataOffset, fileLimit = guessFileOffsetLimit(body_file)
		sectionOffset = fileDataOffset
		while sectionOffset < fileLimit:
			body_file.seek(sectionOffset + APPLEDICT_FILE_OFFSET)
			self._absPos = body_file.tell()

			# at the start of each section byte lengths of the section are encoded
			next_section_jump = readInt(body_file)
			data_byte_len = readInt(body_file)
			if properties.body_compression_type > 0:
				decompressed_byte_len = readInt(body_file)  # noqa: F841
				decompressed_bytes = body_file.read(data_byte_len - 4)
				buffer = decompress(decompressed_bytes)
			else:
				buffer = body_file.read(data_byte_len)

			pos = 0
			while pos < len(buffer):
				chunkLen, offset = self.getChunkLenOffset(pos, buffer)
				articleAddress = ArticleAddress(sectionOffset, pos)
				pos += offset
				entryBytes = buffer[pos:pos + chunkLen]

				pos += chunkLen
				yield entryBytes, articleAddress

			sectionOffset += next_section_jump + 4
