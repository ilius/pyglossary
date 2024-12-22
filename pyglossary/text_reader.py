from __future__ import annotations

import io
import logging
import os
import typing
from os.path import isdir, isfile, join, splitext
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator

	from pyglossary.entry_base import MultiStr
	from pyglossary.glossary_types import EntryType, GlossaryType

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.entry import DataEntry
from pyglossary.io_utils import nullTextIO

__all__ = ["TextFilePosWrapper", "TextGlossaryReader", "nextBlockResultType"]

log = logging.getLogger("pyglossary")

nextBlockResultType: typing.TypeAlias = (
	"tuple[str | list[str], str, list[tuple[str, str]] | None] | None"
)
# (
# 	word: str | list[str],
# 	defi: str,
# 	images: list[tuple[str, str]] | None
# )


class TextFilePosWrapper(io.TextIOBase):
	def __init__(self, fileobj: io.TextIOBase, encoding: str) -> None:
		self.fileobj = fileobj
		self._encoding = encoding
		self.pos = 0

	def __iter__(self) -> Iterator[str]:  # type: ignore
		return self

	def close(self) -> None:
		self.fileobj.close()

	def __next__(self) -> str:  # type: ignore
		line = self.fileobj.__next__()
		self.pos += len(line.encode(self._encoding))
		return line

	def tell(self) -> int:
		return self.pos


class TextGlossaryReader:
	_encoding: str = "utf-8"

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType, hasInfo: bool = True) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._hasInfo = hasInfo
		self._pendingEntries: list[EntryType] = []
		self._wordCount = 0
		self._fileSize = 0
		self._progress = True
		self._pos = -1
		self._fileCount = 1
		self._fileIndex = -1
		self._bufferLine = ""
		self._resDir = ""
		self._resFileNames: list[str] = []

	def _setResDir(self, resDir: str) -> bool:
		if isdir(resDir):
			self._resDir = resDir
			self._resFileNames = os.listdir(self._resDir)
			return True
		return False

	def detectResDir(self, filename: str) -> bool:
		if self._setResDir(f"{filename}_res"):
			return True
		filenameNoExt, ext = splitext(filename)
		ext = ext.lstrip(".")
		if ext not in self.compressions:
			return False
		return self._setResDir(f"{filenameNoExt}_res")

	def readline(self) -> str:
		if self._bufferLine:
			line = self._bufferLine
			self._bufferLine = ""
			return line
		try:
			return next(self._file)
		except StopIteration:
			return ""

	def _openGen(self, filename: str) -> Iterator[tuple[int, int]]:
		self._fileIndex += 1
		log.info(f"Reading file: {filename}")
		cfile = cast(
			"io.TextIOBase",
			compressionOpen(
				filename,
				mode="rt",
				encoding=self._encoding,
			),
		)

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			log.debug(f"File size of {filename}: {self._fileSize}")
			self._glos.setInfo("input_file_size", str(self._fileSize))
		else:
			log.warning("TextGlossaryReader: file is not seekable")

		self._progress = self._glos.progressbar and self._fileSize > 0

		self._file = TextFilePosWrapper(cfile, self._encoding)
		if self._hasInfo:
			yield from self.loadInfo()

		self.detectResDir(filename)

	def _open(self, filename: str) -> None:
		for _ in self._openGen(filename):
			pass

	def open(self, filename: str) -> None:
		self._filename = filename
		self._open(filename)

	def openGen(self, filename: str) -> Iterator[tuple[int, int]]:
		"""
		Like open() but return a generator / iterator to track the progress
		example for reader.open:
		yield from TextGlossaryReader.openGen(self, filename).
		"""
		self._filename = filename
		yield from self._openGen(filename)

	def openNextFile(self) -> bool:
		self.close()
		nextFilename = f"{self._filename}.{self._fileIndex + 1}"
		if isfile(nextFilename):
			self._open(nextFilename)
			return True
		for ext in self.compressions:
			if isfile(f"{nextFilename}.{ext}"):
				self._open(f"{nextFilename}.{ext}")
				return True
		if self._fileCount != -1:
			log.warning(f"next file not found: {nextFilename}")
		return False

	def close(self) -> None:
		try:
			self._file.close()
		except Exception:
			log.exception(f"error while closing file {self._filename!r}")
		self._file = nullTextIO

	def newEntry(self, word: MultiStr, defi: str) -> EntryType:
		byteProgress: tuple[int, int] | None = None
		if self._progress:
			byteProgress = (self._file.tell(), self._fileSize)
		return self._glos.newEntry(
			word,
			defi,
			byteProgress=byteProgress,
		)

	def setInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, value)

	def _loadNextInfo(self) -> bool:
		"""Returns True when reached the end."""
		block = self.nextBlock()
		if not block:
			return False
		key, value, _ = block
		origKey = key
		if isinstance(key, list):
			key = key[0]
		if not self.isInfoWords(key):
			self._pendingEntries.append(self.newEntry(origKey, value))
			return True
		if not value:
			return False
		key = self.fixInfoWord(key)
		if not key:
			return False
		self.setInfo(key, value)
		return False

	def loadInfo(self) -> Generator[tuple[int, int], None, None]:
		self._pendingEntries = []
		try:
			while True:
				if self._loadNextInfo():
					break
				yield (self._file.tell(), self._fileSize)
		except StopIteration:
			pass

		if self._fileIndex == 0:
			fileCountStr = self._glos.getInfo("file_count")
			if fileCountStr:
				self._fileCount = int(fileCountStr)
				self._glos.setInfo("file_count", "")

	@staticmethod
	def _genDataEntries(
		resList: list[tuple[str, str]],
		resPathSet: set[str],
	) -> Iterator[DataEntry]:
		for relPath, fullPath in resList:
			if relPath in resPathSet:
				continue
			resPathSet.add(relPath)
			yield DataEntry(
				fname=relPath,
				tmpPath=fullPath,
			)

	def __iter__(self) -> Iterator[EntryType | None]:
		resPathSet: set[str] = set()
		while True:
			self._pos += 1
			if self._pendingEntries:
				yield self._pendingEntries.pop(0)
				continue
			###
			try:
				block = self.nextBlock()
			except StopIteration:
				if self._fileCount == -1 or (
					self._fileIndex < self._fileCount - 1 and self.openNextFile()
				):
					continue
				self._wordCount = self._pos
				break
			if not block:
				yield None
				continue
			word, defi, resList = block

			if resList:
				yield from self._genDataEntries(resList, resPathSet)

			yield self.newEntry(word, defi)

		resDir = self._resDir
		for fname in self._resFileNames:
			fpath = join(resDir, fname)
			if not isfile(fpath):
				log.error(f"No such file: {fpath}")
				continue
			with open(fpath, "rb") as _file:
				yield self._glos.newDataEntry(
					fname,
					_file.read(),
				)

	def __len__(self) -> int:
		return self._wordCount

	@classmethod
	def isInfoWord(cls, word: str) -> bool:
		raise NotImplementedError

	def isInfoWords(self, arg: str | list[str]) -> bool:
		if isinstance(arg, str):
			return self.isInfoWord(arg)
		if isinstance(arg, list):
			return self.isInfoWord(arg[0])
		raise TypeError(f"bad argument {arg}")

	@classmethod
	def fixInfoWord(cls, word: str) -> str:
		raise NotImplementedError

	def nextBlock(self) -> nextBlockResultType:
		raise NotImplementedError
