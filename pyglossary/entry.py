# -*- coding: utf-8 -*-
import logging
import os
import re
import shutil
from os.path import (
	dirname,
	getsize,
	join,
)
from pickle import loads as pickle_loads
from typing import TYPE_CHECKING
from zlib import decompress as zlib_decompress

from .entry_base import BaseEntry, MultiStr
from .iter_utils import unique_everseen
from .text_utils import joinByBar

if TYPE_CHECKING:
	from typing import (
		Any,
		Callable,
	)

	from .glossary_types import RawEntryType


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
		data: bytes = b"",
		tmpPath: "str | None" = None,
		byteProgress: "tuple[int, int] | None" = None,
	) -> None:
		if data and tmpPath:
			with open(tmpPath, "wb") as toFile:
				toFile.write(data)
			data = b""

		self._fname = fname
		self._data = data  # bytes instance
		self._tmpPath = tmpPath
		self._byteProgress = byteProgress  # tuple[int, int] | None

	def getFileName(self) -> str:
		return self._fname

	@property
	def data(self) -> bytes:
		if self._tmpPath:
			with open(self._tmpPath, "rb") as _file:
				return _file.read()
		else:
			return self._data

	def size(self) -> int:
		if self._tmpPath:
			return getsize(self._tmpPath)
		return len(self._data)

	def save(self, directory: str) -> str:
		fname = self._fname
		fpath = join(directory, fname)
		fdir = dirname(fpath)
		try:
			os.makedirs(fdir, mode=0o755, exist_ok=True)
			if self._tmpPath:
				shutil.move(self._tmpPath, fpath)
				self._tmpPath = fpath
			else:
				with open(fpath, "wb") as toFile:
					toFile.write(self._data)  # NESTED 4
		except FileNotFoundError as e:
			log.error(f"error in DataEntry.save: {e}")
		except Exception:
			log.exception(f"error while saving {fpath}")
			return ""
		return fpath

	@property
	def s_word(self) -> str:
		return self._fname

	@property
	def l_word(self) -> "list[str]":
		return [self._fname]

	@property
	def defi(self) -> str:
		return f"File: {self._fname}"

	def byteProgress(self) -> "tuple[int, int] | None":
		return self._byteProgress

	@property
	def defiFormat(self) -> str:
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

	def removeEmptyAndDuplicateAltWords(self) -> None:
		pass

	def stripFullHtml(self) -> "str | None":
		pass


class Entry(BaseEntry):
	xdxfPattern = re.compile("^<k>[^<>]*</k>", re.DOTALL | re.IGNORECASE)
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
			r"<audio[ >]",
		]) + "|&[a-z]{2,8};|&#x?[0-9]{2,5};)",
		re.DOTALL | re.IGNORECASE,
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
	def getRawEntrySortKey(
		key: "Callable[[bytes], Any]",
		rawEntryCompress: bool,
	) -> "Callable[[RawEntryType], Any]":
		# FIXME: this type for `key` is only for rawEntryCompress=False
		# for rawEntryCompress=True, it is Callable[[bytes], Any]
		# here `x` is raw entity, meaning a tuple of form (word, defi) or
		# (word, defi, defiFormat)
		# so x[0] is word(s) in bytes, that can be a str (one word),
		# or a list or tuple (one word with or more alternatives)
		if rawEntryCompress:
			return lambda x: key(pickle_loads(zlib_decompress(x))[0])  # type: ignore
		# x is rawEntry, so x[0] is list of words (entry.l_word)
		return lambda x: key(x[0])  # type: ignore

	def __init__(
		self,
		word: MultiStr,
		defi: str,
		defiFormat: str = "m",
		byteProgress: "tuple[int, int] | None" = None,
	) -> None:
		"""
		Create a new Entry.

		word: string or a list of strings (including alternate words)
		defi: string or a list of strings (including alternate definitions)
		defiFormat (optional): definition format:
			"m": plain text
			"h": html
			"x": xdxf.
		"""
		# memory optimization:
		if isinstance(word, (list, tuple)):
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
		self._byteProgress = byteProgress  # tuple[int, int] | None

	def __repr__(self) -> str:
		return (
			f"Entry({self._word!r}, {self._defi!r}, "
			f"defiFormat={self._defiFormat!r})"
		)

	@property
	def s_word(self) -> str:
		"""Returns string of word, and all the alternate words separated by "|"."""
		if isinstance(self._word, str):
			return self._word
		return joinByBar(self._word)

	@property
	def l_word(self) -> "list[str]":
		"""Returns list of the word and all the alternate words."""
		if isinstance(self._word, str):
			return [self._word]
		return self._word

	@property
	def defi(self) -> str:
		"""Returns string of definition."""
		return self._defi

	@property
	def defiFormat(self) -> str:
		"""
		Returns definition format.

		Values:
			"m": plain text
			"h": html
			"x": xdxf.
		"""
		# TODO: type: Literal["m", "h", "x"]
		return self._defiFormat

	@defiFormat.setter
	def defiFormat(self, defiFormat: str) -> None:
		"""
		Set definition format.

		defiFormat:
			"m": plain text
			"h": html
			"x": xdxf.
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

	def byteProgress(self) -> "tuple[int, int] | None":
		return self._byteProgress

	def addAlt(self, alt: str) -> None:
		l_word = self.l_word
		l_word.append(alt)
		self._word = l_word

	def editFuncWord(self, func: "Callable[[str], str]") -> None:
		"""
		Run function `func` on all the words.

		`func` must accept only one string as argument
		and return the modified string.
		"""
		if isinstance(self._word, str):
			self._word = func(self._word)
			return

		self._word = [func(st) for st in self._word]

	def editFuncDefi(self, func: "Callable[[str], str]") -> None:
		"""
		Run function `func` on all the definitions.

		`func` must accept only one string as argument
		and return the modified string.
		"""
		self._defi = func(self._defi)

	def _stripTrailingBR(self, s: str) -> str:
		while s.endswith(("<BR>", "<br>")):
			s = s[:-4]
		return s

	def strip(self) -> None:
		"""Strip whitespaces from all words and definitions."""
		self.editFuncWord(str.strip)
		self.editFuncDefi(str.strip)
		self.editFuncDefi(self._stripTrailingBR)

	def replaceInWord(self, source: str, target: str) -> None:
		"""Replace string `source` with `target` in all words."""
		if isinstance(self._word, str):
			self._word = self._word.replace(source, target)
			return

		self._word = [st.replace(source, target) for st in self._word]

	def replaceInDefi(self, source: str, target: str) -> None:
		"""Replace string `source` with `target` in all definitions."""
		self._defi = self._defi.replace(source, target)

	def replace(self, source: str, target: str) -> None:
		"""Replace string `source` with `target` in all words and definitions."""
		self.replaceInWord(source, target)
		self.replaceInDefi(source, target)

	def removeEmptyAndDuplicateAltWords(self) -> None:
		l_word = self.l_word
		if len(l_word) == 1:
			return
		l_word = [word for word in l_word if word]
		l_word = list(unique_everseen(l_word))
		self._word = l_word

	def stripFullHtml(self) -> "str | None":
		"""Remove <html><head><body> tags and returns error."""
		defi = self._defi
		if not defi.startswith("<"):
			return None
		if defi.startswith("<!DOCTYPE html>"):
			defi = defi[len("<!DOCTYPE html>") :].strip()
			if not defi.startswith("<html"):
				return "Has <!DOCTYPE html> but no <html>"
		else:
			if not defi.startswith("<html>"):
				return None
		i = defi.find("<body")
		if i == -1:
			return "<body not found"
		defi = defi[i + 5 :]
		i = defi.find(">")
		if i == -1:
			return "'>' after <body not found"
		defi = defi[i + 1 :]
		i = defi.find("</body")
		if i == -1:
			return "</body close not found"
		defi = defi[:i]
		self._defi = defi
		return None
