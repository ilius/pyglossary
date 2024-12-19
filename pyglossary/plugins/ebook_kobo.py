# -*- coding: utf-8 -*-
# The MIT License (MIT)
# Copyright © 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright © 2022 Saeed Rasooli <saeed.gnu@gmail.com>
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import re
import unicodedata
from gzip import compress, decompress
from operator import itemgetter
from pathlib import Path
from pickle import dumps, loads
from typing import TYPE_CHECKING

from pyglossary import core
from pyglossary.core import exc_note, log, pip
from pyglossary.flags import NEVER
from pyglossary.os_utils import indir

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.option import Option

__all__ = [
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
lname = "kobo"
name = "Kobo"
description = "Kobo E-Reader Dictionary"
extensions = (".kobo",)
extensionCreate = ".kobo.zip"
singleFile = False
kind = "package"
sortOnWrite = NEVER
wiki = "https://en.wikipedia.org/wiki/Kobo_eReader"
website = (
	"https://www.kobo.com",
	"www.kobo.com",
)

# https://help.kobo.com/hc/en-us/articles/360017640093-Add-new-dictionaries-to-your-Kobo-eReader


optionsProp: dict[str, Option] = {}


# Penelope option: marisa_index_size=1000000


def is_cyrillic_char(c: str) -> bool:
	# U+0400 - U+04FF: Cyrillic
	# U+0500 - U+052F: Cyrillic Supplement
	if "\u0400" <= c <= "\u052f":
		return True

	# U+2DE0 - U+2DFF: Cyrillic Extended-A
	if "\u2de0" <= c <= "\u2dff":
		return True

	# U+A640 - U+A69F: Cyrillic Extended-B
	if "\ua640" <= c <= "\ua69f":
		return True

	# U+1C80 - U+1C8F: Cyrillic Extended-C
	if "\u1c80" <= c <= "\u1c8f":
		return True

	# U+FE2E, U+FE2F: Combining Half Marks
	# U+1D2B, U+1D78: Phonetic Extensions
	return c in {"\ufe2e", "\ufe2f", "\u1d2b", "\u1d78"}


def fixFilename(fname: str) -> str:
	return Path(fname.replace("/", "2F").replace("\\", "5C")).name


class Writer:
	WORDS_FILE_NAME = "words"

	depends = {
		"marisa_trie": "marisa-trie",
	}

	@staticmethod
	def stripFullHtmlError(entry: EntryType, error: str) -> None:
		log.error(f"error in stripFullHtml: {error}, words={entry.l_word!r}")

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._words: list[str] = []
		self._img_pattern = re.compile(
			'<img src="([^<>"]*?)"( [^<>]*?)?>',
			re.DOTALL,
		)
		# img tag has no closing
		glos.stripFullHtml(errorHandler=self.stripFullHtmlError)

	def get_prefix(self, word: str) -> str:  # noqa: PLR6301
		if not word:
			return "11"
		wo = word[:2].strip().lower()
		if not wo:
			return "11"
		if wo[0] == "\x00":
			return "11"
		if len(wo) > 1 and wo[1] == "\x00":
			wo = wo[:1]
		if is_cyrillic_char(wo[0]):
			return wo
		# if either of the first 2 chars are not unicode letters, return "11"
		for c in wo:
			if not unicodedata.category(c).startswith("L"):
				return "11"
		return wo.ljust(2, "a")

	def fix_defi(self, defi: str) -> str:
		# @pgaskin on #219: Kobo supports images in dictionaries,
		# but these have a lot of gotchas
		# (see https://pgaskin.net/dictutil/dicthtml/format.html).
		# Basically, The best way to do it is to encode the images as a
		# base64 data URL after shrinking it and making it grayscale
		# (if it's JPG, this is as simple as only keeping the Y channel)

		# for now we just skip data entries and remove '<img' tags
		return self._img_pattern.sub("[Image: \\1]", defi)

	def write_groups(self) -> Generator[None, EntryType, None]:
		import gzip

		dataEntryCount = 0

		htmlHeader = '<?xml version="1.0" encoding="utf-8"?><html>\n'

		groupCounter = 0
		htmlContents = htmlHeader

		def writeGroup(lastPrefix: str) -> None:
			nonlocal htmlContents
			group_fname = fixFilename(lastPrefix)
			htmlContents += "</html>"
			core.trace(
				log,
				f"writeGroup: {lastPrefix!r}, "
				f"{group_fname!r}, count={groupCounter}",
			)
			with gzip.open(group_fname + ".html", mode="wb") as gzipFile:
				gzipFile.write(htmlContents.encode("utf-8"))
			htmlContents = htmlHeader

		allWords: list[str] = []
		# TODO: switch to SQLite, like StarDict writer
		data: list[tuple[str, bytes]] = []

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				dataEntryCount += 1
				continue
			l_word = entry.l_word
			allWords += l_word
			wordsByPrefix: dict[str, list[str]] = {}
			for word in l_word:
				prefix = self.get_prefix(word)
				if prefix in wordsByPrefix:
					wordsByPrefix[prefix].append(word)
				else:
					wordsByPrefix[prefix] = [word]
			defi = self.fix_defi(entry.defi)
			mainHeadword = l_word[0]
			for prefix, p_words in wordsByPrefix.items():
				headword, *variants = p_words
				if headword != mainHeadword:
					headword = f"{mainHeadword}, {headword}"
				data.append(
					(
						prefix,
						compress(
							dumps(
								(
									headword,
									variants,
									defi,
								),
							),
						),
					),
				)
			del entry

		log.info("Kobo: sorting entries...")
		data.sort(key=itemgetter(0))

		log.info("Kobo: writing entries...")

		lastPrefix = ""
		for prefix, row in data:
			headword, variants, defi = loads(decompress(row))
			if lastPrefix and prefix != lastPrefix:
				writeGroup(lastPrefix)
				groupCounter = 0
			lastPrefix = prefix

			htmlVariants = "".join(
				f'<variant name="{v.strip().lower()}"/>' for v in variants
			)
			body = f"<div><b>{headword}</b><var>{htmlVariants}</var><br/>{defi}</div>"
			htmlContents += f'<w><a name="{headword}" />{body}</w>\n'
			groupCounter += 1
		del data

		if groupCounter > 0:
			writeGroup(lastPrefix)

		if dataEntryCount > 0:
			log.warning(
				f"ignored {dataEntryCount} files (data entries)"
				" and replaced '<img ...' tags in definitions with placeholders",
			)

		self._words = allWords

	def open(self, filename: str) -> None:
		try:
			import marisa_trie  # type: ignore # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install marisa-trie` to install")
			raise
		self._filename = filename

	def write(self) -> Generator[None, EntryType, None]:
		with indir(self._filename, create=True):
			yield from self.write_groups()

	def finish(self) -> None:
		import marisa_trie

		with indir(self._filename, create=False):
			trie = marisa_trie.Trie(self._words)
			trie.save(self.WORDS_FILE_NAME)
		self._filename = ""
