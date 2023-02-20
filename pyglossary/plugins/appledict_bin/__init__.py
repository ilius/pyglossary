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
from os.path import isdir, isfile, join, split
from struct import unpack
from typing import TYPE_CHECKING, Any, Dict, Iterator, Match, Tuple

from pyglossary.plugins.appledict.appledict_file_tools import readInt, guessFileOffsetLimit

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
		self._buf = ""
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
		elif isfile(join(contentsPath, "Resources/Body.data")):
			bodyDataPath = join(contentsPath, "Resources/Body.data")
		else:
			raise IOError(
				"could not find Body.data file, "
				"Please provide 'Contents/' folder of the dictionary",
			)

		self.setMetadata(infoPlistPath)

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

	def setMetadata(self, infoPlistPath: str) -> None:
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

	def _readEntry(self, pos: int) -> "Tuple[EntryType, int]":
		"""
			returns (entry, pos)
		"""
		from lxml import etree

		entryBytes, pos = self._readEntryData(pos)
		entryFull = entryBytes.decode(self._encoding, errors="replace")
		entryFull = entryFull.strip()
		if not entryFull:
			return None, pos
		try:
			entryRoot = etree.fromstring(entryFull)
		except etree.XMLSyntaxError as e:
			log.error(
				f"{pos=}, len(buf)={len(self._buf)}, {entryFull=}",
			)
			raise e
		entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
		if not entryElems:
			return None, pos
		word = entryElems[0].xpath("./@d:title", namespaces=entryRoot.nsmap)[0]

		defi = self._getDefi(entryElems[0])

		if self._limit <= 0:
			raise ValueError(f"self._limit = {self._limit}")
		return self._glos.newEntry(
			word, defi,
			defiFormat=self._defiFormat,
			byteProgress=(self._absPos, self._limit),
		), pos

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
				entry, pos = self._readEntry(pos)
				if entry is not None:
					yield entry
