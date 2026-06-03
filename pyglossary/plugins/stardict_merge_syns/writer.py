# -*- coding: utf-8 -*-
from __future__ import annotations

from time import perf_counter as now
from typing import TYPE_CHECKING, BinaryIO

from pyglossary.core import log
from pyglossary.plugins.stardict import Writer as StdWriter
from pyglossary.text_utils import uint32ToBytes

if TYPE_CHECKING:
	from collections.abc import Callable, Generator

	from pyglossary.glossary_types import EntryType
	from pyglossary.plugins.stardict.sd_types import T_SdList


__all__ = ["Writer"]


class Writer(StdWriter):
	dictzipSynFile = False

	def fixDefi(self, defi: str, defiFormat: str) -> bytes:  # noqa: ARG002, PLR6301
		return defi.encode("utf-8")

	def _finishMergeSynsPart(
		self,
		dictFile: BinaryIO,
		idxBlockList: T_SdList[tuple[bytes, bytes]],
		fileBasePath: str,
		partNumber: int | None,
	) -> None:
		from pyglossary.os_utils import runDictzip

		if not dictFile.closed:
			dictFile.close()
		self._openMultipartFiles.clear()
		self.writeIdxFile(idxBlockList, fileBasePath)
		self.writeIfoFile(len(idxBlockList), 0, fileBasePath, partNumber=partNumber)
		if self._dictzip:
			runDictzip(f"{fileBasePath}.dict")

	def _writeMultipartMergeSyns(
		self,
		makeDictBlock: Callable[[EntryType], bytes],
	) -> Generator[None, EntryType, None]:
		dictMarkToBytes = self.dictMarkToBytesFunc()
		dictMarkMax = self.dictMarkMax()

		partIndex = 0
		multiPart = False
		fileBasePath = self.partBasePath(partIndex)
		dictFile = open(fileBasePath + ".dict", "wb")
		self._openMultipartFiles[:] = [dictFile]
		idxBlockList = self.newIdxList()
		dictMark = 0

		try:
			while True:
				entry = yield
				if entry is None:
					break
				if entry.isData():
					entry.save(self._resDir)
					continue

				b_dictBlock = makeDictBlock(entry)
				blockSize = len(b_dictBlock)
				self._checkDictBlockSize(blockSize, dictMarkMax)

				if self._needNewPart(dictMark, blockSize, dictMarkMax):
					multiPart = True
					self._finishMergeSynsPart(
						dictFile,
						idxBlockList,
						fileBasePath,
						partNumber=partIndex + 1,
					)
					partIndex += 1
					log.info(f"Creating {self.partBasePath(partIndex)}")
					fileBasePath = self.partBasePath(partIndex)
					dictFile = open(fileBasePath + ".dict", "wb")
					self._openMultipartFiles[:] = [dictFile]
					idxBlockList = self.newIdxList()
					dictMark = 0

				b_idxBlock = dictMarkToBytes(dictMark) + uint32ToBytes(blockSize)
				for b_term in entry.lb_term:
					idxBlockList.append((b_term, b_idxBlock))

				dictFile.write(b_dictBlock)
				dictMark += blockSize

			self._finishMergeSynsPart(
				dictFile,
				idxBlockList,
				fileBasePath,
				partNumber=partIndex + 1 if multiPart else None,
			)
		finally:
			self._closePartFiles()

	def writeCompact(
		self,
		defiFormat: str,
	) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary with sametypesequence option specified.
		Every item definition consists of a single article.
		All articles have the same format, specified in defiFormat parameter.

		defiFormat - format of article definition: h - html, m - plain text
		"""
		log.debug(f"writeCompact: {defiFormat=}")

		t0 = now()
		yield from self._writeMultipartMergeSyns(
			lambda entry: self.fixDefi(entry.defi, defiFormat),
		)
		log.info(f"Writing dict + idx file took {now() - t0:.2f} seconds")

	def writeGeneral(self) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneral")

		def makeDictBlock(entry: EntryType) -> bytes:
			defiFormat = entry.detectDefiFormat("m")  # call no more than once
			b_defi = self.fixDefi(entry.defi, defiFormat)
			return defiFormat.encode("ascii") + b_defi + b"\x00"

		t0 = now()
		yield from self._writeMultipartMergeSyns(makeDictBlock)
		log.info(f"Writing dict + idx file took {now() - t0:.2f} seconds")

	# TODO: override getDescription to indicate merge_syns
