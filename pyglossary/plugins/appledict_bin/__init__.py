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
from io import BufferedReader, BytesIO
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
from .appledict_properties import AppleDictProperties, from_metadata
from .article_address import ArticleAddress
from .key_data import KeyData, RawKeyData

if TYPE_CHECKING:
	import lxml
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
		self.key_text_data: dict[ArticleAddress, List[RawKeyData]] = \
			self.getKeyTextDataFromFile(keyTextDataPath, self.appledict_properties)

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

	def setMetadata(self, metadata: Dict):
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

		self.appledict_properties = from_metadata(metadata)

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
		entry_bytes: bytes,
		article_address: ArticleAddress,
	) -> Optional[EntryType]:
		# 1. create and validate XML of the entry's body
		entryRoot = self.convertEntryBytesToXml(entry_bytes)
		if entryRoot is None:
			return None
		entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
		if not entryElems:
			return None
		word = entryElems[0].xpath("./@d:title", namespaces=entryRoot.nsmap)[0]
		defi = self._getDefi(entryElems[0])

		# 2. add alts
		key_text_field_order = self.appledict_properties.key_text_field_order
		key_data_list: List[KeyData] = []
		if article_address in self.key_text_data:
			raw_key_data_list = self.key_text_data[article_address]
			for raw_key_data in raw_key_data_list:
				key_data_list.append(KeyData.from_raw_key_data(raw_key_data, key_text_field_order))

		if key_data_list:
			word = [word] + [keyData.keyword for keyData in key_data_list]

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
		for entry_bytes, article_address in \
				self.yieldEntryBytes(self._file, self.appledict_properties):
			entry_bytes = entry_bytes.strip()
			if not entry_bytes:
				continue
			id_i = entry_bytes.find(b'id="')
			if id_i < 0:
				log.error(f"id not found: {entry_bytes}")
				continue
			id_j = entry_bytes.find(b'"', id_i + 4)
			if id_j < 0:
				log.error(f"id closing not found: {entry_bytes.decode(self._encoding)}")
				continue
			_id = entry_bytes[id_i + 4: id_j].decode(self._encoding)
			title_i = entry_bytes.find(b'd:title="')
			if title_i < 0:
				log.error(f"title not found: {entry_bytes.decode(self._encoding)}")
				continue
			title_j = entry_bytes.find(b'"', title_i + 9)
			if title_j < 0:
				log.error(f"title closing not found: {entry_bytes.decode(self._encoding)}")
				continue
			titleById[_id] = entry_bytes[title_i + 9: title_j].decode(self._encoding)

		self._titleById = titleById
		self._wordCount = len(titleById)

	def getKeyTextDataFromFile(
		self,
		morphoFilePath: str,
		properties: AppleDictProperties,
	) -> dict[ArticleAddress, List[RawKeyData]] :
		"""Prepare `KeyText.data` file for extracting morphological data"""
		with open(morphoFilePath, 'rb') as keyTextFile:
			file_data_offset, file_limit = guessFileOffsetLimit(keyTextFile)

			buffer = BytesIO()
			if properties.key_text_compression_type > 0:
				keyTextFile.seek(file_data_offset + APPLEDICT_FILE_OFFSET)
				section_len = readInt(keyTextFile)
				section_offset = keyTextFile.tell()
				file_limit_decompressed = 0
				while keyTextFile.tell() < file_limit + APPLEDICT_FILE_OFFSET:
					compressedSectionByteLen = readInt(keyTextFile)
					decompressedSectionByteLen = readInt(keyTextFile)
					chunksection_bytes = decompress(keyTextFile.read(compressedSectionByteLen - 4))
					buffer.write(chunksection_bytes)
					file_limit_decompressed += decompressedSectionByteLen
					section_offset += section_len
					keyTextFile.seek(section_offset)
				buffer_offset = 0
				buffer_limit = file_limit_decompressed
			else:
				keyTextFile.seek(APPLEDICT_FILE_OFFSET)
				buffer.write(keyTextFile.read())
				buffer_offset = file_data_offset
				buffer_limit = file_limit

			return self.readKeyTextData(
				buffer=buffer,
				buffer_offset=buffer_offset,
				buffer_limit=buffer_limit,
				properties=properties,
			)

	def readKeyTextData(
		self,
		buffer: BufferedReader,
		buffer_offset: int,
		buffer_limit: int,
		properties: AppleDictProperties,
	) -> Dict[ArticleAddress, List[RawKeyData]]:
		buffer.seek(buffer_offset)
		key_text_data: Dict[ArticleAddress, List[RawKeyData]] = {}
		while buffer_offset < buffer_limit:
			buffer.seek(buffer_offset)
			next_section_jump = readInt(buffer)
			if properties.key_text_compression_type == 0:
				big_len = readInt(buffer)  # noqa: F841
			# number of lexemes
			word_forms_number = read_2_bytes_here(buffer)  # 0x01
			next_lexeme_offset: int = 0
			for _ in range(word_forms_number):
				_ = read_2_bytes_here(buffer)  # 0x00 // TODO might be 1 or 2 or more zeros
				if next_lexeme_offset != 0:
					buffer.seek(next_lexeme_offset)
				small_len = 0
				while small_len == 0:
					curr_offset = buffer.tell()
					small_len = read_2_bytes_here(buffer)  # 0x2c
				next_lexeme_offset = curr_offset + small_len
				# the resulting number must match with Contents/Body.data address of the entry
				article_address: ArticleAddress
				if properties.body_has_sections:
					chunk_offset = readInt(buffer)
					section_offset = readInt(buffer)
					article_address = ArticleAddress(
						section_offset=section_offset,
						chunk_offset=chunk_offset,
					)
				else:
					chunk_offset = 0x0
					section_offset = readInt(buffer)
					article_address = ArticleAddress(
						section_offset=section_offset,
						chunk_offset=chunk_offset,
					)

				priority_and_parental_control = read_2_bytes_here(buffer)  # 0x13
				if priority_and_parental_control > 0x20:
					raise RuntimeError(
						'WRONG priority or parental control:' +
						priority_and_parental_control +
						'// section: ' +
						hex(buffer_offset),
					)
				# d:parental-control="1"
				parental_control = priority_and_parental_control % 2
				# d:priority=".." between 0x00..0x12, priority = [0..9]
				priority = int((priority_and_parental_control - parental_control) / 2)

				key_text_fields = []
				while True:
					word_form_len = read_2_bytes_here(buffer)
					if word_form_len == 0:
						break
					word_form = read_x_bytes_as_word(buffer, word_form_len)
					key_text_fields.append(word_form)
				entry_key_text_data: RawKeyData = (priority, parental_control, key_text_fields)
				if article_address in key_text_data:
					key_text_data[article_address].append(entry_key_text_data)
				else:
					key_text_data[article_address] = [entry_key_text_data]
			buffer_offset += next_section_jump + 4
		return key_text_data

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

		for entry_bytes, article_address in \
				self.yieldEntryBytes(self._file, self.appledict_properties):
			entry = self.createEntry(entry_bytes, article_address)
			if entry is not None:
				yield entry

	def yieldEntryBytes(self, body_file, properties: AppleDictProperties) -> Iterator[
		tuple[bytes, ArticleAddress]
	]:
		file_data_offset, file_limit = guessFileOffsetLimit(body_file)
		section_offset = file_data_offset
		while section_offset < file_limit:
			body_file.seek(section_offset + APPLEDICT_FILE_OFFSET)
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
				article_address = ArticleAddress(section_offset, pos)
				pos += offset
				entryBytes = buffer[pos:pos + chunkLen]

				pos += chunkLen
				yield entryBytes, article_address

			section_offset += next_section_jump + 4
