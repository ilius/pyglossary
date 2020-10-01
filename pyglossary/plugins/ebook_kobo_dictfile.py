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

optionsProp = {
	"encoding": EncodingOption(),
}

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


def fixDefi(defi: str) -> str:
	import mistune
	defi = defi.replace("\n @", "\n@")\
		.replace("\n :", "\n:")\
		.replace("\n &", "\n&")
	defi = defi.lstrip()
	if defi.startswith("<html>"):
		defi = defi[len("<html>"):].lstrip()
		i = defi.find("</html>")
		if i >= 0:
			defi = defi[:i]
	else:
		defi = mistune.html(defi)
	return defi


class Reader(TextGlossaryReader):
	depends = {
		"mistune": "mistune==2.0.0a5",
	}

	def open(self, filename: str) -> None:
		try:
			import mistune
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install mistune` to install"
			raise e
		TextGlossaryReader.open(self, filename)
		self._glos.setDefaultDefiFormat("h")

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
					return words, fixDefi("\n".join(defiLines))
				words = [line[1:]]
				continue
			if line.startswith("&"):
				words.append(line[1:])
				continue
			defiLines.append(line)

		if words:
			return words, fixDefi("\n".join(defiLines))

		raise StopIteration


class Writer(object):
	_encoding: str = "utf-8"

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._file = None

	def finish(self):
		if self._file is None:
			return
		self._file.close()

	def open(self, filename: str) -> None:
		self._file = open(filename, "w", encoding=self._encoding)
		# dictgen's ParseDictFile does not seem to support glossary info / metedata

	def write(
		self,
	) -> Generator[None, "BaseEntry", None]:
		fileObj = self._file
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				continue
			words = entry.l_word
			defi = entry.defi

			entry.detectDefiFormat()
			if entry.defiFormat == "h":
				entry.stripFullHtml()
				defi = f"<html>{entry.defi}"

			fileObj.write(f"@ {fixWord(words[0])}\n")
			for alt in words[1:]:
				fileObj.write(f"& {fixWord(alt)}\n")
			fileObj.write(f"{escapeDefi(defi)}\n\n")
