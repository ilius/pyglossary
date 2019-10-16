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
					# ~ input(zipp.decode("utf-8"))
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
				chunkSize, = unpack("i", buf[pos:pos+4])
				entryFull = buf[pos:pos+chunkSize].decode("utf-8")
				entryRoot = etree.fromstring(entryFull)
				entryElems = entryRoot.xpath("/d:entry", namespaces=entryRoot.nsmap)
				if not entryElems:
					continue
				entryElem = entryElems[0]
				word = entryElem.xpath("./@d:title", namespaces=entryRoot.nsmap)[0]
				defi = "".join([
					etree.tostring(child).decode("utf8")
					for child in entryElem.iterdescendants()
				])
				yield self._glos.newEntry(
					word,
					defi,
				)
				pos += chunkSize
