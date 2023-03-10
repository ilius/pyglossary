import logging
from os.path import isfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import io
	from typing import Generator, Iterator, Union

	from pyglossary.glossary_type import EntryType, GlossaryType

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.entry import DataEntry

log = logging.getLogger("pyglossary")

resListType = "list[tuple[str, str]] | None"

nextBlockResultType = f"tuple[str, str, {resListType}] | None"


class TextFilePosWrapper(object):
	def __init__(self, fileobj: "io.TextIOBase", encoding: str) -> None:
		self.fileobj = fileobj
		self._encoding = encoding
		self.pos = 0

	def __iter__(self) -> "Iterator[str]":
		return self

	def close(self) -> None:
		self.fileobj.close()

	def __next__(self) -> str:
		line = self.fileobj.__next__()
		self.pos += len(line.encode(self._encoding))
		return line

	def tell(self) -> int:
		return self.pos


class TextGlossaryReader(object):
	_encoding: str = "utf-8"

	compressions = stdCompressions

	def __init__(self, glos: "GlossaryType", hasInfo: bool = True) -> None:
		self._glos = glos
		self._filename = ""
		self._file = None
		self._hasInfo = hasInfo
		self._pendingEntries = []
		self._wordCount = 0
		self._fileSize = 0
		self._pos = -1
		self._fileCount = 1
		self._fileIndex = -1
		self._bufferLine = ""

	def readline(self) -> str:
		if self._bufferLine:
			line = self._bufferLine
			self._bufferLine = ""
			return line
		try:
			return next(self._file)
		except StopIteration:
			return ""

	def _openGen(self, filename: str) -> "Iterator[tuple[int, int]]":
		self._fileIndex += 1
		log.info(f"Reading file: {filename}")
		cfile = compressionOpen(filename, mode="rt", encoding=self._encoding)

		if not self._wordCount:
			if cfile.seekable():
				cfile.seek(0, 2)
				self._fileSize = cfile.tell()
				cfile.seek(0)
				log.debug(f"File size of {filename}: {self._fileSize}")
				self._glos.setInfo("input_file_size", f"{self._fileSize}")
			else:
				log.warning("TextGlossaryReader: file is not seekable")

		self._file = TextFilePosWrapper(cfile, self._encoding)
		if self._hasInfo:
			yield from self.loadInfo()

	def _open(self, filename: str) -> None:
		for _ in self._openGen(filename):
			pass

	def open(self, filename: str) -> None:
		self._filename = filename
		self._open(filename)

	def openGen(self, filename: str) -> "Iterator[tuple[int, int]]":
		"""
			like open() but return a generator / iterator to track the progress
			example for reader.open:
				yield from TextGlossaryReader.openGen(self, filename)
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
		if not self._file:
			return
		try:
			self._file.close()
		except Exception:
			log.exception(f"error while closing file {self._filename!r}")
		self._file = None

	def newEntry(self, word: str, defi: str) -> "EntryType":
		byteProgress = None
		if self._fileSize:
			byteProgress = (self._file.tell(), self._fileSize)
		return self._glos.newEntry(
			word,
			defi,
			byteProgress=byteProgress,
		)

	def setInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, value)

	def _loadNextInfo(self) -> bool:
		"""
			returns True when reached the end
		"""
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

	def loadInfo(self) -> "Generator[tuple[int, int], None, None]":
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

	def _genDataEntries(
		self,
		resList: "list[tuple[str, str]]",
		resPathSet: "set[str]",
	) -> "Iterator[DataEntry]":
		for relPath, fullPath in resList:
			if relPath in resPathSet:
				continue
			resPathSet.add(relPath)
			yield DataEntry(
				fname=relPath,
				tmpPath=fullPath,
			)

	def __iter__(self) -> "Iterator[EntryType]":
		resPathSet = set()
		while True:
			self._pos += 1
			if self._pendingEntries:
				yield self._pendingEntries.pop(0)
				continue
			###
			try:
				block = self.nextBlock()
			except StopIteration:
				if (
					self._fileCount == -1 or self._fileIndex < self._fileCount - 1
					and self.openNextFile()
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

	def __len__(self) -> int:
		return self._wordCount

	def isInfoWord(self, word: str) -> bool:
		raise NotImplementedError

	def isInfoWords(self, arg: "Union[str, list[str]]") -> bool:
		if isinstance(arg, str):
			return self.isInfoWord(arg)
		if isinstance(arg, list):
			return self.isInfoWord(arg[0])
		raise TypeError(f"bad argument {arg}")

	def fixInfoWord(self, word: str) -> bool:
		raise NotImplementedError

	def nextBlock(self) -> nextBlockResultType:
		raise NotImplementedError
