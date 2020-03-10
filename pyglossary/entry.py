# -*- coding: utf-8 -*-
import re
from tempfile import mktemp
import os
from os.path import (
	join,
	exists,
	dirname,
)
from typing import (
	Optional,
	Tuple,
	List,
	Dict,
	Callable,
	Any,
)


from .entry_base import BaseEntry, MultiStr, RawEntryType
from .iter_utils import unique_everseen


class DataEntry(BaseEntry): # or Resource? FIXME
	def isData(self) -> bool:
		return True

	def __init__(self, fname: str, data: bytes, inTmp: bool = False) -> None:
		assert isinstance(fname, str)
		assert isinstance(data, bytes)
		assert isinstance(inTmp, bool)

		if inTmp:
			tmpPath = mktemp(prefix=fname + "_")
			with open(tmpPath, "wb") as toFile:
				toFile.write(data)
			data = ""
		else:
			tmpPath = None

		self._fname = fname
		self._data = data  # bytes instance
		self._tmpPath = tmpPath

	def getFileName(self) -> str:
		return self._fname

	def getData(self) -> bytes:
		if self._tmpPath:
			with open(self._tmpPath, "rb") as fromFile:
				return fromFile.read()
		else:
			return self._data

	def save(self, directory: str) -> str:
		fname = self._fname
		# fix filename depending on operating system? FIXME
		fpath = join(directory, fname)
		fdir = dirname(fpath)
		if not exists(fdir):
			os.makedirs(fdir)
		with open(fpath, "wb") as toFile:
			toFile.write(self.getData())
		return fpath

	def getWord(self) -> str:
		return self._fname

	def getWords(self) -> List[str]:
		return [self._fname]

	def getDefi(self) -> str:
		return "File: %s" % self._fname

	def getDefis(self) -> List[str]:
		return [self.getDefi()]

	def getDefiFormat(self) -> str:
		# TODO: type: Literal["b", "m"]
		return "b"

	def setDefiFormat(self, defiFormat):
		pass

	def detectDefiFormat(self) -> None:
		pass

	def addAlt(self, alt: str) -> None:
		pass

	def editFuncWord(self, func: Callable[[str], str]) -> None:
		pass
		# modify fname?
		# FIXME

	def editFuncDefi(self, func: Callable[[str], str]) -> None:
		pass

	def strip(self) -> None:
		pass

	def replaceInWord(self, source: str, target: str) -> None:
		pass

	def replaceInDefi(self, source: str, target: str) -> None:
		pass

	def replace(self, source: str, target: str) -> None:
		pass

	def removeEmptyAndDuplicateAltWords(self):
		pass

	def getRaw(self) -> RawEntryType:
		return (
			self._fname,
			"DATA",
		)


class Entry(BaseEntry):
	sep = "|"
	htmlPattern = re.compile(
		".*(" + "|".join([
			r"<br\s*/?\s*>",
			r"<p[ >]",
			r"<div[ >]",
			r"<span[ >]",
			r"<a href=",
			r"<sup[ >]",
		]) + ")",
		re.S,
	)

	def isData(self) -> bool:
		return False

	def _join(self, parts: List[str]) -> str:
		return self.sep.join([
			part.replace(self.sep, "\\" + self.sep)
			for part in parts
		])

	@staticmethod
	def getEntrySortKey(
		key: Optional[Callable[[str], Any]] = None,
	) -> Callable[[BaseEntry], Any]:
		if key:
			return lambda entry: key(entry.getWords()[0])
		else:
			return lambda entry: entry.getWords()[0]

	@staticmethod
	def getRawEntrySortKey(
		key: Optional[Callable[[str], Any]] = None,
	) -> Callable[[Tuple], str]:
		# here `x` is raw entity, meaning a tuple of form (word, defi) or
		# (word, defi, defiFormat)
		# so x[0] is word(s), that can be a str (one word),
		# or a list or tuple (one word with or more alternaties)
		# FIXME: drop the case that x[0] is tuple
		if key:
			return lambda x: key(
				x[0][0] if isinstance(x[0], (list, tuple)) else x[0]
			)
		else:
			return lambda x: \
				x[0][0] if isinstance(x[0], (list, tuple)) else x[0]

	def __init__(
		self,
		word: MultiStr,
		defi: MultiStr,
		defiFormat: str = "m",
		byteProgress: Optional[Tuple[int, int]] = None,
	) -> None:
		"""
			word: string or a list of strings (including alternate words)
			defi: string or a list of strings (including alternate definitions)
			defiFormat (optional): definition format:
				"m": plain text
				"h": html
				"x": xdxf
		"""

		# memory optimization:
		if isinstance(word, list):
			if len(word) == 1:
				word = word[0]
		elif not isinstance(word, str):
			raise TypeError("invalid word type %s" % type(word))

		if isinstance(defi, list):
			if len(defi) == 1:
				defi = defi[0]
		elif not isinstance(defi, str):
			raise TypeError("invalid defi type %s" % type(defi))

		if defiFormat not in ("m", "h", "x"):
			raise ValueError("invalid defiFormat %r" % defiFormat)

		self._word = word
		self._defi = defi
		self._defiFormat = defiFormat
		self._byteProgress = byteProgress  # Optional[Tuple[int, int]]

	def getWord(self) -> str:
		"""
			returns string of word,
				and all the alternate words
				seperated by "|"
		"""
		if isinstance(self._word, str):
			return self._word
		else:
			return self._join(self._word)

	def getWords(self) -> List[str]:
		"""
			returns list of the word and all the alternate words
		"""
		if isinstance(self._word, str):
			return [self._word]
		else:
			return self._word

	def getDefi(self) -> str:
		"""
			returns string of definition,
				and all the alternate definitions
				seperated by "|"
		"""
		if isinstance(self._defi, str):
			return self._defi
		else:
			return self._join(self._defi)

	def getDefis(self) -> List[str]:
		"""
			returns list of the definition and all the alternate definitions
		"""
		if isinstance(self._defi, str):
			return [self._defi]
		else:
			return self._defi

	def getDefiFormat(self) -> str:
		"""
			returns definition format:
				"m": plain text
				"h": html
				"x": xdxf
		"""
		# TODO: type: Literal["m", "h", "x"]
		return self._defiFormat

	def setDefiFormat(self, defiFormat) -> str:
		"""
			defiFormat:
				"m": plain text
				"h": html
				"x": xdxf
		"""
		self._defiFormat = defiFormat

	def detectDefiFormat(self) -> None:
		if self._defiFormat != "m":
			return
		defi = self.getDefi().lower()
		if re.match(self.htmlPattern, defi):
			self._defiFormat = "h"

	def byteProgress(self):
		return self._byteProgress

	def addAlt(self, alt: str) -> None:
		words = self.getWords()
		words.append(alt)
		self._word = words

	def editFuncWord(self, func: Callable[[str], str]) -> None:
		"""
			run function `func` on all the words
			`func` must accept only one string as argument
			and return the modified string
		"""
		if isinstance(self._word, str):
			self._word = func(self._word)
		else:
			self._word = tuple(
				func(st) for st in self._word
			)

	def editFuncDefi(self, func: Callable[[str], str]) -> None:
		"""
			run function `func` on all the definitions
			`func` must accept only one string as argument
			and return the modified string
		"""
		if isinstance(self._defi, str):
			self._defi = func(self._defi)
		else:
			self._defi = tuple(
				func(st) for st in self._defi
			)

	def strip(self) -> None:
		"""
			strip whitespaces from all words and definitions
		"""
		self.editFuncWord(str.strip)
		self.editFuncDefi(str.strip)

	def replaceInWord(self, source: str, target: str) -> None:
		"""
			replace string `source` with `target` in all words
		"""
		if isinstance(self._word, str):
			self._word = self._word.replace(source, target)
		else:
			self._word = tuple(
				st.replace(source, target) for st in self._word
			)

	def replaceInDefi(self, source: str, target: str) -> None:
		"""
			replace string `source` with `target` in all definitions
		"""
		if isinstance(self._defi, str):
			self._defi = self._defi.replace(source, target)
		else:
			self._defi = tuple(
				st.replace(source, target) for st in self._defi
			)

	def replace(self, source: str, target: str) -> None:
		"""
			replace string `source` with `target` in all words and definitions
		"""
		self.replaceInWord(source, target)
		self.replaceInDefi(source, target)

	def removeEmptyAndDuplicateAltWords(self):
		words = self.getWords()
		if len(words) == 1:
			return
		words = [word for word in words if word]
		words = list(unique_everseen(words))
		self._word = words

	def getRaw(self) -> RawEntryType:
		"""
			returns a tuple (word, defi) or (word, defi, defiFormat)
			where both word and defi might be string or list of strings
		"""
		if self._defiFormat:
			return (
				self._word,
				self._defi,
				self._defiFormat,
			)
		else:
			return (
				self._word,
				self._defi,
			)

	@classmethod
	def fromRaw(cls, rawEntry: RawEntryType, defaultDefiFormat: str = "m"):
		"""
			rawEntry can be (word, defi) or (word, defi, defiFormat)
			where both word and defi can be string or list of strings
			if defiFormat is missing, defaultDefiFormat will be used

			creates and return an Entry object from `rawEntry` tuple
		"""
		word = rawEntry[0]
		defi = rawEntry[1]
		if defi == "DATA":
			try:
				dataEntry = rawEntry[2] # DataEntry instance
			except IndexError:
				pass
			else:
				# if isinstance(dataEntry, DataEntry)  # FIXME
				return dataEntry
		try:
			defiFormat = rawEntry[2]
		except IndexError:
			defiFormat = defaultDefiFormat

		if isinstance(word, tuple):
			word = list(word)
		if isinstance(defi, tuple):
			defi = list(defi)

		return cls(
			word,
			defi,
			defiFormat=defiFormat,
		)
