# -*- coding: utf-8 -*-
import sys

import os
from os.path import (
	dirname,
	getsize,
	realpath,
)
import re
import gzip
from time import time as now
from collections import Counter

from pyglossary.text_utils import (
	uint32ToBytes,
	uint32FromBytes,
)

from formats_common import *

enable = True
format = "Stardict"
description = "StarDict (ifo)"
extensions = (".ifo",)
optionsProp = {
	"stardict_client": BoolOption(),
	"dictzip": BoolOption(),
	"sametypesequence": StrOption(
		values=["", "h", "m", "x", None],
	),
	"merge_syns": BoolOption(),
	"xdxf_to_html": BoolOption(),
}
sortOnWrite = ALWAYS
# sortKey is defined in Writer class

if os.getenv("PYGLOSSARY_STARDICT_NO_FORCE_SORT") == "1":
	sortOnWrite = DEFAULT_YES

tools = [
	{
		"name": "StarDict",
		"web": "http://www.huzheng.org/stardict/",
		"platforms": ["Linux", "Windows", "Mac"],
		"license": "GPL",
	},
	{
		"name": "GoldenDict",
		"web": "http://goldendict.org/",
		"platforms": ["Linux", "Windows"],
		"license": "GPL",
	},
	{
		"name": "GoldenDict Mobile",
		"web": "http://goldendict.mobi/",
		"platforms": ["Android"],
		"license": "Unknown",
	},
	{
		"name": "Twinkle Star Dictionary",
		"web": "https://play.google.com/store/apps/details?id=com.qtier.dict",
		"platforms": ["Android"],
		"license": "Unknown",
		# last release: 2015/10/19
		# could not find the source code, license or website
	},
	{
		"name": "WordMateX",
		"web": "https://apkcombo.com/wordmatex/org.d1scw0rld.wordmatex/",
		"platforms": ["Android"],
		"license": "Proprietary",
		# last release: 2020/01/01, version 2.1.1
		# Google Play says "not compatible with your devices", no letting me
		# download and install, so I downloaded apk from apkcombo.com
		# This is the only Android app (not just for StarDict format) I found
		# that supports auto-RTL
	},
	{
		"name": "QDict",
		"web": "https://github.com/namndev/QDict",
		"platforms": ["Android"],
		"license": "Apache 2.0",
		# last release: 2017/04/16 (keeps crashing on my device, unusable)
		# last commit: 2020/06/24
	},
]

infoKeys = (
	"bookname",
	"author",
	"email",
	"website",
	"description",
	"date",
)


# re_newline = re.compile("[\n\r]+")
re_newline = re.compile("\n\r?|\r\n?")


def newlinesToSpace(text: str) -> str:
	return re_newline.sub(" ", text)


def newlinesToBr(text: str) -> str:
	return re_newline.sub("<br>", text)


def verifySameTypeSequence(s: str) -> bool:
	if not s:
		return True
	if not s.isalpha():
		log.error("Invalid sametypesequence option")
		return False
	return True


class Reader(object):
	_xdxf_to_html = True

	def __init__(self, glos: GlossaryType):

		self._glos = glos
		self.clear()

		self._xdxf_tr = None

		"""
		indexData format
		indexData[i] - i-th record in index file,
						a tuple (previously a list) of length 3
		indexData[i][0] - b_word (bytes)
		indexData[i][1] - definition block offset in dict file (int)
		indexData[i][2] - definition block size in dict file (int)
		REMOVED:
			indexData[i][3] - list of definitions
			indexData[i][3][j][0] - definition data
			indexData[i][3][j][1] - definition type - "h", "m" or "x"
			indexData[i][4] - list of synonyms (strings)

		synDict:
			a dict { entryIndex -> altList }
		"""

	def xdxf_setup(self):
		from pyglossary.xdxf_transform import xdxf_to_html_transformer
		self._xdxf_tr = xdxf_to_html_transformer()

	def xdxf_transform(self, text: str):
		if self._xdxf_tr is None:
			self.xdxf_setup()
		return self._xdxf_tr(text)

	def close(self) -> None:
		if self._dictFile:
			self._dictFile.close()
		self.clear()

	def clear(self) -> None:
		self._dictFile = None
		self._filename = ""  # base file path, no extension
		self._indexData = []
		self._synDict = {}
		self._sametypesequence = ""
		self._resDir = ""
		self._resFileNames = []
		self._wordCount = None

	def open(self, filename: str) -> None:
		if splitext(filename)[1].lower() == ".ifo":
			self._filename = splitext(filename)[0]
		else:
			self._filename = filename
		self._filename = realpath(self._filename)
		self.readIfoFile()
		sametypesequence = self._glos.getInfo("sametypesequence")
		if not verifySameTypeSequence(sametypesequence):
			return False
		self._indexData = self.readIdxFile()
		self._wordCount = len(self._indexData)
		self._synDict = self.readSynFile()
		self._sametypesequence = sametypesequence
		if isfile(self._filename + ".dict.dz"):
			self._dictFile = gzip.open(self._filename + ".dict.dz", mode="rb")
		else:
			self._dictFile = open(self._filename + ".dict", mode="rb")
		self._resDir = join(dirname(self._filename), "res")
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []
		# self.readResources()

	def __len__(self) -> int:
		if self._wordCount is None:
			raise RuntimeError(
				"StarDict: len(reader) called while reader is not open"
			)
		return self._wordCount + len(self._resFileNames)

	def readIfoFile(self) -> None:
		"""
		.ifo file is a text file in utf-8 encoding
		"""
		with open(self._filename + ".ifo", "r", encoding="utf-8") as ifoFile:
			for line in ifoFile:
				line = line.strip()
				if not line:
					continue
				if line == "StarDict's dict ifo file":
					continue
				key, _, value = line.partition("=")
				if not (key and value):
					log.warning(f"Invalid ifo file line: {line}")
					continue
				self._glos.setInfo(key, value)

	def readIdxFile(self) -> "List[Tuple[bytes, int, int]]":
		if isfile(self._filename + ".idx.gz"):
			with gzip.open(self._filename + ".idx.gz") as idxFile:
				idxBytes = idxFile.read()
		else:
			with open(self._filename + ".idx", "rb") as idxFile:
				idxBytes = idxFile.read()

		indexData = []
		pos = 0
		while pos < len(idxBytes):
			beg = pos
			pos = idxBytes.find(b"\x00", beg)
			if pos < 0:
				log.error("Index file is corrupted")
				break
			b_word = idxBytes[beg:pos]
			pos += 1
			if pos + 8 > len(idxBytes):
				log.error("Index file is corrupted")
				break
			offset = uint32FromBytes(idxBytes[pos:pos + 4])
			pos += 4
			size = uint32FromBytes(idxBytes[pos:pos + 4])
			pos += 4
			indexData.append((b_word, offset, size))

		return indexData

	def __iter__(self) -> "Iterator[BaseEntry]":
		indexData = self._indexData
		synDict = self._synDict
		sametypesequence = self._sametypesequence
		dictFile = self._dictFile

		if not dictFile:
			raise RuntimeError("iterating over a reader while it's not open")

		if not indexData:
			log.warning("indexData is empty")
			return

		for entryIndex, (b_word, defiOffset, defiSize) in enumerate(indexData):
			if not b_word:
				continue

			dictFile.seek(defiOffset)
			if dictFile.tell() != defiOffset:
				log.error(f"Unable to read definition for word {b_word}")
				continue

			b_defiBlock = dictFile.read(defiSize)

			if len(b_defiBlock) != defiSize:
				log.error(f"Unable to read definition for word {b_word}")
				continue

			if sametypesequence:
				defisData = self.parseDefiBlockCompact(
					b_defiBlock,
					sametypesequence,
				)
			else:
				defisData = self.parseDefiBlockGeneral(b_defiBlock)

			if defisData is None:
				log.error(f"Data file is corrupted. Word {b_word}")
				continue

			# defisData is a list of (b_defi, defiFormatCode) tuples

			defis = []
			defiFormats = []
			for b_partDefi, defiFormatCode in defisData:
				partDefi = b_partDefi.decode("utf-8")
				partDefiFormat = {
					"m": "m",
					"t": "m",
					"y": "m",
					"g": "h",
					"h": "h",
					"x": "x",
				}.get(chr(defiFormatCode), "")
				if partDefiFormat == "x" and self._xdxf_to_html:
					partDefi = self.xdxf_transform(partDefi)
					partDefiFormat = "h"
				defis.append(partDefi)
				defiFormats.append(partDefiFormat)

			# FIXME
			defiFormat = defiFormats[0]
			# defiFormat = Counter(defiFormats).most_common(1)[0][0]

			if not defiFormat:
				log.warning(f"Definition format {defiFormat!r} is not supported")

			word = b_word.decode("utf-8")
			try:
				alts = synDict[entryIndex]
			except KeyError:  # synDict is dict
				pass
			else:
				word = [word] + alts

			defiSep = "\n<hr>\n"
			# if defiFormat == "x"
			# 	defiSep = FIXME
			defi = defiSep.join(defis)

			# FIXME:
			# defi = defi.replace(' src="./res/', ' src="./')
			yield self._glos.newEntry(word, defi, defiFormat=defiFormat)

		if isdir(self._resDir):
			for fname in os.listdir(self._resDir):
				fpath = join(self._resDir, fname)
				with open(fpath, "rb") as fromFile:
					yield self._glos.newDataEntry(
						fname,
						fromFile.read(),
					)

	def readSynFile(self) -> "Dict[int, List[str]]":
		"""
		return synDict, a dict { entryIndex -> altList }
		"""
		if not isfile(self._filename + ".syn"):
			return {}
		with open(self._filename + ".syn", "rb") as synFile:
			synBytes = synFile.read()
		synBytesLen = len(synBytes)
		synDict = {}
		pos = 0
		while pos < synBytesLen:
			beg = pos
			pos = synBytes.find(b"\x00", beg)
			if pos < 0:
				log.error("Synonym file is corrupted")
				break
			b_alt = synBytes[beg:pos]  # b_alt is bytes
			pos += 1
			if pos + 4 > len(synBytes):
				log.error("Synonym file is corrupted")
				break
			entryIndex = uint32FromBytes(synBytes[pos:pos + 4])
			pos += 4
			if entryIndex >= self._wordCount:
				log.error(
					f"Corrupted synonym file. " +
					f"Word {b_alt} references invalid item"
				)
				continue

			s_alt = b_alt.decode("utf-8")  # s_alt is str
			try:
				synDict[entryIndex].append(s_alt)
			except KeyError:
				synDict[entryIndex] = [s_alt]

		return synDict

	def parseDefiBlockCompact(
		self,
		b_block: bytes,
		sametypesequence: str,
	) -> "List[Tuple[bytes, int]]":
		"""
		Parse definition block when sametypesequence option is specified.

		Return a list of (b_defi, defiFormatCode) tuples
			where b_defi is a bytes instance
			and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
		"""
		b_sametypesequence = sametypesequence.encode("utf-8")
		assert len(b_sametypesequence) > 0
		res = []
		i = 0
		for t in b_sametypesequence[:-1]:
			if i >= len(b_block):
				return None
			if bytes([t]).islower():
				beg = i
				i = b_block.find(b"\x00", beg)
				if i < 0:
					return None
				res.append((b_block[beg:i], t))
				i += 1
			else:
				assert bytes([t]).isupper()
				if i + 4 > len(b_block):
					return None
				size = uint32FromBytes(b_block[i:i + 4])
				i += 4
				if i + size > len(b_block):
					return None
				res.append((b_block[i:i + size], t))
				i += size

		if i >= len(b_block):
			return None
		t = b_sametypesequence[-1]
		if bytes([t]).islower():
			if 0 in b_block[i:]:
				return None
			res.append((b_block[i:], t))
		else:
			assert bytes([t]).isupper()
			res.append((b_block[i:], t))

		return res

	def parseDefiBlockGeneral(self, b_block: bytes) -> "List[Tuple[bytes, int]]":
		"""
		Parse definition block when sametypesequence option is not specified.

		Return a list of (b_defi, defiFormatCode) tuples
			where b_defi is a bytes instance
			and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
		"""
		res = []
		i = 0
		while i < len(b_block):
			t = b_block[i]
			if not bytes([t]).isalpha():
				return None
			i += 1
			if bytes([t]).islower():
				beg = i
				i = b_block.find(b"\x00", beg)
				if i < 0:
					return None
				res.append((b_block[beg:i], t))
				i += 1
			else:
				assert bytes([t]).isupper()
				if i + 4 > len(b_block):
					return None
				size = uint32FromBytes(b_block[i:i + 4])
				i += 4
				if i + size > len(b_block):
					return None
				res.append((b_block[i:i + size], t))
				i += size
		return res

	# def readResources(self):
	# 	if not isdir(self._resDir):
	# 		resInfoPath = join(baseDirPath, "res.rifo")
	# 		if isfile(resInfoPath):
	# 			log.warning(
	# 				"StarDict resource database is not supported. Skipping"
	# 			)


class Writer(object):
	_dictzip: bool = True
	_sametypesequence: str = ""  # type: Literal["", "h", "m", "x", None]
	_stardict_client: bool = False
	_merge_syns: bool = False

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self._filename = None
		self._resDir = None
		self._sourceLang = None
		self._targetLang = None
		self._p_pattern = re.compile(
			'<p( [^<>]*?)?>(.*?)</p>',
			re.DOTALL,
		)
		self._br_pattern = re.compile(
			"<br[ /]*>",
			re.IGNORECASE,
		)

	def sortKey(self, b_word: bytes) -> "Tuple[bytes, bytes]":
		assert isinstance(b_word, bytes)
		return (
			b_word.lower(),
			b_word,
		)

	def finish(self) -> None:
		self._filename = None
		self._resDir = None
		self._sourceLang = None
		self._targetLang = None

	def open(self, filename: str) -> None:
		log.debug(f"open: filename = {filename}")
		fileBasePath = filename
		##
		if splitext(filename)[1].lower() == ".ifo":
			fileBasePath = splitext(filename)[0]
		elif filename.endswith(os.sep):
			if not isdir(filename):
				os.makedirs(filename)
			fileBasePath = join(filename, split(filename[:-1])[-1])
		elif isdir(filename):
			fileBasePath = join(filename, split(filename)[-1])

		parentDir = split(fileBasePath)[0]
		if not isdir(parentDir):
			log.info(f"Creating directory {parentDir}")
			os.mkdir(parentDir)
		##
		if fileBasePath:
			fileBasePath = realpath(fileBasePath)
		self._filename = fileBasePath
		self._resDir = join(dirname(fileBasePath), "res")
		self._sourceLang = self._glos.sourceLang
		self._targetLang = self._glos.targetLang
		if self._sametypesequence:
			log.debug(f"Using write option sametypesequence={self._sametypesequence}")
		elif self._sametypesequence is not None:
			stat = self._glos.collectDefiFormat(100)
			log.debug(f"defiFormat stat: {stat}")
			if stat:
				if stat["m"] > 0.97:
					log.info(f"Auto-selecting sametypesequence=m")
					self._sametypesequence = "m"
				elif stat["h"] > 0.5:
					log.info(f"Auto-selecting sametypesequence=h")
					self._sametypesequence = "h"

	def write(self) -> "Generator[None, BaseEntry, None]":
		from pyglossary.os_utils import runDictzip
		if self._sametypesequence:
			if self._merge_syns:
				yield from self.writeCompactMergeSyns(self._sametypesequence)
			else:
				yield from self.writeCompact(self._sametypesequence)
		else:
			if self._merge_syns:
				yield from self.writeGeneralMergeSyns()
			else:
				yield from self.writeGeneral()
		if self._dictzip:
			runDictzip(f"{self._filename}.dict")

	def fixDefi(self, defi: str, defiFormat: str) -> str:
		# for StarDict 3.0:
		if self._stardict_client and defiFormat == "h":
			defi = self._p_pattern.sub("\\2<br>", defi)
			# if there is </p> left without opening, replace with <br>
			defi = defi.replace("</p>", "<br>")
			defi = self._br_pattern.sub("<br>", defi)

		# FIXME:
		# defi = defi.replace(' src="./', ' src="./res/')
		return defi

	def writeCompact(self, defiFormat):
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		Parameters:
		defiFormat - format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompact: defiFormat={defiFormat}")
		dictMark = 0
		altIndexList = []  # list of tuples (b"alternate", entryIndex)

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		t0 = now()
		wordCount = 0
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			for alt in words[1:]:
				altIndexList.append((alt.encode("utf-8"), entryIndex))

			b_dictBlock = defi.encode("utf-8")
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			b_idxBlock = word.encode("utf-8") + b"\x00" + \
				uint32ToBytes(dictMark) + \
				uint32ToBytes(blockLen)
			idxFile.write(b_idxBlock)

			dictMark += blockLen
			wordCount += 1

		dictFile.close()
		idxFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat=defiFormat,
		)

	def writeGeneral(self) -> None:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug(f"writeGeneral")
		dictMark = 0
		altIndexList = []  # list of tuples (b"alternate", entryIndex)

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		t0 = now()
		wordCount = 0
		defiFormatCounter = Counter()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			entry.detectDefiFormat()  # call no more than once
			defiFormat = entry.defiFormat
			defiFormatCounter[defiFormat] += 1
			if defiFormat not in ("h", "m", "x"):
				log.error(f"invalid defiFormat={defiFormat}, using 'm'")
				defiFormat = "m"

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			for alt in words[1:]:
				altIndexList.append((alt.encode("utf-8"), entryIndex))

			b_dictBlock = (defiFormat + defi).encode("utf-8") + b"\x00"
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			b_idxBlock = word.encode("utf-8") + b"\x00" + \
				uint32ToBytes(dictMark) + \
				uint32ToBytes(blockLen)
			idxFile.write(b_idxBlock)

			dictMark += blockLen
			wordCount += 1

		dictFile.close()
		idxFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")
		log.debug("defiFormatsCount = " + pformat(defiFormatCounter.most_common()))

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat="",
		)

	def writeSynFile(self, altIndexList: "List[Tuple[bytes, int]]") -> None:
		"""
		Build .syn file
		"""
		if not altIndexList:
			return

		log.info(f"Sorting {len(altIndexList)} synonyms...")
		t0 = now()

		altIndexList.sort(
			key=lambda x: self.sortKey(x[0])
		)
		# 28 seconds with old sort key (converted from custom cmp)
		# 0.63 seconds with my new sort key
		# 0.20 seconds without key function (default sort)

		log.info(
			f"Sorting {len(altIndexList)} synonyms took {now()-t0:.2f} seconds",
		)
		log.info(f"Writing {len(altIndexList)} synonyms...")
		t0 = now()
		with open(self._filename + ".syn", "wb") as synFile:
			synFile.write(b"".join([
				b_alt + b"\x00" + uint32ToBytes(entryIndex)
				for b_alt, entryIndex in altIndexList
			]))
		log.info(
			f"Writing {len(altIndexList)} synonyms took {now()-t0:.2f} seconds",
		)

	def writeCompactMergeSyns(self, defiFormat):
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		Parameters:
		defiFormat - format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompactMergeSyns: defiFormat={defiFormat}")
		dictMark = 0
		idxBlockList = []  # list of tuples (b"word", startAndLength)
		altIndexList = []  # list of tuples (b"alternate", entryIndex)

		dictFile = open(self._filename + ".dict", "wb")

		t0 = now()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			b_dictBlock = defi.encode("utf-8")
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			blockData = uint32ToBytes(dictMark) + uint32ToBytes(blockLen)
			for word in words:
				idxBlockList.append((word.encode("utf-8"), blockData))

			dictMark += blockLen

		wordCount = self.writeIdxFile(idxBlockList)

		dictFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")

		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat=defiFormat,
		)

	def writeGeneralMergeSyns(self) -> None:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug(f"writeGeneralMergeSyns")
		dictMark = 0
		idxBlockList = []  # list of tuples (b"word", startAndLength)
		altIndexList = []  # list of tuples (b"alternate", entryIndex)

		dictFile = open(self._filename + ".dict", "wb")

		t0 = now()
		wordCount = 0
		defiFormatCounter = Counter()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		entryIndex = -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			entry.detectDefiFormat()  # call no more than once
			defiFormat = entry.defiFormat
			defiFormatCounter[defiFormat] += 1
			if defiFormat not in ("h", "m", "x"):
				log.error(f"invalid defiFormat={defiFormat}, using 'm'")
				defiFormat = "m"

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			b_dictBlock = (defiFormat + defi).encode("utf-8") + b"\x00"
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			blockData = uint32ToBytes(dictMark) + uint32ToBytes(blockLen)
			for word in words:
				idxBlockList.append((word.encode("utf-8"), blockData))

			dictMark += blockLen

		wordCount = self.writeIdxFile(idxBlockList)

		dictFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now()-t0:.2f} seconds")
		log.debug("defiFormatsCount = " + pformat(defiFormatCounter.most_common()))

		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat="",
		)

	def writeIdxFile(self, indexList: "List[Tuple[bytes, bytes]]") -> int:
		filename = self._filename + ".idx"
		if not indexList:
			return 0

		log.info(f"Sorting {len(indexList)} items...")
		t0 = now()

		indexList.sort(key=lambda x: self.sortKey(x[0]))
		log.info(
			f"Sorting {len(indexList)} {filename} took {now()-t0:.2f} seconds",
		)
		log.info(f"Writing {len(indexList)} index entries...")
		t0 = now()
		with open(filename, "wb") as indexFile:
			indexFile.write(b"".join([
				key + b"\x00" + value
				for key, value in indexList
			]))
		log.info(
			f"Writing {len(indexList)} {filename} took {now()-t0:.2f} seconds",
		)
		return len(indexList)

	def writeIfoFile(
		self,
		wordCount: int,
		synWordCount: int,
		defiFormat: str = "",  # type: Literal["", "h", "m", "x"]
	) -> None:
		"""
		Build .ifo file
		"""
		glos = self._glos
		bookname = newlinesToSpace(glos.getInfo("name"))
		indexFileSize = getsize(self._filename + ".idx")

		sourceLang = self._sourceLang
		targetLang = self._targetLang
		if sourceLang and targetLang:
			langs = f"{sourceLang.code}-{targetLang.code}"
			if langs not in bookname.lower():
				bookname = f"{bookname} ({langs})"
			log.info(f"bookname: {bookname}")

		ifo = [
			("version", "3.0.0"),
			("bookname", bookname),
			("wordcount", wordCount),
			("idxfilesize", indexFileSize),
		]
		if defiFormat:
			ifo.append(("sametypesequence", defiFormat))
		if synWordCount > 0:
			ifo.append(("synwordcount", synWordCount))

		desc = glos.getInfo("description")
		copyright = glos.getInfo("copyright")
		if copyright:
			desc = f"{copyright}\n{desc}"
		publisher = glos.getInfo("publisher")
		if publisher:
			desc = f"Publisher: {publisher}\n{desc}"

		for key in infoKeys:
			if key in (
				"bookname",
				"description",
			):
				continue
			value = glos.getInfo(key)
			if value == "":
				continue
			value = newlinesToSpace(value)
			ifo.append((key, value))

		ifo.append(("description", newlinesToBr(desc)))

		ifoStr = "StarDict's dict ifo file\n"
		for key, value in ifo:
			ifoStr += f"{key}={value}\n"
		with open(self._filename + ".ifo", "w", encoding="utf-8") as ifoFile:
			ifoFile.write(ifoStr)
