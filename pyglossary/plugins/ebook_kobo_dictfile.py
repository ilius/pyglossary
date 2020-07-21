# -*- coding: utf-8 -*-
# The MIT License (MIT)

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
from pyglossary.text_reader import TextGlossaryReader

enable = True
format = "Dictfile"
description = "Kobo E-Reader Dictfile"
extensions = (".df",)
# https://github.com/pgaskin/dictutil
tools = [
	{
		"name": "dictgen",
		"web": "https://pgaskin.net/dictutil/dictgen/",
		"platforms": ["Linux", "Windows", "Mac"],
		"license": "MIT",
	},
]


def fixWord(word: str) -> str:
	return word.replace("\n", " ")


def escapeDefi(defi: str) -> str:
	return defi.replace("\n@", "\n @")\
		.replace("\n:", "\n :")\
		.replace("\n&", "\n &")


def unescapeDefi(defi: str) -> str:
	return defi.replace("\n @", "\n@")\
		.replace("\n :", "\n:")\
		.replace("\n &", "\n&")


class Reader(TextGlossaryReader):
	def __len__(self):
		return 0

	def isInfoWord(self, word):
		return False

	def fixInfoWord(self, word):
		raise NotImplementedError

	def nextPair(self):
		if not self._file:
			raise StopIteration
		words = []
		defiLines = []

		while True:
			line = self.readline()
			if not line:
				break
			line = line.rstrip("\n\r")
			if line.startswith("@"):
				if words:
					self._bufferLine = line
					return words, unescapeDefi("\n".join(defiLines))
				words = [line[1:]]
				continue
			if line.startswith("&"):
				words.append(line[1:])
				continue
			defiLines.append(line)

		if words:
			return words, unescapeDefi("\n".join(defiLines))

		raise StopIteration


class Writer(object):
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def write(
		self,
		filename: str,
	) -> Generator[None, "BaseEntry", None]:
		glos = self._glos
		fileObj = open(filename, "w", encoding="utf-8")
		# dictgen's ParseDictFile does not seem to support glossary info / metedata
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				continue
			words = entry.l_word
			defi = entry.defi
			fileObj.write(f"@ {fixWord(words[0])}\n")
			for alt in words[1:]:
				fileObj.write(f"& {fixWord(alt)}\n")
			fileObj.write(f"{escapeDefi(defi)}\n\n")
		fileObj.close()
