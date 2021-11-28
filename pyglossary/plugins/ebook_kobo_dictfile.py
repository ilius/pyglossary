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
from pyglossary.image_utils import extractInlineHtmlImages

enable = True
lname = "kobo_dictfile"
format = "Dictfile"
description = "Kobo E-Reader Dictfile (.df)"
extensions = (".df",)
extensionCreate = ".df"
kind = "text"
wiki = ""
website = (
	"https://pgaskin.net/dictutil/dictgen/#dictfile-format",
	"dictgen - dictutil",
)
# https://github.com/pgaskin/dictutil

optionsProp = {
	"encoding": EncodingOption(),
	"extract_inline_images": BoolOption(comment="Extract inline images"),
}


def fixWord(word: str) -> str:
	return word.replace("\n", " ")


def escapeDefi(defi: str) -> str:
	return defi.replace("\n@", "\n @")\
		.replace("\n:", "\n :")\
		.replace("\n&", "\n &")


class Reader(TextGlossaryReader):
	depends = {
		"mistune": "mistune==2.0.0a5",
	}

	_extract_inline_images = True

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

	def fixDefi(self, defi: str) -> str:
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
		if self._extract_inline_images:
			defi, images = extractInlineHtmlImages(
				defi,
				self._glos.tmpDataDir,
				fnamePrefix="",  # maybe f"{self._pos:06d}-"
			)
			if images:
				defi = (defi, images)
		return defi

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
					return words, self.fixDefi("\n".join(defiLines))
				words = [line[1:]]
				continue
			if line.startswith("&"):
				words.append(line[1:])
				continue
			defiLines.append(line)

		if words:
			return words, self.fixDefi("\n".join(defiLines))

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
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)

	def open(self, filename: str) -> None:
		self._file = open(filename, "w", encoding=self._encoding)
		# dictgen's ParseDictFile does not seem to support glossary info / metedata
		self._resDir = filename + "_res"
		if not isdir(self._resDir):
			os.mkdir(self._resDir)

	def write(
		self,
	) -> "Generator[None, BaseEntry, None]":
		fileObj = self._file
		resDir = self._resDir
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				entry.save(resDir)
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
