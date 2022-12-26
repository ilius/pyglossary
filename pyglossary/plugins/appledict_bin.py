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
from typing import Tuple, Match

from pyglossary.plugins.formats_common import *

from struct import unpack
from zlib import decompress
from datetime import datetime

enable = True
lname = "appledict_bin"
format = "AppleDictBin"
description = "AppleDict Binary"
extensions = (".dictionary", ".data",)
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
	}

	_html: bool = True
	_html_full: bool = False

	def __init__(self, glos):
		self._glos = glos
		self._filename = ""
		self._file = None
		self._encoding = "utf-8"
		self._buf = ""
		self._defiFormat = "m"
		self._re_link = re.compile(f'<a [^<>]*>')
		self._titleById = {}
		self._wordCount = 0

		try:
			from lxml import etree
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e

	def sub_link(self, m: "Match"):
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
		elif href.startswith("http://") or href.startswith("https://"):
			pass
		else:
			a.attrib["href"] = href = f"bword://{href}"

		a_new = tostring(a).decode("utf-8")
		a_new = a_new[:-4]  # remove '</a>'

		return a_new

	def fixLinksInDefi(self, defi: str) -> str:
		defi = self._re_link.sub(self.sub_link, defi)
		return defi

	def open(self, filename):
		self._defiFormat = "h" if self._html else "m"
		parts = split(filename)
		dbname = parts[-1]
		if isdir(filename):
			if parts[-1] == "Contents":
				filename = join(filename, "Body.data")
				if len(parts) > 2:
					dbname = parts[-2]
			elif isfile(join(filename, "Contents/Body.data")):
				filename = join(filename, "Contents/Body.data")
			elif isfile(join(filename, "Contents/Resources/Body.data")):
				filename = join(filename, "Contents/Resources/Body.data")
			else:
				raise IOError(
					"could not find Body.data file, "
					"please select Body.data file instead of directory"
				)
		elif dbname == "Body.data" and len(parts) > 1:
			dbname = parts[-2]
			if len(parts) > 2:
				if dbname == "Contents":
					dbname = parts[-3]
				elif dbname == "Resources" and len(parts) > 3:
					dbname = parts[-4]

		if not isfile(filename):
			raise IOError(f"no such file: {filename}")

		if dbname.endswith(".dictionary"):
			dbname = dbname[:-len(".dictionary")]
		self._glos.setInfo("name", dbname)

		self._filename = filename
		self._file = open(filename, "rb")

		self._file.seek(0x40)
		self._limit = 0x40 + self.read_int_from_file()
		self._file.seek(0x60)

		t0 = datetime.now()
		self.readEntryIds()
		dt = datetime.now() - t0
		log.info(
			f"Reading entry IDs took {int(dt.total_seconds() * 1000)} ms, "
			f"number of entries: {self._wordCount}"
		)

	def __len__(self):
		return self._wordCount

	def close(self):
		if self._file is not None:
			self._file.close()
			self._file = None

	def getChunkSize(self, pos):
		plus = self._buf[pos:pos + 12].find(b"<d:entry")
		if plus < 1:
			return 0, 0
		bs = self._buf[pos:pos + plus]
		if plus < 4:
			bs = b"\x00" * (4 - plus) + bs
		try:
			chunkSize, = unpack("i", bs)
		except Exception as e:
			log.error(f"{self._buf[pos:pos+100]}")
			raise e
		return chunkSize, plus

	def _getDefi(self, entryElem: "Element") -> str:
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

		defi = etree.tostring(
			entryElem,
			encoding="utf-8",
		).decode("utf-8")
		defi = self.fixLinksInDefi(defi)

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

	def _readEntry(self, pos: int) -> "Tuple[BaseEntry, int]":
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
				f"{pos=}, len(buf)={len(self._buf)}, {entryFull=}"
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

	def readEntryIds(self):
		_file = self._file
		limit = self._limit
		titleById = {}

		while True:
			absPos = _file.tell()
			if absPos >= limit:
				break

			bufSize = self.read_int_from_file()
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
		_file.seek(0x60)
		self._wordCount = len(titleById)

	def read_int_from_file(self) -> int:
		return unpack("i", self._file.read(4))[0]

	def __iter__(self):
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

			bufSize = self.read_int_from_file()
			self._buf = decompress(_file.read(bufSize)[8:])

			pos = 0
			while pos < len(self._buf):
				entry, pos = self._readEntry(pos)
				if entry is not None:
					yield entry
