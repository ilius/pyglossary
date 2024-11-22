# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
import typing
from collections import Counter
from os.path import (
	dirname,
	getsize,
	isdir,
	isfile,
	join,
	realpath,
	split,
	splitext,
)
from pprint import pformat
from time import perf_counter as now
from typing import (
	TYPE_CHECKING,
	Any,
	Literal,
	Protocol,
	TypeVar,
)

if TYPE_CHECKING:
	import sqlite3
	from collections.abc import Callable, Generator, Iterator, Sequence

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.langs import Lang


from pyglossary.core import log
from pyglossary.glossary_utils import Error
from pyglossary.text_utils import (
	uint32ToBytes,
	uint64ToBytes,
)

__all__ = ["Writer"]

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


T_SDListItem_contra = TypeVar("T_SDListItem_contra", contravariant=True)


class T_SdList(Protocol[T_SDListItem_contra]):
	def append(self, x: T_SDListItem_contra) -> None: ...

	def __len__(self) -> int: ...

	def __iter__(self) -> Iterator[Any]: ...

	def sort(self) -> None: ...


class MemSdList:
	def __init__(self) -> None:
		self._l: list[Any] = []

	def append(self, x: Any) -> None:
		self._l.append(x)

	def __len__(self) -> int:
		return len(self._l)

	def __iter__(self) -> Iterator[Any]:
		return iter(self._l)

	def sortKey(self, item: "tuple[bytes, Any]") -> tuple[bytes, bytes]:  # noqa: PLR6301
		return (
			item[0].lower(),
			item[0],
		)

	def sort(self) -> None:
		self._l.sort(key=self.sortKey)


class BaseSqList:
	def __init__(
		self,
		filename: str,
	) -> None:
		from sqlite3 import connect

		if isfile(filename):
			log.warning(f"Renaming {filename} to {filename}.bak")
			os.rename(filename, filename + "bak")

		self._filename = filename

		self._con: "sqlite3.Connection | None" = connect(filename)
		self._cur: "sqlite3.Cursor | None" = self._con.cursor()

		if not filename:
			raise ValueError(f"invalid {filename=}")

		self._orderBy = "word_lower, word"
		self._sorted = False
		self._len = 0

		columns = self._columns = [
			("word_lower", "TEXT"),
			("word", "TEXT"),
		] + self.getExtraColumns()

		self._columnNames = ",".join(col[0] for col in columns)

		colDefs = ",".join(f"{col[0]} {col[1]}" for col in columns)
		self._con.execute(
			f"CREATE TABLE data ({colDefs})",
		)
		self._con.execute(
			f"CREATE INDEX sortkey ON data({self._orderBy});",
		)
		self._con.commit()

	@classmethod
	def getExtraColumns(cls) -> list[tuple[str, str]]:
		# list[(columnName, dataType)]
		return []

	def __len__(self) -> int:
		return self._len

	def append(self, item: Sequence) -> None:
		if self._cur is None or self._con is None:
			raise RuntimeError("db is closed")
		self._len += 1
		extraN = len(self._columns) - 1
		self._cur.execute(
			f"insert into data({self._columnNames}) values (?{', ?' * extraN})",
			[item[0].lower()] + list(item),
		)
		if self._len % 1000 == 0:
			self._con.commit()

	def sort(self) -> None:
		pass

	def close(self) -> None:
		if self._cur is None or self._con is None:
			return
		self._con.commit()
		self._cur.close()
		self._con.close()
		self._con = None
		self._cur = None

	def __del__(self) -> None:
		try:
			self.close()
		except AttributeError as e:
			log.error(str(e))

	def __iter__(self) -> Iterator[EntryType]:
		if self._cur is None:
			raise RuntimeError("db is closed")
		query = f"SELECT * FROM data ORDER BY {self._orderBy}"
		self._cur.execute(query)
		for row in self._cur:
			yield row[1:]


class IdxSqList(BaseSqList):
	@classmethod
	def getExtraColumns(cls) -> list[tuple[str, str]]:
		# list[(columnName, dataType)]
		return [
			("idx_block", "BLOB"),
		]


class SynSqList(BaseSqList):
	@classmethod
	def getExtraColumns(cls) -> list[tuple[str, str]]:
		# list[(columnName, dataType)]
		return [
			("entry_index", "INTEGER"),
		]


class Writer:
	_large_file: bool = False
	_dictzip: bool = True
	_sametypesequence: "Literal['', 'h', 'm', 'x'] | None" = ""
	_stardict_client: bool = False
	_merge_syns: bool = False
	_audio_goldendict: bool = False
	_audio_icon: bool = True
	_sqlite: bool = False

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resDir = ""
		self._sourceLang: "Lang | None" = None
		self._targetLang: "Lang | None" = None
		self._p_pattern = re.compile(
			"<p( [^<>]*?)?>(.*?)</p>",
			re.DOTALL,
		)
		self._br_pattern = re.compile(
			"<br[ /]*>",
			re.IGNORECASE,
		)
		self._re_audio_link = re.compile(
			'<a (type="sound" )?([^<>]*? )?href="sound://([^<>"]+)"( .*?)?>(.*?)</a>',
		)

	def finish(self) -> None:
		self._filename = ""
		self._resDir = ""
		self._sourceLang = None
		self._targetLang = None

	def open(self, filename: str) -> None:
		log.debug(f"open: {filename = }")
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
					log.info("Auto-selecting sametypesequence=m")
					self._sametypesequence = "m"
				elif stat["h"] > 0.5:
					log.info("Auto-selecting sametypesequence=h")
					self._sametypesequence = "h"

	def write(self) -> Generator[None, EntryType, None]:
		from pyglossary.os_utils import runDictzip

		if self._sametypesequence:
			if self._merge_syns:
				yield from self.writeCompactMergeSyns(self._sametypesequence)
			else:
				yield from self.writeCompact(self._sametypesequence)
		elif self._merge_syns:
			yield from self.writeGeneralMergeSyns()
		else:
			yield from self.writeGeneral()
		if self._dictzip:
			runDictzip(f"{self._filename}.dict")
			syn_file = f"{self._filename}.syn"
			if not self._merge_syns and os.path.exists(syn_file):
				runDictzip(syn_file)

	def fixDefi(self, defi: str, defiFormat: str) -> str:
		# for StarDict 3.0:
		if self._stardict_client and defiFormat == "h":
			defi = self._p_pattern.sub("\\2<br>", defi)
			# if there is </p> left without opening, replace with <br>
			defi = defi.replace("</p>", "<br>")
			defi = self._br_pattern.sub("<br>", defi)

		if self._audio_goldendict:
			if self._audio_icon:
				defi = self._re_audio_link.sub(
					r'<audio src="\3">\5</audio>',
					defi,
				)
			else:
				defi = self._re_audio_link.sub(
					r'<audio src="\3"></audio>',
					defi,
				)

		# FIXME:
		# defi = defi.replace(' src="./', ' src="./res/')
		return defi

	def newIdxList(self) -> T_SdList:
		if not self._sqlite:
			return MemSdList()
		return IdxSqList(join(self._glos.tmpDataDir, "stardict-idx.db"))

	def newSynList(self) -> T_SdList:
		if not self._sqlite:
			return MemSdList()
		return SynSqList(join(self._glos.tmpDataDir, "stardict-syn.db"))

	def dictMarkToBytesFunc(self) -> tuple[Callable, int]:
		if self._large_file:
			return uint64ToBytes, 0xFFFFFFFFFFFFFFFF

		return uint32ToBytes, 0xFFFFFFFF

	def writeCompact(self, defiFormat: str) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		defiFormat: format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompact: {defiFormat=}")
		dictMark = 0
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

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

			b_idxBlock = (
				word.encode("utf-8")
				+ b"\x00"
				+ dictMarkToBytes(dictMark)
				+ uint32ToBytes(blockLen)
			)
			idxFile.write(b_idxBlock)

			dictMark += blockLen
			wordCount += 1

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		dictFile.close()
		idxFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now() - t0:.2f} seconds")

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat=defiFormat,
		)

	def writeGeneral(self) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneral")
		dictMark = 0
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		t0 = now()
		wordCount = 0
		defiFormatCounter: "typing.Counter[str]" = Counter()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

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
			if defiFormat not in {"h", "m", "x"}:
				log.error(f"invalid {defiFormat=}, using 'm'")
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

			b_idxBlock = (
				word.encode("utf-8")
				+ b"\x00"
				+ dictMarkToBytes(dictMark)
				+ uint32ToBytes(blockLen)
			)
			idxFile.write(b_idxBlock)

			dictMark += blockLen
			wordCount += 1

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		dictFile.close()
		idxFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now() - t0:.2f} seconds")
		log.debug("defiFormatsCount = " + pformat(defiFormatCounter.most_common()))

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat="",
		)

	def writeSynFile(self, altIndexList: "T_SdList[tuple[bytes, int]]") -> None:
		"""Build .syn file."""
		if not altIndexList:
			return

		log.info(f"Sorting {len(altIndexList)} synonyms...")
		t0 = now()

		altIndexList.sort()
		# 28 seconds with old sort key (converted from custom cmp)
		# 0.63 seconds with my new sort key
		# 0.20 seconds without key function (default sort)

		log.info(
			f"Sorting {len(altIndexList)} synonyms took {now() - t0:.2f} seconds",
		)
		log.info(f"Writing {len(altIndexList)} synonyms...")
		t0 = now()
		with open(self._filename + ".syn", "wb") as synFile:
			synFile.write(
				b"".join(
					b_alt + b"\x00" + uint32ToBytes(entryIndex)
					for b_alt, entryIndex in altIndexList
				),
			)
		log.info(
			f"Writing {len(altIndexList)} synonyms took {now() - t0:.2f} seconds",
		)

	def writeCompactMergeSyns(
		self,
		defiFormat: str,
	) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		defiFormat - format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompactMergeSyns: {defiFormat=}")
		dictMark = 0

		idxBlockList = self.newIdxList()
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")

		t0 = now()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

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

			blockData = dictMarkToBytes(dictMark) + uint32ToBytes(blockLen)
			for word in words:
				idxBlockList.append((word.encode("utf-8"), blockData))

			dictMark += blockLen

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		wordCount = self.writeIdxFile(idxBlockList)

		dictFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now() - t0:.2f} seconds")

		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat=defiFormat,
		)

	def writeGeneralMergeSyns(self) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneralMergeSyns")
		dictMark = 0
		idxBlockList = self.newIdxList()
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")

		t0 = now()
		wordCount = 0
		defiFormatCounter: "typing.Counter[str]" = Counter()
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

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
			if defiFormat not in {"h", "m", "x"}:
				log.error(f"invalid {defiFormat=}, using 'm'")
				defiFormat = "m"

			words = entry.l_word  # list of strs
			word = words[0]  # str
			defi = self.fixDefi(entry.defi, defiFormat)
			# defi is str

			b_dictBlock = (defiFormat + defi).encode("utf-8") + b"\x00"
			dictFile.write(b_dictBlock)
			blockLen = len(b_dictBlock)

			blockData = dictMarkToBytes(dictMark) + uint32ToBytes(blockLen)
			for word in words:
				idxBlockList.append((word.encode("utf-8"), blockData))

			dictMark += blockLen

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		wordCount = self.writeIdxFile(idxBlockList)

		dictFile.close()
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
		log.info(f"Writing dict file took {now() - t0:.2f} seconds")
		log.debug("defiFormatsCount = " + pformat(defiFormatCounter.most_common()))

		self.writeIfoFile(
			wordCount,
			len(altIndexList),
			defiFormat="",
		)

	def writeIdxFile(self, indexList: "T_SdList[tuple[bytes, bytes]]") -> int:
		filename = self._filename + ".idx"
		if not indexList:
			return 0

		log.info(f"Sorting {len(indexList)} items...")
		t0 = now()

		indexList.sort()
		log.info(
			f"Sorting {len(indexList)} {filename} took {now() - t0:.2f} seconds",
		)
		log.info(f"Writing {len(indexList)} index entries...")
		t0 = now()
		with open(filename, mode="wb") as indexFile:
			indexFile.write(b"".join(key + b"\x00" + value for key, value in indexList))
		log.info(
			f"Writing {len(indexList)} {filename} took {now() - t0:.2f} seconds",
		)
		return len(indexList)

	def writeIfoFile(
		self,
		wordCount: int,
		synWordCount: int,
		defiFormat: str = "",
	) -> None:
		"""Build .ifo file."""
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

		ifo: "list[tuple[str, str]]" = [
			("version", "3.0.0"),
			("bookname", bookname),
			("wordcount", str(wordCount)),
			("idxfilesize", str(indexFileSize)),
		]
		if self._large_file:
			ifo.append(("idxoffsetbits", "64"))
		if defiFormat:
			ifo.append(("sametypesequence", defiFormat))
		if synWordCount > 0:
			ifo.append(("synwordcount", str(synWordCount)))

		desc = glos.getInfo("description")
		_copyright = glos.getInfo("copyright")
		if _copyright:
			desc = f"{_copyright}\n{desc}"
		publisher = glos.getInfo("publisher")
		if publisher:
			desc = f"Publisher: {publisher}\n{desc}"

		for key in infoKeys:
			if key in {
				"bookname",
				"description",
			}:
				continue
			value = glos.getInfo(key)
			if not value:
				continue
			value = newlinesToSpace(value)
			ifo.append((key, value))

		ifo.append(("description", newlinesToBr(desc)))

		ifoStr = "StarDict's dict ifo file\n"
		for key, value in ifo:
			ifoStr += f"{key}={value}\n"
		with open(
			self._filename + ".ifo",
			mode="w",
			encoding="utf-8",
			newline="\n",
		) as ifoFile:
			ifoFile.write(ifoStr)
