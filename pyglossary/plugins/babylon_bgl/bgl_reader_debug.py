# -*- coding: utf-8 -*-
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from .bgl_reader import BglReader
from pyglossary.text_utils import toStr, isASCII


class MetaData(object):
	def __init__(self):
		self.blocks = []
		self.numEntries = None
		self.numBlocks = None
		self.numFiles = None
		self.gzipStartOffset = None
		self.gzipEndOffset = None
		self.fileSize = None
		self.bglHeader = None  # data before gzip header


class MetaDataBlock(object):
	def __init__(self, data, _type):
		self.data = data
		self.type = _type


class MetaDataRange(object):
	def __init__(self, _type, count):
		self.type = _type
		self.count = count


class MetaData2(object):
	"""
	Second pass metadata.
	We need to scan all definitions in order to collect these
	statistical data.
	"""
	def __init__(self):
		# defiTrailingFields[i] - number of fields with code i found
		self.defiTrailingFields = [0] * 256
		self.isDefiASCII = True
		# isDefiASCII = true if all definitions contain only ASCII chars
		"""
		We apply a number of tests to each definition, excluding those with
		overwritten encoding (they start with <charset c=U>).
		defiProcessedCount - total number of definitions processed
		defiUtf8Count - number of definitions in utf8 encoding
		defiAsciiCount - number of definitions containing only ASCII chars
		"""
		self.defiProcessedCount = 0
		self.defiUtf8Count = 0
		self.defiAsciiCount = 0
		self.charRefs = dict()  # encoding -> [ 0 ] * 257


class GzipWithCheck(object):
	"""
	gzip.GzipFile with check.
	It checks that unpacked data match what was packed.
	"""
	def __init__(self, fileobj, unpackedPath, reader, closeFileobj=False):
		"""
		constructor

		fileobj - gzip file - archive
		unpackedPath - path of a file containing original data, for testing.
		reader - reference to BglReader class instance, used for logging.
		"""
		self.file = BGLGzipFile(
			fileobj=fileobj,
			closeFileobj=closeFileobj,
		)
		self.unpackedFile = open(unpackedPath, "rb")
		self.reader = reader

	def __del__(self):
		self.close()

	def close(self):
		if self.file:
			self.file.close()
			self.file = None
		if self.unpackedFile:
			self.unpackedFile.close()
			self.unpackedFile = None

	def read(self, size=-1):
		buf1 = self.file.read(size)
		buf2 = self.unpackedFile.read(size)
		if buf1 != buf2:
			self.reader.msgLogFileWrite(
				f"GzipWithCheck.read: !=: size = {buf1}, ({buf2}) ({size})",
			)
		# else:
		# 	self.reader.msgLogFileWrite(
		# 		f"GzipWithCheck.read: ==: size = {buf1}, ({buf2}) ({size})",
		# 	)
		return buf1

	def seek(self, offset, whence=os.SEEK_SET):
		self.file.seek(offset, whence)
		self.unpackedFile.seek(offset, whence)
		# self.reader.msgLogFileWrite(
		# 	f"GzipWithCheck.seek: offset = {offset}, whence = {whence}",
		# )

	def tell(self):
		pos1 = self.file.tell()
		pos2 = self.unpackedFile.tell()
		if pos1 != pos2:
			self.reader.msgLogFileWrite(
				f"GzipWithCheck.tell: !=: {pos1} {pos2}",
			)
		# else:
		# 	self.reader.msgLogFileWrite(
		# 		f"GzipWithCheck.tell: ==: {pos1} {pos2}",
		# 	)
		return pos1

	def flush(self):
		if os.sep == "\\":
			pass
			# a bug in Windows
			# after file.flush, file.read returns garbage
		else:
			self.file.flush()
			self.unpackedFile.flush()


class DebugBglReader(BglReader):
	_collect_metadata2 = False
	_search_char_samples = False
	_write_gz = False
	_raw_dump_path = None
	_unpacked_gzip_path = None
	_char_samples_path = None
	_msg_log_path = None

	def open(
		self,
		filename,
	):
		if not BglReader.open(self, filename):
			return

		self.metadata2 = MetaData2() if self._collect_metadata2 else None
		if self._search_char_samples:
			self.targetCharsArray = ([False] * 256)
		else:
			self.targetCharsArray = None

		if self._raw_dump_path:
			self.rawDumpFile = open(self._raw_dump_path, "w")
		if self._char_samples_path:
			self.samplesDumpFile = open(self._char_samples_path, "w")
		if self._msg_log_path:
			self.msgLogFile = open(self._msg_log_path, "w")

		self.charRefStatPattern = re.compile(b"(&#\\w+;)", re.I)

	def openGzip(self):
		with open(self._filename, "rb") as bglFile:
			if not bglFile:
				log.error(f"file pointer empty: {bglFile}")
				return False
			buf = bglFile.read(6)
			if len(buf) < 6 or not buf[:4] in (
				b"\x12\x34\x00\x01",
				b"\x12\x34\x00\x02",
			):
				log.error(f"invalid header: {buf[:6]!r}")
				return False
			self.gzipOffset = gzipOffset = uintFromBytes(buf[4:6])
			log.debug(f"Position of gz header: {gzipOffset}")
			if gzipOffset < 6:
				log.error(f"invalid gzip header position: {gzipOffset}")
				return False

			if self._write_gz:
				self.dataFile = self._filename + "-data.gz"
				try:
					f2 = open(self.dataFile, "wb")
				except IOError:
					log.exception("error while opening gzip data file")
					self.dataFile = join(
						tmpDir,
						os.path.split(self.m_filename)[-1] + "-data.gz"
					)
					f2 = open(self.dataFile, "wb")
				bglFile.seek(i)
				f2.write(bglFile.read())
				f2.close()
				self.file = gzip.open(self.dataFile, "rb")
			else:
				f2 = FileOffS(self._filename, gzipOffset)
				if self._unpacked_gzip_path:
					self.file = GzipWithCheck(
						f2,
						self._unpacked_gzip_path,
						self,
						closeFileobj=True,
					)
				else:
					self.file = BGLGzipFile(
						fileobj=f2,
						closeFileobj=True,
					)

	def close(self):
		BglReader.close(self)
		if self.rawDumpFile:
			self.rawDumpFile.close()
			self.rawDumpFile = None
		if self.msgLogFile:
			self.msgLogFile.close()
			self.msgLogFile = None
		if self.samplesDumpFile:
			self.samplesDumpFile.close()
			self.samplesDumpFile = None

	def __del__(self):
		BglReader.__del__(self)

	def readEntryWord(self, block, pos):
		succeed, pos, u_word, b_word = \
			BglReader.readEntryWord(self, block, pos)
		if not succeed:
			return
		self.rawDumpFileWriteText(f"\n\nblock type = {block.type}\nkey = ")
		self.rawDumpFileWriteData(b_word)

	def readEntryDefi(self, block, pos, b_key):
		succeed, pos, u_defi, b_defi = \
			BglReader.readEntryDefi(self, block, pos, b_key)
		if not succeed:
			return
		self.rawDumpFileWriteText("\ndefi = ")
		self.rawDumpFileWriteData(b_defi)

	"""
	def readEntryAlts(self, block, pos, b_key, key):
		succeed, pos, alts, b_alts = \
			BglReader.readEntryAlts(self, block, pos, b_key, key)
		if not succeed:
			return
		for b_alt in b_alts:
			self.rawDumpFileWriteText("\nalt = ")
			self.rawDumpFileWriteData(b_alt)
	"""

	def charReferencesStat(self, b_text, encoding):
		"""
			b_text is bytes instance
		"""
		# &#0147;
		# &#x010b;
		if not self.metadata2:
			return

		if encoding not in self.metadata2.charRefs:
			self.metadata2.charRefs[encoding] = [0] * 257
		charRefs = self.metadata2.charRefs[encoding]

		for index, b_part in enumerate(self.charRefStatPattern.split(b_text)):
			if index % 2 != 1:
				continue
			try:
				if b_part[:3].lower() == "&#x":
					code = int(b_part[3:-1], 16)
				else:
					code = int(b_part[2:-1])
			except (ValueError, OverflowError):
				continue
			if code <= 0:
				continue
			code = min(code, 256)
			charRefs[code] += 1

	def processDefiStat(self, fields, b_defi, b_key):
		if fields.singleEncoding:
			self.findAndPrintCharSamples(
				fields.b_defi,
				f"defi, key = {b_key}",
				fields.encoding,
			)
			if self.metadata2:
				self.metadata2.defiProcessedCount += 1
				if isASCII(toStr(fields.b_defi)):
					self.metadata2.defiAsciiCount += 1
				try:
					fields.b_defi.decode("utf-8")
				except UnicodeError:
					pass
				else:
					self.metadata2.defiUtf8Count += 1
		if self.metadata2 and self.metadata2.isDefiASCII:
			if not isASCII(fields.u_defi):
				self.metadata2.isDefiASCII = False

	# write text to dump file as is
	def rawDumpFileWriteText(self, text):  # FIXME
		text = toStr(text)
		if self.rawDumpFile:
			self.rawDumpFile.write(text)

	# write data to dump file unambiguously representing control chars
	# escape "\" with "\\"
	# print control chars as "\xhh"
	def rawDumpFileWriteData(self, text):
		text = toStr(text)
		# the next function escapes too many chars, for example, it escapes äöü
		# self.rawDumpFile.write(text.encode("unicode_escape"))
		if self.rawDumpFile:
			self.rawDumpFile.write(text)

	def msgLogFileWrite(self, text):
		text = toStr(text)
		if self.msgLogFile:
			offset = self.msgLogFile.tell()
			# print offset in the log file to facilitate navigating this
			# log in hex editor
			# intended usage:
			# the log file is opened in a text editor and hex editor
			# use text editor to read error messages, use hex editor to
			# inspect char codes offsets allows to quickly jump to the right
			# place of the file hex editor
			self.msgLogFile.write(f"\noffset = {offset:#02x}\n")
			self.msgLogFile.write(text + "\n")
		else:
			log.debug(text)

	def samplesDumpFileWrite(self, text):
		text = toStr(text)
		if self.samplesDumpFile:
			offset = self.samplesDumpFile.tell()
			self.samplesDumpFile.write(f"\noffset = {offset:#02x}\n")
			self.samplesDumpFile.write(text + "\n")
		else:
			log.debug(text)

	def dumpBlocks(self, dumpPath):
		import pickle
		self.file.seek(0)
		metaData = MetaData()
		metaData.numFiles = 0
		metaData.gzipStartOffset = self.gzipOffset

		self.numEntries = 0
		self.numBlocks = 0
		range_type = None
		range_count = 0
		block = Block()
		while not self.isEndOfDictData():
			log.debug(
				f"readBlock: offset {self.file.tell():#02x}, "
				f"unpacked offset {self.file.unpackedFile.tell():#02x}"
			)
			if not self.readBlock(block):
				break
			self.numBlocks += 1

			if block.type in (1, 7, 10, 11, 13):
				self.numEntries += 1
			elif block.type == 2:  # Embedded File (mostly Image or HTML)
				metaData.numFiles += 1

			if block.type in (1, 2, 7, 10, 11, 13):
				if range_type == block.type:
					range_count += 1
				else:
					if range_count > 0:
						mblock = MetaDataRange(range_type, range_count)
						metaData.blocks.append(mblock)
						range_count = 0
					range_type = block.type
					range_count = 1
			else:
				if range_count > 0:
					mblock = MetaDataRange(range_type, range_count)
					metaData.blocks.append(mblock)
					range_count = 0
				mblock = MetaDataBlock(block.data, block.type)
				metaData.blocks.append(mblock)

		if range_count > 0:
			mblock = MetaDataRange(range_type, range_count)
			metaData.blocks.append(mblock)
			range_count = 0

		metaData.numEntries = self.numEntries
		metaData.numBlocks = self.numBlocks
		metaData.gzipEndOffset = self.file_bgl.tell()
		metaData.fileSize = os.path.getsize(self._filename)
		with open(self._filename, "rb") as f:
			metaData.bglHeader = f.read(self.gzipOffset)

		with open(dumpPath, "wb") as f:
			pickle.dump(metaData, f)

		self.file.seek(0)

	def dumpMetadata2(self, dumpPath):
		import pickle
		if not self.metadata2:
			return
		with open(dumpPath, "wb") as f:
			pickle.dump(self.metadata2, f)

	def processDefiStat(self, fields, defi, b_key):
		BglReader.processDefiStat(self, fields, defi, b_key)

		if fields.b_title:
			self.rawDumpFileWriteText("\ndefi title: ")
			self.rawDumpFileWriteData(fields.b_title)
		if fields.b_title_trans:
			self.rawDumpFileWriteText("\ndefi title trans: ")
			self.rawDumpFileWriteData(fields.b_title_trans)
		if fields.b_transcription_50:
			self.rawDumpFileWriteText(
				f"\ndefi transcription_50 ({fields.code_transcription_50:#x}): ",
			)
			self.rawDumpFileWriteData(fields.b_transcription_50)
		if fields.b_transcription_60:
			self.rawDumpFileWriteText(
				f"\ndefi transcription_60 ({fields.code_transcription_60:#x}): ",
			)
			self.rawDumpFileWriteData(fields.b_transcription_60)
		if fields.b_field_1a:
			self.rawDumpFileWriteText("\ndefi field_1a: ")
			self.rawDumpFileWriteData(fields.b_field_1a)
		if fields.b_field_13:
			self.rawDumpFileWriteText(
				f"\ndefi field_13 bytes: {fields.b_field_13!r}",
			)
		if fields.b_field_07:
			self.rawDumpFileWriteText("\ndefi field_07: ")
			self.rawDumpFileWriteData(fields.b_field_07)
		if fields.b_field_06:
			self.rawDumpFileWriteText(
				f"\ndefi field_06: {fields.b_field_06}",
			)

	# search for new chars in data
	# if new chars are found, mark them with a special sequence in the text
	# and print result into msg log
	def findAndPrintCharSamples(self, b_data, hint, encoding):
		assert isinstance(b_data, bytes)
		if not self.targetCharsArray:
			return
		offsets = self.findCharSamples(b_data)
		if len(offsets) == 0:
			return
		res = ""
		utf8 = (encoding.lower() == "utf-8")
		i = 0
		for o in offsets:
			j = o
			if utf8:
				while b_data[j] & 0xc0 == 0x80:
					j -= 1
			res += b_data[i:j]
			res += "!!!--+!!!"
			i = j
		res += b_data[j:]
		offsets_str = " ".join([str(el) for el in offsets])
		self.samplesDumpFileWrite(
			f"charSample({hint})\noffsets = {offsets_str}"
			f"\nmarked = {res}\norig = {b_data}\n",
		)

	def findCharSamples(self, b_data):
		"""
		Find samples of chars in b_data.

		Search for chars in data that have not been marked so far in
		the targetCharsArray array, mark new chars.
		Returns a list of offsets in b_data
		May return an empty list.
		"""
		res = []
		if not isinstance(b_data, bytes):
			log.error("findCharSamples: b_data is not a bytes instance")
			return res
		if not self.targetCharsArray:
			log.error("findCharSamples: self.targetCharsArray == None")
			return res
		for i, char in enumerate(b_data):
			if x < 128:
				continue
			if not self.targetCharsArray[x]:
				self.targetCharsArray[x] = True
				res.append(i)
		return res
