# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright © 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright © 2020 Saeed Rasooli <saeed.gnu@gmail.com>

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

from formats_common import *
from itertools import groupby
from pathlib import Path
import unicodedata
import re
from pickle import dumps, loads
from gzip import compress, decompress

enable = True
format = "Kobo"
description = "Kobo E-Reader Dictionary"
extensions = (".kobo",)
sortOnWrite = NEVER

tools = [
	{
		"name": "Kobo eReader",
		"web": "https://www.kobo.com",
		"platforms": ["Kobo eReader"],
		"license": "Proprietary",
	},
]
# https://help.kobo.com/hc/en-us/articles/360017640093-Add-new-dictionaries-to-your-Kobo-eReader


optionsProp = {
}


# Penelope option: marisa_index_size=1000000


def is_cyrillic_char(c: str) -> bool:
	# U+0400 – U+04FF: Cyrillic
	# U+0500 – U+052F: Cyrillic Supplement
	if "\u0400" <= c <= "\u052F":
		return True

	# U+2DE0 – U+2DFF: Cyrillic Extended-A
	if "\u2DE0" <= c <= "\u2DFF":
		return True

	# U+A640 – U+A69F: Cyrillic Extended-B
	if "\uA640" <= c <= "\uA69F":
		return True

	# U+1C80 – U+1C8F: Cyrillic Extended-C
	if "\u1C80" <= c <= "\u1C8F":
		return True

	# U+FE2E, U+FE2F: Combining Half Marks
	# U+1D2B, U+1D78: Phonetic Extensions
	return c in ("\uFE2E", "\uFE2F", "\u1D2B", "\u1D78")


def fixFilename(fname: str) -> str:
	return Path(fname.replace("/", "2F").replace("\\", "5C")).name


class Writer:
	WORDS_FILE_NAME = "words"

	depends = {
		"marisa_trie": "marisa-trie",
	}

	def __init__(self, glos, **kwargs):
		self._glos = glos
		self._filename = None
		self._words = []
		self._img_pattern = re.compile(
			'<img src="([^<>"]*?)"( [^<>]*?)?>',
			re.DOTALL,
		)
		# img tag has no closing
		try:
			import marisa_trie
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install marisa-trie` to install"
			raise e

	def get_prefix(self, word: str) -> str:
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
		wo = wo.ljust(2, "a")
		return wo

	def fix_defi(self, defi: str) -> str:
		# @pgaskin on #219: Kobo supports images in dictionaries,
		# but these have a lot of gotchas
		# (see https://pgaskin.net/dictutil/dicthtml/format.html).
		# Basically, The best way to do it is to encode the images as a
		# base64 data URL after shrinking it and making it grayscale
		# (if it's JPG, this is as simple as only keeping the Y channel)

		# for now we just skip data entries and remove '<img' tags
		defi = self._img_pattern.sub("[Image: \\1]", defi)
		return defi

	def write_groups(self):
		import gzip
		from collections import OrderedDict
		from pyglossary.entry import Entry

		glos = self._glos
		dataEntryCount = 0

		htmlHeader = "<?xml version=\"1.0\" encoding=\"utf-8\"?><html>\n"

		groupCounter = 0
		htmlContents = htmlHeader

		def writeGroup(lastPrefix):
			nonlocal htmlContents
			group_fname = fixFilename(lastPrefix)
			htmlContents += "</html>"
			log.debug(
				f"writeGroup: {lastPrefix!r}, "
				"{group_fname!r}, count={groupCounter}"
			)
			with gzip.open(group_fname + ".html", mode="wb") as gzipFile:
				gzipFile.write(htmlContents.encode("utf-8"))
			htmlContents = htmlHeader

		allWords = []
		data = []

		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				dataEntryCount += 1
				continue
			l_word = entry.l_word
			allWords += l_word
			wordsByPrefix = OrderedDict()
			for word in l_word:
				prefix = self.get_prefix(word)
				if prefix in wordsByPrefix:
					wordsByPrefix[prefix].append(word)
				else:
					wordsByPrefix[prefix] = [word]
			entry.stripFullHtml()
			defi = self.fix_defi(entry.defi)
			mainHeadword = l_word[0]
			for prefix, p_words in wordsByPrefix.items():
				headword, *variants = p_words
				if headword != mainHeadword:
					headword = f"{mainHeadword}, {headword}"
				data.append((
					prefix,
					compress(dumps((
						headword,
						variants,
						defi,
					)))
				))
			del entry

		log.info(f"Kobo: sorting entries...")
		data.sort(key=lambda x: x[0])

		log.info(f"Kobo: writing entries...")

		lastPrefix = ""
		for prefix, row in data:
			headword, variants, defi = loads(decompress(row))
			if lastPrefix and prefix != lastPrefix:
				writeGroup(lastPrefix)
				groupCounter = 0
			lastPrefix = prefix

			htmlVariants = "".join(
				f'<variant name="{v.strip().lower()}"/>'
				for v in variants
			)
			body = f"<div><b>{headword}</b><var>{htmlVariants}</var><br/>{defi}</div>"
			htmlContents += f"<w><a name=\"{headword}\" />{body}</w>\n"
			groupCounter += 1
		del data

		if groupCounter > 0:
			writeGroup(lastPrefix)

		if dataEntryCount > 0:
			log.warn(
				f"ignored {dataEntryCount} files (data entries)"
				" and replaced '<img ...' tags in definitions with placeholders"
			)

		self._words = allWords

	def open(self, filename: str) -> None:
		self._filename = filename

	def write(self) -> "Generator[None, BaseEntry, None]":
		with indir(self._filename, create=True):
			yield from self.write_groups()

	def finish(self) -> None:
		import marisa_trie
		with indir(self._filename, create=False):
			trie = marisa_trie.Trie(self._words)
			trie.save(self.WORDS_FILE_NAME)
		self._filename = None
