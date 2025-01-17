# mypy: ignore-errors
from __future__ import annotations

from os import listdir
from os.path import isdir, isfile, join, splitext
from typing import TYPE_CHECKING

from pyglossary.compression import (
	compressionOpenFunc,
)
from pyglossary.core import log
from pyglossary.text_utils import (
	splitByBarUnescapeNTB,
)

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = None
		self._wordCount = 0

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToData

		self._filename = filename

		with open(join(filename, "info.json"), encoding="utf-8") as infoFp:
			info = jsonToData(infoFp.read())
		self._wordCount = info.pop("wordCount")
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def close(self) -> None:
		pass

	def __len__(self) -> int:
		return self._wordCount

	def _fromFile(self, fpath: str) -> EntryType:
		_, ext = splitext(fpath)
		c_open = compressionOpenFunc(ext.lstrip("."))
		if not c_open:
			log.error(f"invalid extension {ext}")
			c_open = open
		with c_open(fpath, "rt", encoding="utf-8") as _file:
			words = splitByBarUnescapeNTB(_file.readline().rstrip("\n"))
			defi = _file.read()
			return self._glos.newEntry(words, defi)

	@staticmethod
	def _listdirSortKey(name: str) -> str:
		name_nox, ext = splitext(name)
		if ext == ".d":
			return name
		return name_nox

	def _readDir(
		self,
		dpath: str,
		exclude: set[str] | None,
	) -> Generator[EntryType, None, None]:
		children = listdir(dpath)
		if exclude:
			children = [name for name in children if name not in exclude]
		children.sort(key=self._listdirSortKey)
		for name in children:
			cpath = join(dpath, name)
			if isfile(cpath):
				yield self._fromFile(cpath)
				continue
			if isdir(cpath):
				yield from self._readDir(cpath, None)
				continue
			log.error(f"Not a file nor a directory: {cpath}")

	def __iter__(self) -> Iterator[EntryType]:
		yield from self._readDir(
			self._filename,
			{
				"info.json",
			},
		)
