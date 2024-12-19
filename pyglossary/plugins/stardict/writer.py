# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
from os.path import (
	dirname,
	getsize,
	isdir,
	join,
	realpath,
	split,
	splitext,
)
from time import perf_counter as now
from typing import (
	TYPE_CHECKING,
	Literal,
)

if TYPE_CHECKING:
	from collections.abc import Callable, Generator

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.langs import Lang
	from pyglossary.plugins.stardict.sd_types import T_SdList


from pyglossary.core import log
from pyglossary.glossary_utils import Error
from pyglossary.plugins.stardict.memlist import MemSdList
from pyglossary.plugins.stardict.sqlist import IdxSqList, SynSqList
from pyglossary.text_utils import uint32ToBytes, uint64ToBytes

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


class Writer:
	_large_file: bool = False
	_dictzip: bool = True
	_sametypesequence: Literal["", "h", "m", "x"] | None = ""
	_stardict_client: bool = False
	_audio_goldendict: bool = False
	_audio_icon: bool = True
	_sqlite: bool | None = None

	dictzipSynFile = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resDir = ""
		self._sourceLang: Lang | None = None
		self._targetLang: Lang | None = None
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
		if self._sqlite is None:
			self._sqlite = self._glos.sqlite
		log.debug(f"open: {filename = }, {self._sqlite = }")
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

		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		if self._sametypesequence:
			yield from self.writeCompact(self._sametypesequence)
		else:
			yield from self.writeGeneral()

		try:
			os.rmdir(self._resDir)
		except OSError:
			pass  # "Directory not empty" or "Permission denied"

		if self._dictzip:
			runDictzip(f"{self._filename}.dict")
			syn_file = f"{self._filename}.syn"
			if os.path.exists(syn_file) and self.dictzipSynFile:
				runDictzip(syn_file)

	def fixDefi(self, defi: str, defiFormat: str) -> bytes:
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
		return defi.encode("utf-8")

	def newIdxList(self) -> T_SdList[tuple[bytes, bytes]]:
		if not self._sqlite:
			return MemSdList()
		return IdxSqList(join(self._glos.tmpDataDir, "stardict-idx.db"))

	def newSynList(self) -> T_SdList[tuple[bytes, int]]:
		if not self._sqlite:
			return MemSdList()
		return SynSqList(join(self._glos.tmpDataDir, "stardict-syn.db"))

	def dictMarkToBytesFunc(self) -> tuple[Callable[[int], bytes], int]:
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
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

		t0 = now()

		dictMark, entryIndex = 0, -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			b_words = entry.lb_word

			for b_alt in b_words[1:]:
				altIndexList.append((b_alt, entryIndex))

			b_dictBlock = self.fixDefi(entry.defi, defiFormat)
			dictFile.write(b_dictBlock)

			idxFile.write(
				b_words[0]
				+ b"\x00"
				+ dictMarkToBytes(dictMark)
				+ uint32ToBytes(len(b_dictBlock))
			)

			dictMark += len(b_dictBlock)

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		dictFile.close()
		idxFile.close()
		log.info(f"Writing dict + idx file took {now() - t0:.2f} seconds")

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			entryIndex + 1,
			len(altIndexList),
		)

	def writeGeneral(self) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneral")
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")
		idxFile = open(self._filename + ".idx", "wb")

		t0 = now()
		dictMarkToBytes, dictMarkMax = self.dictMarkToBytesFunc()

		dictMark, entryIndex = 0, -1
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue
			entryIndex += 1

			defiFormat = entry.detectDefiFormat("m")  # call no more than once

			b_words = entry.lb_word

			for b_alt in b_words[1:]:
				altIndexList.append((b_alt, entryIndex))

			b_defi = self.fixDefi(entry.defi, defiFormat)
			b_dictBlock = defiFormat.encode("ascii") + b_defi + b"\x00"
			dictFile.write(b_dictBlock)

			idxFile.write(
				b_words[0]
				+ b"\x00"
				+ dictMarkToBytes(dictMark)
				+ uint32ToBytes(len(b_dictBlock))
			)

			dictMark += len(b_dictBlock)

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		dictFile.close()
		idxFile.close()
		log.info(f"Writing dict + idx file took {now() - t0:.2f} seconds")

		self.writeSynFile(altIndexList)
		self.writeIfoFile(
			entryIndex + 1,
			len(altIndexList),
		)

	def writeSynFile(self, altIndexList: T_SdList[tuple[bytes, int]]) -> None:
		"""Build .syn file."""
		if not altIndexList:
			return

		log.info(f"Sorting {len(altIndexList)} synonyms...")
		t0 = now()

		altIndexList.sort()

		log.info(
			f"Sorting {len(altIndexList)} synonyms took {now() - t0:.2f} seconds",
		)
		log.info(f"Writing {len(altIndexList)} synonyms...")
		t0 = now()
		with open(self._filename + ".syn", "wb") as synFile:
			for b_alt, entryIndex in altIndexList:
				synFile.write(b_alt + b"\x00" + uint32ToBytes(entryIndex))
		log.info(
			f"Writing {len(altIndexList)} synonyms took {now() - t0:.2f} seconds",
		)

	def writeIdxFile(self, indexList: T_SdList[tuple[bytes, bytes]]) -> None:
		if not indexList:
			return

		log.info(f"Sorting idx with {len(indexList)} entries...")
		t0 = now()
		indexList.sort()
		log.info(
			f"Sorting idx with {len(indexList)} entries took {now() - t0:.2f} seconds",
		)

		log.info(f"Writing idx with {len(indexList)} entries...")
		t0 = now()
		with open(self._filename + ".idx", mode="wb") as indexFile:
			for key, value in indexList:
				indexFile.write(key + b"\x00" + value)
		log.info(
			f"Writing idx with {len(indexList)} entries took {now() - t0:.2f} seconds",
		)

	def getBookname(self) -> str:
		bookname = newlinesToSpace(self._glos.getInfo("name"))
		sourceLang = self._sourceLang
		targetLang = self._targetLang
		if sourceLang and targetLang:
			langs = f"{sourceLang.code}-{targetLang.code}"
			if langs not in bookname.lower():
				bookname = f"{bookname} ({langs})"
			log.info(f"bookname: {bookname}")
		return bookname

	def getDescription(self) -> str:
		glos = self._glos
		desc = glos.getInfo("description")
		copyright_ = glos.getInfo("copyright")
		if copyright_:
			desc = f"{copyright_}\n{desc}"
		publisher = glos.getInfo("publisher")
		if publisher:
			desc = f"Publisher: {publisher}\n{desc}"
		return newlinesToBr(desc)

	def writeIfoFile(
		self,
		wordCount: int,
		synWordCount: int,
	) -> None:
		"""Build .ifo file."""
		glos = self._glos
		defiFormat = self._sametypesequence
		indexFileSize = getsize(self._filename + ".idx")

		ifoDict: dict[str, str] = {
			"version": "3.0.0",
			"bookname": self.getBookname(),
			"wordcount": str(wordCount),
			"idxfilesize": str(indexFileSize),
		}

		if self._large_file:
			ifoDict["idxoffsetbits"] = "64"
		if defiFormat:
			ifoDict["sametypesequence"] = defiFormat
		if synWordCount > 0:
			ifoDict["synwordcount"] = str(synWordCount)

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
			ifoDict[key] = value

		ifoDict["description"] = self.getDescription()

		with open(
			self._filename + ".ifo",
			mode="w",
			encoding="utf-8",
			newline="\n",
		) as ifoFile:
			ifoFile.write("StarDict's dict ifo file\n")
			for key, value in ifoDict.items():
				ifoFile.write(f"{key}={value}\n")
