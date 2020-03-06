# -*- coding: utf-8 -*-

# Copyright (C) 2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
description = "AppleDict Binary (.dictionary)"
extensions = [".dictionary", ".data"]

from lxml import etree

class Reader(object):
	def __init__(self, glos):
		self._glos = glos
		self._filename = ""
		self._file = None
		self._encoding = "utf-8"

	def open(self, filename):
		parts = filename.split(os.sep)
		dbname = parts[-1]
		if isdir(filename):
			if parts[-1] == "Contents":
				filename = join(filename, "Body.data")
				if len(parts) > 2:
					dbname = parts[-2]
			else:
				filename = join(filename, "Contents/Body.data")
		elif dbname == "Body.data" and len(parts) > 1:
			dbname = parts[-2]
			if len(parts) > 2 and dbname == "Contents":
				dbname =  parts[-3]

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

	def getChunkSize(self, buf, pos):
		plus = buf[pos:pos+12].find(b"<d:entry")
		if plus < 1:
			return 0, 0
		bs = buf[pos:pos+plus]
		if plus < 4:
			bs = b"\x00" * (4 - plus) + bs
		try:
			chunkSize, = unpack("i", bs)
		except Exception as e:
			log.error(f"{buf[pos:pos+100]}")
			raise e
		return chunkSize, plus

	def __iter__(self):
		file = self._file
		limit = self._limit
		while file.tell() < limit:
			bufSizeB = file.read(4)  # type: bytes
			# alternative for buf, bufSize is calculated
			# ~ flag = f.tell()
			# ~ bufSize = 0
			# ~ while True:
				# ~ zipp = f.read(bufSize)
				# ~ try:
					# ~ # print(zipp)
					# ~ input(zipp.decode(self._encoding))
					# ~ buf = decompress(zipp[8:])
					# ~ # print(buf)
					# ~ break
				# ~ except:
					# ~ print(bufSize)
					# ~ f.seek(flag)
					# ~ bufSize = bufSize+1

			bufSize, = unpack("i", bufSizeB)  # type: int
			buf = decompress(file.read(bufSize)[8:])

			pos = 0
			while pos < len(buf):
				chunkSize, plus = self.getChunkSize(buf, pos)
				pos += plus
				if chunkSize == 0:
					endI = buf[pos:].find(b"</d:entry>")
					if endI == -1:
						chunkSize = len(buf) - pos
					else:
						chunkSize = endI + 10
				entryFull = self.decode(buf[pos:pos+chunkSize])
				entryFull = entryFull.strip()
				if not entryFull:
					pos += chunkSize
					continue
				try:
					entryRoot = etree.fromstring(entryFull)
				except etree.XMLSyntaxError as e:
					log.error(f"\n{buf[pos-plus:pos+100]}")
					log.error(f"chunkSize={chunkSize}, plus={plus}, pos={pos}, len(buf)={len(buf)}")
					log.error(f"entryFull={entryFull!r}")
					raise e
				entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
				if not entryElems:
					continue
				entryElem = entryElems[0]
				word = entryElem.xpath("./@d:title", namespaces=entryRoot.nsmap)[0]
				defi = "".join([
					self.decode(etree.tostring(child))
					for child in entryElem.iterdescendants()
				])
				yield self._glos.newEntry(
					word,
					defi,
				)
				pos += chunkSize
