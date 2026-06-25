from __future__ import annotations

import os
import re
from dataclasses import dataclass
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
from time import perf_counter as now
from typing import TYPE_CHECKING, Literal

from pyglossary.core import log
from pyglossary.glossary_utils import Error
from pyglossary.plugins.stardict.memlist import MemSdList
from pyglossary.plugins.stardict.sqlist import IdxSqList, SynSqList
from pyglossary.text_utils import uint32ToBytes, uint64ToBytes

if TYPE_CHECKING:
	import io
	from collections.abc import Callable, Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType
	from pyglossary.langs import Lang
	from pyglossary.plugins.stardict.sd_types import T_SdList


__all__ = ["Writer"]

infoKeys = (
	"bookname",
	"author",
	"email",
	"website",
	"description",
	"date",
)


# _re_newline = re.compile("[\n\r]+")
_re_newline = re.compile("\n\r?|\r\n?")


def _newlinesToSpace(text: str) -> str:
	return _re_newline.sub(" ", text)


def _newlinesToBr(text: str) -> str:
	return _re_newline.sub("<br>", text)


@dataclass(slots=True)
class _PartFiles:
	dictFile: io.BufferedWriter
	idxFile: io.BufferedWriter
	altIndexList: T_SdList[tuple[bytes, int]]


@dataclass(slots=True)
class _MultipartState:
	partIndex: int = 0
	multiPart: bool = False
	dictMark: int = 0
	entryIndex: int = -1

	@property
	def entryCount(self) -> int:
		return self.entryIndex + 1

	def resetPart(self) -> None:
		self.dictMark = 0
		self.entryIndex = -1


class Writer:
	_large_file: bool = False
	_dictzip: bool = False
	_dictzip_syn: bool = False
	_sametypesequence: Literal["", "h", "m", "x", "-"] = ""
	_stardict_client: bool = False
	_audio_goldendict: bool = False
	_audio_icon: bool = True
	_autosqlite: bool = True
	_sqlite: bool = False
	_max_file_size: int = 0

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resDir = ""
		self._openMultipartFiles: list[io.BufferedWriter] = []
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

	_partFileExts = (
		"syn",
		"idx",
		"dict",
		"ifo",
		"idx.oft",
		"syn.oft",
		"dict.dz",
		"syn.dz",
	)

	def finish(self) -> None:
		self._filename = ""
		self._resDir = ""
		self._sourceLang = None
		self._targetLang = None
		self._openMultipartFiles = []

	def partBasePath(self, partIndex: int) -> str:
		if partIndex <= 0:
			return self._filename
		return f"{self._filename}.{partIndex}"

	def _removeAllPartFiles(self) -> None:
		partIndex = 0
		while True:
			base = self.partBasePath(partIndex)
			found = False
			for ext in self._partFileExts:
				fpath = f"{base}.{ext}"
				if isfile(fpath):
					log.info(f"removing file {fpath}")
					os.remove(fpath)
					found = True
			if not found and partIndex > 0:
				break
			partIndex += 1

	def open(self, filename: str) -> None:  # noqa: PLR0912
		if self._autosqlite:
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
			if self._sametypesequence == "-":
				self._sametypesequence = ""
		else:
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
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		self._removeAllPartFiles()

		if self._sametypesequence:
			yield from self.writeCompact(self._sametypesequence)
		else:
			yield from self.writeGeneral()

		try:
			os.rmdir(self._resDir)
		except OSError:
			pass  # "Directory not empty" or "Permission denied"

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

	def dictMarkToBytesFunc(self) -> Callable[[int], bytes]:
		if self._large_file:
			return uint64ToBytes

		return uint32ToBytes

	def dictMarkMax(self) -> int:
		offsetMax = 0xFFFFFFFFFFFFFFFF if self._large_file else 0xFFFFFFFF
		if self._max_file_size > 0:
			return min(self._max_file_size, offsetMax)
		return offsetMax

	def _checkDictBlockSize(self, blockSize: int, dictMarkMax: int) -> None:
		if blockSize > dictMarkMax:
			raise Error(
				f"StarDict: single entry definition is too big"
				f" ({blockSize} bytes > {dictMarkMax} bytes limit)",
			)

	def _needNewPart(
		self,
		dictMark: int,
		blockSize: int,
		dictMarkMax: int,
	) -> bool:
		return dictMark > 0 and dictMark + blockSize > dictMarkMax

	def _openPartFiles(
		self,
		partIndex: int,
	) -> _PartFiles:
		fileBasePath = self.partBasePath(partIndex)
		return _PartFiles(
			open(fileBasePath + ".dict", "wb"),
			open(fileBasePath + ".idx", "wb"),
			self.newSynList(),
		)

	def _finishPart(
		self,
		partState: _MultipartState,
		partFiles: _PartFiles,
	) -> None:
		from pyglossary.os_utils import runDictzip

		fileBasePath = self.partBasePath(partState.partIndex)
		partFiles.dictFile.close()
		partFiles.idxFile.close()

		self.writeSynFile(partFiles.altIndexList, fileBasePath)
		partNumber = partState.partIndex + 1 if partState.multiPart else None
		self.writeIfoFile(
			partState.entryCount,
			len(partFiles.altIndexList),
			fileBasePath,
			partNumber=partNumber,
		)

		if self._dictzip:
			runDictzip(f"{fileBasePath}.dict")
		syn_file = f"{fileBasePath}.syn"
		if self._dictzip_syn and isfile(syn_file):
			runDictzip(syn_file)

	def _closePartFiles(self) -> None:
		for partFile in self._openMultipartFiles:
			if not partFile.closed:
				partFile.close()
		self._openMultipartFiles = []

	def _writeMultipartMain(
		self,
		makeDictBlock: Callable[[EntryType], tuple[bytes, tuple[bytes, ...]]],
	) -> Generator[None, EntryType, None]:
		dictMarkToBytes = self.dictMarkToBytesFunc()
		dictMarkMax = self.dictMarkMax()

		partState = _MultipartState()
		partFiles = self._openPartFiles(partState.partIndex)
		self._openMultipartFiles[:] = [partFiles.dictFile, partFiles.idxFile]
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(self._resDir)
				continue

			b_dictBlock, b_terms = makeDictBlock(entry)
			blockSize = len(b_dictBlock)
			self._checkDictBlockSize(blockSize, dictMarkMax)

			if self._needNewPart(partState.dictMark, blockSize, dictMarkMax):
				partState.multiPart = True
				self._finishPart(partState, partFiles)
				partState.partIndex += 1
				log.info(f"Creating {self.partBasePath(partState.partIndex)}")
				partFiles = self._openPartFiles(partState.partIndex)
				self._openMultipartFiles[:] = [partFiles.dictFile, partFiles.idxFile]
				partState.resetPart()

			partState.entryIndex += 1

			for b_alt in b_terms[1:]:
				partFiles.altIndexList.append((b_alt, partState.entryIndex))

			partFiles.dictFile.write(b_dictBlock)

			partFiles.idxFile.write(
				b_terms[0]
				+ b"\x00"
				+ dictMarkToBytes(partState.dictMark)
				+ uint32ToBytes(blockSize)
			)

			partState.dictMark += blockSize

		self._finishPart(partState, partFiles)

	def _writeMultipart(
		self,
		makeDictBlock: Callable[[EntryType], tuple[bytes, tuple[bytes, ...]]],
	) -> Generator[None, EntryType, None]:
		try:
			yield from self._writeMultipartMain(makeDictBlock)
		finally:
			self._closePartFiles()

	def writeCompact(self, defiFormat: str) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		defiFormat: format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompact: {defiFormat=}")

		t0 = now()
		yield from self._writeMultipart(
			lambda entry: (
				self.fixDefi(entry.defi, defiFormat),
				entry.lb_term,
			),
		)
		log.info(f"Writing dict + idx file took {now() - t0:.2f} seconds")

	def writeGeneral(self) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneral")

		t0 = now()
		yield from self._writeMultipart(self._generalDictBlock)
		log.info(f"Writing dict + idx file took {now() - t0:.2f} seconds")

	def _generalDictBlock(
		self,
		entry: EntryType,
	) -> tuple[bytes, tuple[bytes, ...]]:
		defiFormat = entry.detectDefiFormat("m")  # call no more than once
		b_defi = self.fixDefi(entry.defi, defiFormat)
		return defiFormat.encode("ascii") + b_defi + b"\x00", entry.lb_term

	def writeSynFile(
		self,
		altIndexList: T_SdList[tuple[bytes, int]],
		fileBasePath: str | None = None,
	) -> None:
		"""Build .syn file."""
		if not altIndexList:
			return

		if fileBasePath is None:
			fileBasePath = self._filename

		log.info(f"Sorting {len(altIndexList)} synonyms...")
		t0 = now()

		altIndexList.sort()

		log.info(
			f"Sorting {len(altIndexList)} synonyms took {now() - t0:.2f} seconds",
		)
		log.info(f"Writing {len(altIndexList)} synonyms...")
		t0 = now()
		with open(fileBasePath + ".syn", "wb") as synFile:
			synFile.writelines(
				b_alt + b"\x00" + uint32ToBytes(entryIndex)
				for b_alt, entryIndex in altIndexList
			)
		log.info(
			f"Writing {len(altIndexList)} synonyms took {now() - t0:.2f} seconds",
		)

	def writeIdxFile(
		self,
		indexList: T_SdList[tuple[bytes, bytes]],
		fileBasePath: str | None = None,
	) -> None:
		if not indexList:
			return

		if fileBasePath is None:
			fileBasePath = self._filename

		log.info(f"Sorting idx with {len(indexList)} entries...")
		t0 = now()
		indexList.sort()
		log.info(
			f"Sorting idx with {len(indexList)} entries took {now() - t0:.2f} seconds",
		)

		log.info(f"Writing idx with {len(indexList)} entries...")
		t0 = now()
		with open(fileBasePath + ".idx", mode="wb") as indexFile:
			indexFile.writelines(key + b"\x00" + value for key, value in indexList)
		log.info(
			f"Writing idx with {len(indexList)} entries took {now() - t0:.2f} seconds",
		)

	def getBookname(self, partNumber: int | None = None) -> str:
		bookname = _newlinesToSpace(self._glos.getInfo("name"))
		sourceLang = self._sourceLang
		targetLang = self._targetLang
		if sourceLang and targetLang:
			langs = f"{sourceLang.code}-{targetLang.code}"
			if langs not in bookname.lower():
				bookname = f"{bookname} ({langs})"
		if partNumber is not None:
			bookname = f"{bookname} (part {partNumber})"
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
		return _newlinesToBr(desc)

	def writeIfoFile(
		self,
		entryCount: int,
		synWordCount: int,
		fileBasePath: str | None = None,
		partNumber: int | None = None,
	) -> None:
		"""Build .ifo file."""
		glos = self._glos
		defiFormat = self._sametypesequence
		if fileBasePath is None:
			fileBasePath = self._filename
		indexFileSize = getsize(fileBasePath + ".idx")

		ifoDict: dict[str, str] = {
			"version": "3.0.0",
			"bookname": self.getBookname(partNumber),
			"wordcount": str(entryCount),
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
			value = _newlinesToSpace(value)
			ifoDict[key] = value

		ifoDict["description"] = self.getDescription()

		with open(
			fileBasePath + ".ifo",
			mode="w",
			encoding="utf-8",
			newline="\n",
		) as ifoFile:
			ifoFile.write("StarDict's dict ifo file\n")
			ifoFile.writelines(f"{key}={value}\n" for key, value in ifoDict.items())
