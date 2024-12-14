# -*- coding: utf-8 -*-
# The MIT License (MIT)
# Copyright © 2020-2021 Saeed Rasooli <saeed.gnu@gmail.com>
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

import os
from os.path import isdir
from typing import TYPE_CHECKING

from pyglossary.core import exc_note, log, pip
from pyglossary.image_utils import extractInlineHtmlImages
from pyglossary.io_utils import nullTextIO
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)
from pyglossary.text_reader import TextGlossaryReader

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

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
lname = "kobo_dictfile"
name = "Dictfile"
description = "Kobo E-Reader Dictfile (.df)"
extensions = (".df",)
extensionCreate = ".df"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://pgaskin.net/dictutil/dictgen/#dictfile-format",
	"dictgen - dictutil",
)
# https://github.com/pgaskin/dictutil

optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"extract_inline_images": BoolOption(comment="Extract inline images"),
}


def fixWord(word: str) -> str:
	return word.replace("\n", " ")


def escapeDefi(defi: str) -> str:
	return defi.replace("\n@", "\n @").replace("\n:", "\n :").replace("\n&", "\n &")


class Reader(TextGlossaryReader):
	depends = {
		"mistune": "mistune==3.0.1",
	}

	_extract_inline_images: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		TextGlossaryReader.__init__(self, glos, hasInfo=False)

	def open(self, filename: str) -> None:
		try:
			import mistune  # type: ignore # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install mistune` to install")
			raise
		TextGlossaryReader.open(self, filename)
		self._glos.setDefaultDefiFormat("h")

	@classmethod
	def isInfoWord(cls, _word: str) -> bool:
		return False

	@classmethod
	def fixInfoWord(cls, _word: str) -> str:
		raise NotImplementedError

	def fixDefi(
		self,
		defi: str,
		html: bool,
	) -> tuple[str, list[tuple[str, str]] | None]:
		import mistune

		defi = (
			defi.replace("\n @", "\n@")
			.replace("\n :", "\n:")
			.replace("\n &", "\n&")
			.replace("</p><br />", "</p>")
			.replace("</p><br/>", "</p>")
			.replace("</p></br>", "</p>")
		)
		defi = defi.strip()
		if html:
			pass
		else:
			defi = mistune.html(defi)
		images: list[tuple[str, str]] | None = None
		if self._extract_inline_images:
			defi, images = extractInlineHtmlImages(
				defi,
				self._glos.tmpDataDir,
				fnamePrefix="",  # maybe f"{self._pos:06d}-"
			)
		return defi, images

	def nextBlock(
		self,
	) -> tuple[list[str], str, list[tuple[str, str]] | None]:
		words: list[str] = []
		defiLines: list[str] = []
		html = False

		while True:
			line = self.readline()
			if not line:
				break
			line = line.rstrip("\n\r")
			if line.startswith("@"):
				if words:
					self._bufferLine = line
					defi, images = self.fixDefi("\n".join(defiLines), html=html)
					return words, defi, images
				words = [line[1:].strip()]
				continue
			if line.startswith(": "):
				defiLines.append(line[2:])
				continue
			if line.startswith("::"):
				continue
			if line.startswith("&"):
				words.append(line[1:].strip())
				continue
			if line.startswith("<html>"):
				line = line[6:]
				html = True
			defiLines.append(line)

		if words:
			defi, images = self.fixDefi("\n".join(defiLines), html=html)
			return words, defi, images

		raise StopIteration


class Writer:
	_encoding: str = "utf-8"

	@staticmethod
	def stripFullHtmlError(entry: EntryType, error: str) -> None:
		log.error(f"error in stripFullHtml: {error}, words={entry.l_word!r}")

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._file: io.TextIOBase = nullTextIO
		glos.stripFullHtml(errorHandler=self.stripFullHtmlError)

	def finish(self) -> None:
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
	) -> Generator[None, EntryType, None]:
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
				defi = f"<html>{entry.defi}"

			fileObj.write(f"@ {fixWord(words[0])}\n")
			for alt in words[1:]:
				fileObj.write(f"& {fixWord(alt)}\n")
			fileObj.write(f"{escapeDefi(defi)}\n\n")
