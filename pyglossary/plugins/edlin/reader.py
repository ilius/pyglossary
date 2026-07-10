from __future__ import annotations

from os.path import dirname, isdir, isfile, join
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.os_utils import countFilesRecursive, listFilesRecursiveRelPath
from pyglossary.text_utils import (
	splitByBarUnescapeNTB,
	unescapeNTB,
)

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = False
	_encoding: str = "utf-8"

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._clear()

	def close(self) -> None:
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._prev_link = True
		self._entryCount = None
		self._rootPath = None
		self._resDir = ""
		self._resCount = 0

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToData

		if isdir(filename):
			infoFname = join(filename, "info.json")
		elif isfile(filename):
			infoFname = filename
			filename = dirname(filename)
		else:
			raise ValueError(
				f"error while opening {filename!r}: no such file or directory",
			)
		self._filename = filename

		with open(infoFname, encoding=self._encoding) as infoFp:
			info = jsonToData(infoFp.read())
		if not isinstance(info, dict):
			raise TypeError(f"expected dict in info.json, got {type(info).__name__}")
		self._entryCount = info.pop("wordCount")
		self._prev_link = info.pop("prev_link")
		self._rootPath = info.pop("root")
		for key, value in info.items():
			self._glos.info[key] = value

		self._resDir = join(filename, "res")
		resCount = 0
		if not isdir(self._resDir):
			self._resDir = ""
		elif self._glos.progressbar:
			log.info("Counting resource files...")
			resCount = countFilesRecursive(self._resDir)
			log.info(f"Found {resCount} resource files")
		self._resCount = resCount

	def __len__(self) -> int:
		if self._entryCount is None:
			log.error("called len() on a reader which is not open")
			return 0
		return self._entryCount + self._resCount

	def countResourceFiles(self) -> int:
		return self._resCount

	def __iter__(self) -> Iterator[EntryType]:
		if not self._rootPath:
			raise RuntimeError("iterating over a reader while it's not open")

		entryCount = 0
		nextPath = self._rootPath
		while nextPath != "END":
			entryCount += 1
			# before or after reading word and defi
			# (and skipping empty entry)? FIXME

			with open(
				join(self._filename, nextPath),
				encoding=self._encoding,
			) as file:
				header = file.readline().rstrip()
				if self._prev_link:
					_prevPath, nextPath = header.split(" ")
				else:
					nextPath = header
				term = file.readline()
				if not term:
					yield None  # update progressbar
					continue
				defi = file.read()
				if not defi:
					log.warning(
						f"Edlin Reader: no definition for word {term!r}, skipping",
					)
					yield None  # update progressbar
					continue
				term = term.rstrip()
				defi = defi.rstrip()

			if self._glos.alts:
				term = splitByBarUnescapeNTB(term)
				if len(term) == 1:
					term = term[0]
			else:
				term = unescapeNTB(term, bar=False)

			# defi = unescapeNTB(defi)
			yield self._glos.newEntry(term, defi)

		if entryCount != self._entryCount:
			log.warning(
				f"{entryCount} words found, "
				f"entryCount in info.json was {self._entryCount}",
			)
			self._entryCount = entryCount

		resDir = self._resDir
		for fname in listFilesRecursiveRelPath(resDir):
			with open(join(resDir, fname), "rb") as file:
				yield self._glos.newDataEntry(
					fname,
					file.read(),
				)
