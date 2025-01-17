# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from os.path import isdir, join
from typing import TYPE_CHECKING

from pyglossary.text_utils import (
	escapeNTB,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


def _makeDir(direc: str) -> None:
	if not isdir(direc):
		os.makedirs(direc)


class Writer:
	_encoding: str = "utf-8"
	_prev_link: bool = True

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._clear()

	def finish(self) -> None:
		self._clear()

	def open(self, filename: str) -> None:
		self._filename = filename
		self._resDir = join(filename, "res")
		os.makedirs(filename)
		os.mkdir(self._resDir)

	def _clear(self) -> None:
		self._filename = ""
		self._resDir = ""
		self._encoding = "utf-8"
		self._hashSet: set[str] = set()
		# self._wordCount = None

	@staticmethod
	def hashToPath(h: str) -> str:
		return h[:2] + "/" + h[2:]

	def getEntryHash(self, entry: EntryType) -> str:
		"""
		Return hash string for given entry
		don't call it twice for one entry, if you do you will get a
		different hash string.
		"""
		from hashlib import sha1

		hash_ = sha1(entry.s_word.encode("utf-8")).hexdigest()[:8]  # noqa: S324
		if hash_ not in self._hashSet:
			self._hashSet.add(hash_)
			return hash_
		index = 0
		while True:
			tmp_hash = hash_ + f"{index:x}"
			if tmp_hash not in self._hashSet:
				self._hashSet.add(tmp_hash)
				return tmp_hash
			index += 1

	def saveEntry(
		self,
		thisEntry: EntryType,
		thisHash: str,
		prevHash: str | None,
		nextHash: str | None,
	) -> None:
		dpath = join(self._filename, thisHash[:2])
		_makeDir(dpath)
		with open(
			join(dpath, thisHash[2:]),
			"w",
			encoding=self._encoding,
		) as toFile:
			nextPath = self.hashToPath(nextHash) if nextHash else "END"
			if self._prev_link:
				prevPath = self.hashToPath(prevHash) if prevHash else "START"
				header = prevPath + " " + nextPath
			else:
				header = nextPath
			toFile.write(
				"\n".join(
					[
						header,
						escapeNTB(thisEntry.s_word, bar=False),
						thisEntry.defi,
					],
				),
			)

	def write(self) -> Generator[None, EntryType, None]:
		from pyglossary.json_utils import dataToPrettyJson

		thisEntry = yield
		if thisEntry is None:
			raise ValueError("glossary is empty")

		count = 1
		rootHash = thisHash = self.getEntryHash(thisEntry)
		prevHash = None

		while True:
			nextEntry = yield
			if nextEntry is None:
				break
			if nextEntry.isData():
				nextEntry.save(self._resDir)
				continue
			nextHash = self.getEntryHash(nextEntry)
			self.saveEntry(thisEntry, thisHash, prevHash, nextHash)
			thisEntry = nextEntry
			prevHash, thisHash = thisHash, nextHash
			count += 1
		self.saveEntry(thisEntry, thisHash, prevHash, None)

		with open(
			join(self._filename, "info.json"),
			"w",
			encoding=self._encoding,
		) as toFile:
			info = {}
			info["name"] = self._glos.getInfo("name")
			info["root"] = self.hashToPath(rootHash)
			info["prev_link"] = self._prev_link
			info["wordCount"] = count
			# info["modified"] =

			info |= self._glos.getExtraInfos(["name", "root", "prev_link", "wordCount"])

			toFile.write(dataToPrettyJson(info))
