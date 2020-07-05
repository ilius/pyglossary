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

enable = True
format = "Kobo"
description = "Kobo E-Reader Dictionary"
extensions = (".kobo",)
sortOnWrite = ALWAYS

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

	# U+1D2B, U+1D78: Phonetic Extensions:
	if c in ("\u1D2B", "\u1D78"):
		return True

	# U+FE2E – U+FE2F: Combining Half Marks
	if "\uFE2E" <= c <= "\uFE2F":
		return True

	return False


def fixFilename(fname: str) -> str:
	return Path(fname.replace("/", "2F").replace("\\", "5C")).name


class Writer:
	WORDS_FILE_NAME = "words"
	MARISA_BUILD = "marisa-build"
	MARISA_REVERSE_LOOKUP = "marisa-reverse-lookup"

	def __init__(self, glos, **kwargs):
		self._glos = glos

	def get_prefix(self, word: str) -> str:
		if not word:
			return "11"
		wo = word[:2].strip().lower()
		if not wo:
			return "11"
		if is_cyrillic_char(wo[0]):
			return wo
		wo = wo.ljust(2, "a")
		return wo

	def sort_key(self, b_word: bytes) -> Any:
		word = b_word.decode("utf-8")
		return (
			self.get_prefix(word),
			word,
		)

	def write_groups(self):
		import gzip
		words = []

		self._glos.sortWords(key=self.sort_key)
		for group_i, (group_prefix, group_entry_iter) in enumerate(groupby(
			self._glos,
			lambda entry: self.get_prefix(entry.getWord())
		)):
			group_fname = fixFilename(group_prefix)
			htmlContents = "<?xml version=\"1.0\" encoding=\"utf-8\"?><html>\n"
			for entry in group_entry_iter:
				if entry.isData():
					continue
				word = entry.getWord()
				defi = entry.getDefi()
				words.append(word)
				htmlContents += f"<w><a name=\"{word}\"/><div><b>{word}</b>"\
					f"<br/>{defi}</div></w>\n"
			htmlContents += "</html>"
			with gzip.open(group_fname + ".html", mode="wb") as gzipFile:
				gzipFile.write(htmlContents.encode("utf-8"))

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
