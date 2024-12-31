# -*- coding: utf-8 -*-
# edlin.py
#
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from __future__ import annotations

import os
from os.path import dirname, isdir, isfile, join
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)
from pyglossary.text_utils import (
	escapeNTB,
	splitByBarUnescapeNTB,
	unescapeNTB,
)

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = [
	"Reader",
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "edlin"
name = "Edlin"
# Editable Linked List of Entries
description = "EDLIN"
extensions = (".edlin",)
extensionCreate = ".edlin/"
singleFile = False
kind = "directory"
wiki = ""
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"prev_link": BoolOption(comment="Enable link to previous entry"),
}


def makeDir(direc: str) -> None:
	if not isdir(direc):
		os.makedirs(direc)


class Reader:
	_encoding: str = "utf-8"

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._clear()

	def close(self) -> None:
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._prev_link = True
		self._wordCount = None
		self._rootPath = None
		self._resDir = ""
		self._resFileNames: list[str] = []

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
		self._wordCount = info.pop("wordCount")
		self._prev_link = info.pop("prev_link")
		self._rootPath = info.pop("root")
		for key, value in info.items():
			self._glos.setInfo(key, value)

		self._resDir = join(filename, "res")
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []

	def __len__(self) -> int:
		if self._wordCount is None:
			log.error("called len() on a reader which is not open")
			return 0
		return self._wordCount + len(self._resFileNames)

	def __iter__(self) -> Iterator[EntryType]:
		if not self._rootPath:
			raise RuntimeError("iterating over a reader while it's not open")

		wordCount = 0
		nextPath = self._rootPath
		while nextPath != "END":
			wordCount += 1
			# before or after reading word and defi
			# (and skipping empty entry)? FIXME

			with open(
				join(self._filename, nextPath),
				encoding=self._encoding,
			) as _file:
				header = _file.readline().rstrip()
				if self._prev_link:
					_prevPath, nextPath = header.split(" ")
				else:
					nextPath = header
				word = _file.readline()
				if not word:
					yield None  # update progressbar
					continue
				defi = _file.read()
				if not defi:
					log.warning(
						f"Edlin Reader: no definition for word {word!r}, skipping",
					)
					yield None  # update progressbar
					continue
				word = word.rstrip()
				defi = defi.rstrip()

			if self._glos.alts:
				word = splitByBarUnescapeNTB(word)
				if len(word) == 1:
					word = word[0]
			else:
				word = unescapeNTB(word, bar=False)

			# defi = unescapeNTB(defi)
			yield self._glos.newEntry(word, defi)

		if wordCount != self._wordCount:
			log.warning(
				f"{wordCount} words found, "
				f"wordCount in info.json was {self._wordCount}",
			)
			self._wordCount = wordCount

		resDir = self._resDir
		for fname in self._resFileNames:
			with open(join(resDir, fname), "rb") as _file:
				yield self._glos.newDataEntry(
					fname,
					_file.read(),
				)


class Writer:
	_encoding: str = "utf-8"
	_prev_link: bool = True

	def __init__(self, glos: GlossaryType) -> None:
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
		makeDir(dpath)
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
