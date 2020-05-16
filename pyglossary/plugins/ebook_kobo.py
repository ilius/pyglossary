# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright (C) 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright (C) 2016 Saeed Rasooli <saeed.gnu@gmail.com>

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
from pyglossary.ebook_base import get_prefix
from itertools import groupby
from pathlib import Path

enable = True
format = "Kobo"
description = "Kobo E-Reader Dictionary"
extensions = [".kobo"]
sortOnWrite = ALWAYS

optionsProp = {
	"group_by_prefix_length": IntOption(),
	# "group_by_prefix_merge_min_size": IntOption(),
	# "group_by_prefix_merge_across_first": BoolOption(),
	"keep": BoolOption(),
	"marisa_bin_path": StrOption(),
}


def fixFilename(fname: str) -> str:
	return Path(fname.replace("/", "2F").replace("\\", "5C")).name


class Writer:
	WORDS_FILE_NAME = "words"
	MARISA_BUILD = "marisa-build"
	MARISA_REVERSE_LOOKUP = "marisa-reverse-lookup"

	def __init__(self, glos, **kwargs):
		self._glos = glos

	def write_groups(self, group_by_prefix_length):
		import gzip
		words = []

		self._glos.sortWords()
		for group_i, (group_prefix, group_entry_iter) in enumerate(groupby(
			self._glos,
			lambda tmpEntry: get_prefix(
				tmpEntry.getWord(),
				group_by_prefix_length,
			),
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
		group_by_prefix_length=2,
	):
		try:
			import marisa_trie
		except ImportError as e:
			log.error("Run: sudo pip3 install marisa-trie")
			raise e

		with indir(filename, create=True):
			words = self.write_groups(group_by_prefix_length)
			trie = marisa_trie.Trie(words)
			trie.save(self.WORDS_FILE_NAME)
