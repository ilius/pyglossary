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

enable = True
format = "Kobo"
description = "Kobo E-Reader Dictionary"
extensions = (".kobo",)
sortOnWrite = ALWAYS

tools = [
	{
		"name": "Kobo eReader",
		"web": "https://www.kobo.com",
		"platforms": ["Kobo eReader"],
		"license": "Proprietary",
	},
]

optionsProp = {
	# "group_by_prefix_merge_min_size": IntOption(),
	# "group_by_prefix_merge_across_first": BoolOption(),
	"keep": BoolOption(),
	"marisa_bin_path": StrOption(),
}


"""
FIXME:
Kobo will only look in the file matching the word’s prefix, so if a
variant has a different prefix, it must be duplicated into each matching file
(note that duplicate words aren’t an issue).
https://pgaskin.net/dictutil/dicthtml/prefixes.html
"""


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
	MARISA_BUILD = "marisa-build"
	MARISA_REVERSE_LOOKUP = "marisa-reverse-lookup"

	def __init__(self, glos, **kwargs):
		self._glos = glos
		self._img_pattern = re.compile(
			'<img src="([^<>"]*?)"( [^<>]*?)?>',
			re.DOTALL,
		)
		# img tag has no closing

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

	def sort_key(self, b_word: bytes) -> Any:
		word = b_word.decode("utf-8")
		return (
			self.get_prefix(word),
			word,
		)

	def fix_defi(self, defi: str) -> str:
		# @geek1011 on #219: Kobo supports images in dictionaries,
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
		words = []
		dataEntryCount = 0

		self._glos.sortWords(key=self.sort_key)
		for group_i, (group_prefix, group_entry_iter) in enumerate(groupby(
			self._glos,
			lambda entry: self.get_prefix(entry.word)
		)):
			group_fname = fixFilename(group_prefix)
			htmlContents = "<?xml version=\"1.0\" encoding=\"utf-8\"?><html>\n"

			for entry in group_entry_iter:
				if entry.isData():
					dataEntryCount += 1
					continue
				word = entry.word
				defi = entry.defi
				defi = self.fix_defi(defi)
				words.append(word)
				htmlContents += f"<w><a name=\"{word}\" /><div><b>{word}</b>"\
					f"<br/>{defi}</div></w>\n"
			htmlContents += "</html>"
			with gzip.open(group_fname + ".html", mode="wb") as gzipFile:
				gzipFile.write(htmlContents.encode("utf-8"))

		if dataEntryCount > 0:
			log.warn(
				f"ignored {dataEntryCount} files (data entries)"
				" and replaced '<img ...' tags in definitions with placeholders"
			)

		return words

	def write(
		self,
		filename,
	):
		try:
			import marisa_trie
		except ImportError as e:
			log.error("Run: sudo pip3 install marisa-trie")
			raise e

		with indir(filename, create=True):
			words = self.write_groups()
			trie = marisa_trie.Trie(words)
			trie.save(self.WORDS_FILE_NAME)
