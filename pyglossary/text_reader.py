from pyglossary.file_utils import fileCountLines
from pyglossary.entry_base import BaseEntry
from pyglossary.entry import Entry, DataEntry
from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.glossary_type import GlossaryType

import os
from os.path import isfile

import logging
log = logging.getLogger("pyglossary")

nextBlockResultType = """Optional[
	Tuple[
		str,
		str,
		Optional[List[Tuple[str, str]]]
	]
]"""


class TextFilePosWrapper(object):
	def __init__(self, fileobj, encoding):
		self.fileobj = fileobj
		self._encoding = encoding
		self.pos = 0

	def __iter__(self):
		return self

	def close(self):
		self.fileobj.close()

	def __next__(self):
		line = self.fileobj.__next__()
		self.pos += len(line.encode(self._encoding))
		return line

	def tell(self):
		return self.pos


class TextGlossaryReader(object):
	_encoding: str = "utf-8"

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType, hasInfo: bool = True):
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

	def readline(self):
		if self._bufferLine:
			line = self._bufferLine
			self._bufferLine = ""
			return line
		try:
			return next(self._file)
		except StopIteration:
			return ""

	def _open(self, filename: str) -> None:
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
			self.loadInfo()

	def open(self, filename: str) -> None:
		self._filename = filename
		self._open(filename)

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

	def newEntry(self, word, defi) -> "BaseEntry":
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

	def loadInfo(self) -> None:
		self._pendingEntries = []
		try:
			while True:
				block = self.nextBlock()
				if not block:
					continue
				key, value, _ = block
				origKey = key
				if isinstance(key, list):
					key = key[0]
				if not self.isInfoWords(key):
					self._pendingEntries.append(self.newEntry(origKey, value))
					break
				if not value:
					continue
				key = self.fixInfoWord(key)
				if not key:
					continue
				self.setInfo(key, value)
		except StopIteration:
			pass

		if self._fileIndex == 0:
			fileCountStr = self._glos.getInfo("file_count")
			if fileCountStr:
				self._fileCount = int(fileCountStr)
				self._glos.setInfo("file_count", "")

	def _genDataEntries(self, resList, resPathSet) -> "Iterator[DataEntry]":
		for relPath, fullPath in resList:
			if relPath in resPathSet:
				continue
			resPathSet.add(relPath)
			yield DataEntry(
				fname=relPath,
				tmpPath=fullPath,
			)

	def __iter__(self) -> "Iterator[BaseEntry]":
		resPathSet = set()
		while True:
			self._pos += 1
			if self._pendingEntries:
				yield self._pendingEntries.pop(0)
				continue
			###
			try:
				block = self.nextBlock()
			except StopIteration as e:
				if self._fileCount == -1 or self._fileIndex < self._fileCount - 1:
					if self.openNextFile():
						continue  # NESTED 5
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

	def isInfoWords(self, arg: "Union[str, List[str]]") -> bool:
		if isinstance(arg, str):
			return self.isInfoWord(arg)
		if isinstance(arg, list):
			return self.isInfoWord(arg[0])
		raise TypeError(f"bad argument {arg}")

	def fixInfoWord(self, word: str) -> bool:
		raise NotImplementedError

	def nextBlock(self) -> nextBlockResultType:
		raise NotImplementedError
