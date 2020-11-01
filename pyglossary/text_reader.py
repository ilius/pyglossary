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
	_encoding = "utf-8"

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
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			log.debug(f"File size of {filename}: {self._fileSize}")
			self._glos.setInfo("input_file_size", f"{self._fileSize}")

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

	def setInfo(self, word: str, defi: str) -> None:
		self._glos.setInfo(word, defi)

	def loadInfo(self) -> None:
		self._pendingEntries = []
		try:
			while True:
				wordDefi = self.nextPair()
				if not wordDefi:
					continue
				word, defi = wordDefi
				if not self.isInfoWords(word):
					self._pendingEntries.append(self.newEntry(word, defi))
					break
				if isinstance(word, list):
					word = [self.fixInfoWord(w) for w in word]
				else:
					word = self.fixInfoWord(word)
				if not word:
					continue
				if not defi:
					continue
				self.setInfo(word, defi)
		except StopIteration:
			pass

		if self._fileIndex == 0:
			fileCountStr = self._glos.getInfo("file_count")
			if fileCountStr:
				self._fileCount = int(fileCountStr)
				self._glos.setInfo("file_count", "")

	def __iter__(self) -> "Iterator[BaseEntry]":
		while True:
			self._pos += 1
			if self._pendingEntries:
				yield self._pendingEntries.pop(0)
				continue
			###
			try:
				wordDefi = self.nextPair()
			except StopIteration as e:
				if self._fileIndex < self._fileCount - 1:
					if self.openNextFile():
						continue
				self._wordCount = self._pos
				break
			if not wordDefi:
				yield None
			word, defi = wordDefi
			if isinstance(defi, tuple):
				defi, resList = defi
				for relPath, fullPath in resList:
					yield DataEntry.fromFile(self._glos, relPath, fullPath)
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

	def nextPair(self) -> "Tuple[str, str]":
		raise NotImplementedError
