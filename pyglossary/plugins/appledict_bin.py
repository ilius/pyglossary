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

from formats_common import *

from struct import unpack
from zlib import decompress

enable = True
format = "AppleDictBin"
description = "AppleDict Binary"
extensions = (".dictionary", ".data",)
singleFile = True
tools = [
	{
		"name": "Apple Dictionary",
		"web": "https://support.apple.com/en-gu/guide/dictionary/welcome/mac",
		"platforms": ["Mac"],
		"license": "Proprietary",
	},
]
optionsProp = {
	"html": BoolOption(),
}


class Reader(object):
	depends = {
		"lxml": "lxml",
	}

	_html: bool = False

	def __init__(self, glos):
		self._glos = glos
		self._filename = ""
		self._file = None
		self._encoding = "utf-8"
		self._buf = ""
		self._defiFormat = "m"

	def open(self, filename):
		self._defiFormat = "h" if self._html else "m"
		parts = filename.split(os.sep)
		dbname = parts[-1]
		if isdir(filename):
			if parts[-1] == "Contents":
				filename = join(filename, "Body.data")
				if len(parts) > 2:
					dbname = parts[-2]
			else:
				filename = join(filename, "Contents/Resources/Body.data")
		elif dbname == "Body.data" and len(parts) > 1:
			dbname = parts[-2]
			if len(parts) > 2:
				if dbname == "Contents":
					dbname = parts[-3]
				elif dbname == "Resources" and len(parts) > 3:
					dbname = parts[-4]

		if dbname.endswith(".dictionary"):
			dbname = dbname[:-len(".dictionary")]
		self._glos.setInfo("name", dbname)

		self._filename = filename
		self._file = open(filename, "rb")

		self._file.seek(0x40)
		self._limit = 0x40 + unpack("i", self._file.read(4))[0]
		self._file.seek(0x60)

	def __len__(self):
		# FIXME: returning zero will disable the progress bar
		return 0

	def close(self):
		if self._file is not None:
			self._file.close()
			self._file = None

	def decode(self, st: bytes) -> str:
		return st.decode(self._encoding, errors="replace")

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

	def _readEntry(self, pos: int) -> "Tuple[BaseEntry, int]":
		"""
			returns (entry, pos)
		"""
		try:
			from lxml import etree
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install lxml` to install"
			raise e
		chunkSize, plus = self.getChunkSize(pos)
		pos += plus
		if chunkSize == 0:
			endI = self._buf[pos:].find(b"</d:entry>")
			if endI == -1:
				chunkSize = len(self._buf) - pos
			else:
				chunkSize = endI + 10
		entryFull = self.decode(self._buf[pos:pos + chunkSize])
		entryFull = entryFull.strip()
		if not entryFull:
			pos += chunkSize
			return None, pos
		try:
			entryRoot = etree.fromstring(entryFull)
		except etree.XMLSyntaxError as e:
			log.error(f"{self._buf[pos-plus:pos+100]}")
			log.error(
				f"chunkSize={chunkSize}, plus={plus}, pos={pos}, len(buf)={len(self._buf)}"
			)
			log.error(f"entryFull={entryFull!r}")
			raise e
		entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
		if not entryElems:
			return None, pos
		word = entryElems[0].xpath("./@d:title", namespaces=entryRoot.nsmap)[0]
		if self._html:
			defi = self.decode(etree.tostring(entryElems[0]))
		else:
			defi = "".join([
				self.decode(etree.tostring(child))
				for child in entryElems[0].iterdescendants()
			])
		pos += chunkSize
		if self._limit <= 0:
			raise ValueError(f"self._limit = {self._limit}")
		return self._glos.newEntry(
			word, defi,
			defiFormat=self._defiFormat,
			byteProgress=(self._absPos, self._limit),
		), pos

	def __iter__(self):
		file = self._file
		limit = self._limit
		while True:
			self._absPos = file.tell()
			if self._absPos >= limit:
				break
			bufSizeB = file.read(4)  # type: bytes
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

			bufSize, = unpack("i", bufSizeB)  # type: int
			self._buf = decompress(file.read(bufSize)[8:])

			pos = 0
			while pos < len(self._buf):
				entry, pos = self._readEntry(pos)
				if entry is not None:
					yield entry
