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
from io import BytesIO, BufferedReader
from os.path import isdir, isfile, join, split
from struct import unpack
from typing import TYPE_CHECKING, Any, Dict, Iterator, Match, Tuple, List, Optional
from lxml import etree

from pyglossary.plugins.appledict import appledict_file_tools
from pyglossary.plugins.appledict.ArticleAddress import ArticleAddress
from pyglossary.plugins.appledict.appledict_file_tools import readInt, guessFileOffsetLimit, APPLEDICT_FILE_OFFSET, \
	enumerate_reversed
from pyglossary.xml_utils import xml_escape

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
		self._buf: bytes
		self._defiFormat = "m"
		self._entriesOffset: int
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
		# 1. morphological data (opens article "make" when user enters "making") and data that shows
		# 2. data that encodes that searching "2 per cent", "2 percent", or "2%" returns the same article
		# EXAMPLE: <d:index d:value="made" d:title="made (make)"/>
		# If the entry for "make" contains these <d:index> definitions, the entry can be searched not only by "make" but also by "makes" or "made".
		# On the search result list, title value texts like "made" are displayed.
		# EXAMPLE: <d:index d:value="make it" d:title="make it" d:parental-control="1" d:anchor="xpointer(//*[@id='make_it'])"/>
		# EXAMPLE: <d:index d:value="工夫する" d:title="工夫する" d:yomi="くふうする" d:anchor="xpointer(//*[@id='kufuu-suru'])" />
		# EXAMPLE: <d:index d:value="'s finest" d:title="—'s finest" d:DCSEntryTitle="fine" d:anchor="xpointer(//*[@id='m_en_gbus0362750.070'])"/>
		#     user entered "'s finest", search list we show "—'s finest", show article with title "fine" and point to element id = 'm_en_gbus0362750.070'
		self.keytext_data_xml: Dict[ArticleAddress, List[str]] = self.prepareKeyTextFile(keyTextDataPath, metadata)

		self._filename = bodyDataPath
		self._file = open(bodyDataPath, "rb")

		self._entriesOffset, self._limit = guessFileOffsetLimit(self._file)

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

		edition = metadata.get("IDXDictionaryVersion")
		if edition:
			self._glos.setInfo("edition", edition)

		if "DCSDictionaryLanguages" in metadata:
			self.setLangs(metadata)

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
			#if attr == "id" or attr.endswith("title"):
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

	def _readEntryData(self, pos: int) -> "Tuple[bytes, int]":
		chunkSize, plus = self.getChunkSize(pos)
		pos += plus
		if chunkSize == 0:
			endI = self._buf[pos:].find(b"</d:entry>")
			if endI == -1:
				chunkSize = len(self._buf) - pos
			else:
				chunkSize = endI + 10
		entryBytes = self._buf[pos:pos + chunkSize]
		pos += chunkSize
		return entryBytes, pos

	def _readEntry(self, section_offset: int, chunk_offset: int) -> "Tuple[EntryType, int]":
		"""
			returns (entry, pos)
		"""
		entryBytes, pos = self._readEntryData(chunk_offset)
		entryRoot = self.convertEntryBytesToXml(entryBytes)
		if not entryRoot:
			return None, pos

		article_address = ArticleAddress(section_offset, chunk_offset)
		morpho_xmls: List[str]
		if article_address in self.keytext_data_xml:
			morpho_xmls = self.keytext_data_xml[article_address]
		else:
			morpho_xmls = []
		entry = self.createEntry(entryRoot, morpho_xmls)
		return entry, pos

	def createEntry(self, entryRoot, morpho_xmls: List[str]) -> Optional[EntryType]:
		entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
		if not entryElems:
			return None
		word = entryElems[0].xpath("./@d:title", namespaces=entryRoot.nsmap)[0]

		for i, morpho_xml in enumerate_reversed(morpho_xmls):
			entryRoot.insert(0, etree.fromstring(morpho_xml))

		defi = self._getDefi(entryElems[0])

		return self._glos.newEntry(
			word, defi,
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
		_file = self._file
		limit = self._limit
		titleById = {}

		self._file.seek(self._entriesOffset)
		while True:
			absPos = _file.tell()
			if absPos >= limit:
				break

			bufSize = readInt(self._file)
			self._buf = decompress(_file.read(bufSize)[8:])

			pos = 0
			while pos < len(self._buf):
				b_entry, pos = self._readEntryData(pos)
				b_entry = b_entry.strip()
				if not b_entry:
					continue
				id_i = b_entry.find(b'id="')
				if id_i < 0:
					log.error(f"id not found: {b_entry}, {pos=}, buf={self._buf}")
					continue
				id_j = b_entry.find(b'"', id_i + 4)
				if id_j < 0:
					log.error(f"id closing not found: {b_entry.decode(self._encoding)}")
					continue
				_id = b_entry[id_i + 4: id_j].decode(self._encoding)
				title_i = b_entry.find(b'd:title="')
				if title_i < 0:
					log.error(f"title not found: {b_entry.decode(self._encoding)}")
					continue
				title_j = b_entry.find(b'"', title_i + 9)
				if title_j < 0:
					log.error(f"title closing not found: {b_entry.decode(self._encoding)}")
					continue
				titleById[_id] = b_entry[title_i + 9: title_j].decode(self._encoding)

		self._titleById = titleById
		_file.seek(self._entriesOffset)
		self._wordCount = len(titleById)

	def prepareKeyTextFile(self, morphoFilePath, metadata: Dict) -> Dict[ArticleAddress, List[str]]:
		"""Prepare `KeyText.data` file for extracting morphological data"""
		keyText_metadata = metadata.get('IDXDictionaryIndexes')[0]
		metadata_index_fields = keyText_metadata \
			.get('IDXIndexDataFields') \
			.get('IDXVariableDataFields')
		key_data_order = []
		for index_field_info in metadata_index_fields:
			key_data_order.append([index_field_info['IDXDataFieldName'], index_field_info['IDXDataSizeLength']])

		is_compressed = 'TrieAuxiliaryDataOptions' in keyText_metadata and "HeapDataCompressionType" in keyText_metadata['TrieAuxiliaryDataOptions']
		with open(morphoFilePath, 'rb') as keyTextFile:
			(file_data_offset, file_limit) = appledict_file_tools.guessFileOffsetLimit(keyTextFile)

			buffer = BytesIO()
			if is_compressed:
				keyTextFile.seek(file_data_offset)
				section_len = appledict_file_tools.readInt(keyTextFile)
				section_offset = keyTextFile.tell()
				file_limit_decompressed = 0
				while keyTextFile.tell() < file_limit:
					compressedSectionByteLen = appledict_file_tools.readInt(keyTextFile)
					decompressedSectionByteLen = appledict_file_tools.readInt(keyTextFile)
					chunksection_bytes = decompress(keyTextFile.read(compressedSectionByteLen - 4))
					buffer.write(chunksection_bytes)
					file_limit_decompressed += decompressedSectionByteLen
					section_offset += section_len
					keyTextFile.seek(section_offset)
				buffer_offset = 0
				buffer_limit = file_limit_decompressed
				has_sections = True
			else:
				keyTextFile.seek(APPLEDICT_FILE_OFFSET)
				buffer.write(keyTextFile.read())
				buffer_offset = file_data_offset - APPLEDICT_FILE_OFFSET
				buffer_limit = file_limit - APPLEDICT_FILE_OFFSET
				has_sections = False

			morpho_data = self.readMorphology(
				f=buffer,
				buffer_offset=buffer_offset,
				buffer_limit=buffer_limit,
				has_sections=has_sections,
				key_data_order=key_data_order,
			)

			morpho_data_xml: Dict[ArticleAddress, List[str]] = {}
			for article_address in morpho_data:
				morpho_xmls = [self.morpho_data_to_xml(morpho, key_data_order) for morpho in
							   morpho_data[article_address]]
				morpho_data_xml[article_address] = morpho_xmls
			return morpho_data_xml

	def readMorphology(self, f: BufferedReader, buffer_offset: int, buffer_limit: int,
					   has_sections: bool,
					   key_data_order):

		f.seek(buffer_offset)
		morpho_data: Dict[ArticleAddress, List[List[str]]] = {}
		while f.tell() + 2 < buffer_limit:  # TODO check if +2 is a good solution
			f.seek(buffer_offset)
			jump = appledict_file_tools.read_2_bytes_here(f) + 4
			zero1 = appledict_file_tools.read_2_bytes_here(f)  # 0x00
			if not has_sections:
				big_len = appledict_file_tools.read_2_bytes_here(f)  # 0x2c TODO might be here or might be not
				zero2 = appledict_file_tools.read_2_bytes_here(f)  # 0x00 TODO might be here or might be not
			# number of lexemes
			word_forms_number = appledict_file_tools.read_2_bytes_here(f)  # 0x01
			if zero1 != 0:
				print('zero1')
				quit()
			next_lexeme_offset: int = 0
			for word_form_n in range(0, word_forms_number):
				# TODO fix quotes <d:index d:value=""mass produced"" d:title=""mass-produced""/>

				zero3 = appledict_file_tools.read_2_bytes_here(f)  # 0x00 // TODO might be 1 or 2 or more zeros
				if next_lexeme_offset != 0:
					f.seek(next_lexeme_offset)
				small_len = 0
				while small_len == 0:
					curr_offset = f.tell()
					small_len = appledict_file_tools.read_2_bytes_here(f)  # 0x2c
				next_lexeme_offset = curr_offset + small_len
				# the resulting number must match with Contents/Body.data address of the entry
				article_address: ArticleAddress
				if has_sections:
					chunk_offset = appledict_file_tools.readInt(f)
					section_offset = appledict_file_tools.readInt(f)
					article_address = ArticleAddress(section_offset=section_offset, chunk_offset=chunk_offset)
				else:
					chunk_offset = 0x0
					section_offset = appledict_file_tools.readInt(f)
					article_address = ArticleAddress(section_offset=section_offset, chunk_offset=chunk_offset)

				keyword_list = []
				priority_and_parental_control = appledict_file_tools.read_2_bytes_here(f)  # 0x13
				if priority_and_parental_control > 0x20:
					print('WRONG priority or parental control:', priority_and_parental_control, '// section: ',
						  hex(buffer_offset))
					quit()
				# d:parental-control="1"
				parental_control = priority_and_parental_control % 2
				# d:priority=".." between 0x00..0x12, priority = [0..9]
				priority = int((priority_and_parental_control - parental_control) / 2)

				keyword_list.append(priority)
				keyword_list.append(parental_control)

				has_one_zero = False
				for word_form_id, word_form_size_len_bytes in key_data_order:
					# read length, or if value is zero then read again
					word_form_len = appledict_file_tools.read_x_bytes_as_int(f, word_form_size_len_bytes)
					if word_form_len == 0:
						if has_one_zero:
							break
						else:
							has_one_zero = True
							continue
					else:
						has_one_zero = False
					word_form = appledict_file_tools.read_x_bytes_as_word(f, word_form_len)
					keyword_list.append(word_form)

				if article_address in morpho_data:
					morpho_data[article_address].append(keyword_list)
				else:
					morpho_data[article_address] = [keyword_list]
			buffer_offset += jump
		return morpho_data

	keyword_data_id_xml = {
		'DCSKeyword': 'd:value',  # Search key -- if entered in search, this key will provide this definition.
		'DCSHeadword': 'd:title',
		# Headword text that is displayed on the search result list.
		# When the value is the same to the d:index value, it can be omitted.
		# In that case, the value of the d:value is used also for the d:title.
		'DCSAnchor': 'd:anchor',
		# Used to highlight a specific part in an entry.
		# For example, it is used to highlight an idiomatic phrase explanation in an entry for a word.
		'DCSYomiWord': 'd:yomi',  # Used only in making Japanese dictionaries.
		'DCSSortKey': 'd:DCSSortKey',  # This value shows sorting (probably for non-english languages)
		'DCSEntryTitle': 'd:DCSEntryTitle',  # Headword displayed as article title
	}

	def morpho_data_to_xml(self, data: List, keyword_data_order) -> str:
		d_index_xml = '<d:index xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng" '

		for idx, value in enumerate(data):
			if idx == 0:
				priority: int = value
				if priority != 0:
					d_index_xml += f' d:priority="{priority}"'
			elif idx == 1:
				parental_control: int = value
				if parental_control != 0:
					d_index_xml += f' d:parental-control="{parental_control}"'
			else:
				word_form_id = keyword_data_order[idx - 2][0]
				if word_form_id != 'DCSEntryTitle' and word_form_id != 'DCSSortKey':
					d_index_xml += f' {self.keyword_data_id_xml[word_form_id]}="{xml_escape(value)}"'
		d_index_xml += f' />'
		return d_index_xml

	def __iter__(self) -> "Iterator[EntryType]":
		from os.path import dirname

		if self._file is None:
			raise RuntimeError("iterating over a reader while it's not open")
		glos = self._glos

		cssFilename = join(dirname(self._filename), "DefaultStyle.css")
		if isfile(cssFilename):
			with open(cssFilename, mode="rb") as cssFile:
				cssBytes = cssFile.read()
			yield glos.newDataEntry("style.css", cssBytes)

		_file = self._file
		limit = self._limit
		while True:
			self._absPos = _file.tell()
			section_offset = _file.tell() - APPLEDICT_FILE_OFFSET
			if self._absPos >= limit:
				break
			# alternative for buf, bufSize is calculated
			# ~ flag = f.tell()
			# ~ bufSize = 0
			# ~ while True:
			# ~ 	zipp = f.read(bufSize)
			# ~		try:
			# ~			# print(zipp)
			# ~			input(zipp.decode(self._encoding))
			# ~			buf = decompress(zipp[8:])
			# ~			# print(buf)
			# ~			break
			# ~		except:
			# ~			print(bufSize)
			# ~			f.seek(flag)
			# ~			bufSize = bufSize+1

			bufSize = readInt(self._file)
			self._buf = decompress(_file.read(bufSize)[8:])

			pos = 0
			while pos < len(self._buf):
				entry, pos = self._readEntry(section_offset, pos)
				if entry is not None:
					yield entry
