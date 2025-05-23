# -*- coding: utf-8 -*-
from __future__ import annotations

from time import perf_counter as now
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.glossary_utils import Error
from pyglossary.plugins.stardict import Writer as StdWriter
from pyglossary.text_utils import uint32ToBytes

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType


__all__ = ["Writer"]


class Writer(StdWriter):
	dictzipSynFile = False

	def fixDefi(self, defi: str, defiFormat: str) -> bytes:  # noqa: ARG002, PLR6301
		return defi.encode("utf-8")

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

		idxBlockList = self.newIdxList()
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")

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

			b_dictBlock = self.fixDefi(entry.defi, defiFormat)
			dictFile.write(b_dictBlock)

			b_idxBlock = dictMarkToBytes(dictMark) + uint32ToBytes(len(b_dictBlock))
			for b_word in entry.lb_word:
				idxBlockList.append((b_word, b_idxBlock))

			dictMark += len(b_dictBlock)

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		dictFile.close()
		log.info(f"Writing dict file took {now() - t0:.2f} seconds")

		self.writeIdxFile(idxBlockList)

		self.writeIfoFile(
			len(idxBlockList),
			len(altIndexList),
		)

	def writeGeneral(self) -> Generator[None, EntryType, None]:
		"""
		Build StarDict dictionary in general case.
		Every item definition may consist of an arbitrary number of articles.
		sametypesequence option is not used.
		"""
		log.debug("writeGeneral")
		idxBlockList = self.newIdxList()
		altIndexList = self.newSynList()

		dictFile = open(self._filename + ".dict", "wb")

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

			b_defi = self.fixDefi(entry.defi, defiFormat)
			b_dictBlock = defiFormat.encode("ascii") + b_defi + b"\x00"
			dictFile.write(b_dictBlock)

			b_idxBlock = dictMarkToBytes(dictMark) + uint32ToBytes(len(b_dictBlock))
			for b_word in entry.lb_word:
				idxBlockList.append((b_word, b_idxBlock))

			dictMark += len(b_dictBlock)

			if dictMark > dictMarkMax:
				raise Error(
					f"StarDict: {dictMark = } is too big, set option large_file=true",
				)

		dictFile.close()
		log.info(f"Writing dict file took {now() - t0:.2f} seconds")

		self.writeIdxFile(idxBlockList)

		self.writeIfoFile(
			len(idxBlockList),
			len(altIndexList),
		)

	# TODO: override getDescription to indicate merge_syns
