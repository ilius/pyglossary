# -*- coding: utf-8 -*-
import re
import shutil
import os
from os.path import (
	join,
	exists,
	dirname,
	getsize,
)

from .entry_base import BaseEntry, MultiStr, RawEntryType
from .iter_utils import unique_everseen
from .text_utils import (
	joinByBar,
	splitByBar,
	splitByBarBytes,
)

from pickle import dumps, loads
from zlib import compress, decompress

import logging
log = logging.getLogger("pyglossary")


# aka Resource
class DataEntry(BaseEntry):
	__slots__ = [
		"_fname",
		"_data",
		"_tmpPath",
		"_byteProgress",
	]

	def isData(self) -> bool:
		return True

	def __init__(
		self,
		fname: str,
		data: bytes,
		tmpPath: "Optional[str]" = None,
		byteProgress: "Optional[Tuple[int, int]]" = None,
	) -> None:
		assert isinstance(fname, str)
		assert isinstance(data, bytes)

		if tmpPath:
			with open(tmpPath, "wb") as toFile:
				toFile.write(data)
			data = b""

		self._fname = fname
		self._data = data  # bytes instance
		self._tmpPath = tmpPath
		self._byteProgress = byteProgress  # Optional[Tuple[int, int]]

	def getFileName(self) -> str:
		return self._fname

	@property
	def data(self) -> bytes:
		if self._tmpPath:
			with open(self._tmpPath, "rb") as fromFile:
				return fromFile.read()
		else:
			return self._data

	def size(self):
		if self._tmpPath:
			return getsize(self._tmpPath)
		else:
			return len(self._data)

	def save(self, directory: str) -> str:
		fname = self._fname
		# fix filename depending on operating system? FIXME
		fpath = join(directory, fname)
		fdir = dirname(fpath)
		try:
			os.makedirs(fdir, mode=0o755, exist_ok=True)
			if self._tmpPath:
				shutil.move(self._tmpPath, fpath)
				self._tmpPath = fpath
			else:
				with open(fpath, "wb") as toFile:
					toFile.write(self._data)
		except Exception:
			log.exception(f"error while saving {fpath}")
			return ""
		return fpath

	@property
	def s_word(self) -> str:
		return self._fname

	@property
	def l_word(self) -> "List[str]":
		return [self._fname]

	@property
	def defi(self) -> str:
		return f"File: {self._fname}"

	def byteProgress(self):
		return self._byteProgress

	@property
	def defiFormat(self) -> 'Literal["b"]':
		return "b"

	@defiFormat.setter
	def defiFormat(self, defiFormat: str) -> None:
		pass

	def detectDefiFormat(self) -> None:
		pass

	def addAlt(self, alt: str) -> None:
		pass

	def editFuncWord(self, func: "Callable[[str], str]") -> None:
		pass
		# modify fname?
		# FIXME

	def editFuncDefi(self, func: "Callable[[str], str]") -> None:
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

	def getRaw(self, glos: "GlossaryType") -> "RawEntryType":
		b_fpath = b""
		if glos.tmpDataDir:
			b_fpath = self.save(glos.tmpDataDir).encode("utf-8")
		tpl = (
			self._fname.encode("utf-8"),
			b_fpath,
			"b",
		)
		if glos._rawEntryCompress:
			return compress(dumps(tpl), level=9)
		return tpl

	@classmethod
	def fromFile(cls, glos, relPath, fullPath):
		entry = DataEntry(relPath, b"")
		entry._tmpPath = fullPath
		return entry


class Entry(BaseEntry):
	xdxfPattern = re.compile("^<k>[^<>]*</k>", re.S | re.I)
	htmlPattern = re.compile(
		".*(?:" + "|".join([
			r"<font[ >]",
			r"<br\s*/?\s*>",
			r"<i[ >]",
			r"<b[ >]",
			r"<p[ >]",
			r"<hr\s*/?\s*>",
			r"<a ",  # or r"<a [^<>]*href="
			r"<div[ >]",
			r"<span[ >]",
			r"<img[ >]",
			r"<table[ >]",
			r"<sup[ >]",
			r"<u[ >]",
			r"<ul[ >]",
			r"<ol[ >]",
			r"<li[ >]",
			r"<h[1-6][ >]",
		]) + "|&[a-z]{2,8};|&#x?[0-9]{2,5};)",
		re.S | re.I,
	)

	__slots__ = [
		"_word",
		"_defi",
		"_defiFormat",
		"_byteProgress",
	]

	def isData(self) -> bool:
		return False

	@staticmethod
	def defaultStringSortKey(word: str) -> "Any":
		return Entry.defaultSortKey(word.encode("utf-8"))

	@staticmethod
	def defaultSortKey(b_word: bytes) -> "Any":
		return b_word.lower()

	@staticmethod
	def getEntrySortKey(
		key: "Optional[Callable[[bytes], Any]]" = None,
	) -> "Callable[[BaseEntry], Any]":
		if key is None:
			key = Entry.defaultSortKey
		return lambda entry: key(entry.l_word[0].encode("utf-8"))

	@staticmethod
	def getRawEntrySortKey(
		glos: "GlossaryType",
		key: "Optional[Callable[[bytes], Any]]" = None,
	) -> "Callable[[Tuple], Any]":
		# here `x` is raw entity, meaning a tuple of form (word, defi) or
		# (word, defi, defiFormat)
		# so x[0] is word(s) in bytes, that can be a str (one word),
		# or a list or tuple (one word with or more alternaties)
		if key is None:
			key = Entry.defaultSortKey

		if glos.getConfig("enable_alts", True):
			if glos._rawEntryCompress:
				return lambda x: key(splitByBarBytes(loads(decompress(x))[0])[0])
			else:
				return lambda x: key(splitByBarBytes(x[0])[0])
		else:
			if glos._rawEntryCompress:
				return lambda x: key(loads(decompress(x))[0])
			else:
				return lambda x: key(x[0])

	def __init__(
		self,
		word: MultiStr,
		defi: MultiStr,
		defiFormat: str = "m",
		byteProgress: "Optional[Tuple[int, int]]" = None,
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
			raise TypeError(f"invalid word type {type(word)}")

		if isinstance(defi, list):
			if len(defi) == 1:
				defi = defi[0]
		elif not isinstance(defi, str):
			raise TypeError(f"invalid defi type {type(defi)}")

		if defiFormat not in ("m", "h", "x"):
			raise ValueError(f"invalid defiFormat {defiFormat!r}")

		self._word = word
		self._defi = defi
		self._defiFormat = defiFormat
		self._byteProgress = byteProgress  # Optional[Tuple[int, int]]

	def __repr__(self):
		return (
			f"Entry({self._word!r}, {self._defi!r}, "
			f"defiFormat={self._defiFormat!r})"
		)

	@property
	def s_word(self):
		"""
			returns string of word,
				and all the alternate words
				seperated by "|"
		"""
		if isinstance(self._word, str):
			return self._word
		else:
			return joinByBar(self._word)

	@property
	def l_word(self) -> "List[str]":
		"""
			returns list of the word and all the alternate words
		"""
		if isinstance(self._word, str):
			return [self._word]
		else:
			return self._word

	@property
	def defi(self) -> str:
		"""
			returns string of definition
		"""
		return self._defi

	@property
	def defiFormat(self) -> str:
		"""
			returns definition format:
				"m": plain text
				"h": html
				"x": xdxf
		"""
		# TODO: type: Literal["m", "h", "x"]
		return self._defiFormat

	@defiFormat.setter
	def defiFormat(self, defiFormat: str) -> None:
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
		if Entry.xdxfPattern.match(self.defi):
			self._defiFormat = "x"
			return
		if Entry.htmlPattern.match(self.defi):
			self._defiFormat = "h"
			return

	def byteProgress(self):
		return self._byteProgress

	def addAlt(self, alt: str) -> None:
		l_word = self.l_word
		l_word.append(alt)
		self._word = l_word

	def editFuncWord(self, func: "Callable[[str], str]") -> None:
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

	def editFuncDefi(self, func: "Callable[[str], str]") -> None:
		"""
			run function `func` on all the definitions
			`func` must accept only one string as argument
			and return the modified string
		"""
		self._defi = func(self._defi)

	def _stripTrailingBR(self, s: str) -> str:
		while s.endswith('<BR>') or s.endswith('<br>'):
			s = s[:-4]
		return s

	def strip(self) -> None:
		"""
			strip whitespaces from all words and definitions
		"""
		self.editFuncWord(str.strip)
		self.editFuncDefi(str.strip)
		self.editFuncDefi(self._stripTrailingBR)

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
		self._defi = self._defi.replace(source, target)

	def replace(self, source: str, target: str) -> None:
		"""
			replace string `source` with `target` in all words and definitions
		"""
		self.replaceInWord(source, target)
		self.replaceInDefi(source, target)

	def removeEmptyAndDuplicateAltWords(self):
		l_word = self.l_word
		if len(l_word) == 1:
			return
		l_word = [word for word in l_word if word]
		l_word = list(unique_everseen(l_word))
		self._word = l_word

	def stripFullHtml(self) -> None:
		defi = self._defi
		if not defi.startswith('<'):
			return
		if defi.startswith('<!DOCTYPE html>'):
			defi = defi[len('<!DOCTYPE html>'):].strip()
			if not defi.startswith('<html'):
				log.error(f"<html> not found: word={self.s_word}")
				log.error(f"defi={defi[:100]}...")
		else:
			if not defi.startswith('<html>'):
				return
		word = self.s_word
		i = defi.find('<body')
		if i == -1:
			log.warning(f"<body not found: word={word}")
			return
		defi = defi[i + 5:]
		i = defi.find('>')
		if i == -1:
			log.error(f"'>' after <body not found: word={word}")
			return
		defi = defi[i + 1:]
		i = defi.find('</body')
		if i == -1:
			log.error(f"</body close not found: word={word}")
			return
		defi = defi[:i]
		self._defi = defi

	def getRaw(
		self,
		glos: "GlossaryType",
	) -> RawEntryType:
		"""
			returns a tuple (word, defi) or (word, defi, defiFormat)
			where both word and defi might be string or list of strings
		"""
		if self._defiFormat and self._defiFormat != glos.getDefaultDefiFormat():
			tpl = (
				self.b_word,
				self.b_defi,
				self._defiFormat,
			)
		else:
			tpl = (
				self.b_word,
				self.b_defi,
			)

		if glos._rawEntryCompress:
			return compress(dumps(tpl), level=9)

		return tpl

	@classmethod
	def fromRaw(
		cls,
		glos: "GlossaryType",
		rawEntry: RawEntryType,
		defaultDefiFormat: str = "m",
	):
		"""
			rawEntry can be (word, defi) or (word, defi, defiFormat)
			where both word and defi can be string or list of strings
			if defiFormat is missing, defaultDefiFormat will be used

			creates and return an Entry object from `rawEntry` tuple
		"""
		if isinstance(rawEntry, bytes):
			rawEntry = loads(decompress(rawEntry))
		word = rawEntry[0].decode("utf-8")
		defi = rawEntry[1].decode("utf-8")
		if len(rawEntry) > 2:
			defiFormat = rawEntry[2]
			if defiFormat == "b":
				return DataEntry.fromFile(glos, word, defi)
		else:
			defiFormat = defaultDefiFormat

		if glos.getConfig("enable_alts", True):
			word = splitByBar(word)

		return cls(
			word,
			defi,
			defiFormat=defiFormat,
		)
