# -*- coding: utf-8 -*-
# dsl/__init__.py
# Read ABBYY Lingvo DSL dictionary format
#
# Copyright © 2013-2020 Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright © 2016 ivan tkachenko me@ratijas.tk
# Copyright © 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import html
import html.entities
import re
from collections.abc import Iterator
from os.path import dirname, isfile, join
from typing import TYPE_CHECKING, cast

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.io_utils import nullTextIO
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
	StrOption,
)
from pyglossary.text_reader import TextFilePosWrapper

from .title import TitleTransformer
from .transform import Transformer

if TYPE_CHECKING:
	import io

enable = True
lname = "dsl"
format = "ABBYYLingvoDSL"
description = "ABBYY Lingvo DSL (.dsl)"
extensions = (".dsl",)
extensionCreate = ".dsl"
singleFile = True
kind = "text"
wiki = "https://ru.wikipedia.org/wiki/ABBYY_Lingvo"
website = (
	"https://www.lingvo.ru/",
	"www.lingvo.ru",
)
optionsProp: "dict[str, Option]" = {
	"encoding": EncodingOption(),
	"audio": BoolOption(
		comment="Enable audio objects",
	),
	"example_color": StrOption(
		comment="Examples color",
	),
}

# ABBYY is a Russian company
# https://ru.wikipedia.org/wiki/ABBYY_Lingvo
# http://lingvo.helpmax.net/en/troubleshooting/dsl-compiler/compiling-a-dictionary/
# https://www.abbyy.com/news/abbyy-lingvo-80-dictionaries-to-suit-every-taste/


# {{{
# modified to work around codepoints that are not supported by `unichr`.
# http://effbot.org/zone/re-sub.htm#unescape-html
# January 15, 2003 | Fredrik Lundh


# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

htmlEntityPattern = re.compile(r"&#?\w+;")


def unescape(text: str) -> str:
	def fixup(m: "re.Match") -> str:
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				i = int(text[3:-1], 16) if text[:3] == "&#x" else int(text[2:-1])
			except ValueError:
				pass
			else:
				try:
					return chr(i)
				except ValueError:
					# f"\\U{i:08x}", but no fb"..."
					return (b"\\U%08x" % i).decode("unicode-escape")
		else:
			# named entity
			try:
				text = chr(html.entities.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text  # leave as is
	return htmlEntityPattern.sub(fixup, text)
# }}}


# precompiled regexs
re_wrapped_in_quotes = re.compile("^(\\'|\")(.*)(\\1)$")


def unwrap_quotes(s: str) -> str:
	return re_wrapped_in_quotes.sub("\\2", s)


class Reader:
	compressions = stdCompressions + ("dz",)

	_encoding: str = ""
	_audio: bool = True
	_example_color: str = "steelblue"

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._file: "io.TextIOBase" = nullTextIO
		self._fileSize = 0
		self._bufferLine = ""
		self._resFileSet: "set[str]" = set()

	def transform(
		self,
		text: str,
		header: str,
	) -> str:
		tr = Transformer(
			text,
			currentKey=header,
			audio=self._audio,
			exampleColor=self._example_color,
		)
		try:
			result, err = tr.transform()
		except Exception:
			log.exception(f"{text = }")
			return ""
		if err:
			log.error(f"error in transforming {text!r}: {err}")
			return ""
		if result is None:
			log.error(f"error in transforming {text!r}: result is None")
			return ""
		resText = result.output.strip()
		self._resFileSet.update(tr.resFileSet)
		return resText

	def close(self) -> None:
		self._file.close()
		self._file = nullTextIO

	def __len__(self) -> int:
		# FIXME
		return 0

	def open(
		self,
		filename: str,
	) -> None:
		self._filename = filename

		encoding = self._encoding
		if not encoding:
			encoding = self.detectEncoding()
		cfile = cast("io.TextIOBase", compressionOpen(
			filename,
			dz=True,
			mode="rt",
			encoding=encoding,
		))

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			# self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("DSL Reader: file is not seekable")

		self._file = TextFilePosWrapper(cfile, encoding)

		# read header
		for line in self._file:
			line = line.rstrip().lstrip('\ufeff')  # noqa: B005
			# \ufeff -> https://github.com/ilius/pyglossary/issues/306
			if not line:
				continue
			if not line.startswith("#"):
				self._bufferLine = line
				break
			self.processHeaderLine(line)

	def detectEncoding(self) -> str:
		for testEncoding in ("utf-8", "utf-16"):
			with compressionOpen(
				self._filename,
				dz=True,
				mode="rt",
				encoding=testEncoding,
			) as fileObj:
				try:
					for _ in range(10):
						fileObj.readline()
				except UnicodeDecodeError:
					log.info(f"Encoding of DSL file is not {testEncoding}")
					continue
				else:
					log.info(f"Encoding of DSL file detected: {testEncoding}")
					return testEncoding
		raise ValueError(
			"Could not detect encoding of DSL file"
			", specify it by: --read-options encoding=ENCODING",
		)

	def setInfo(self, key: str, value: str) -> None:
		self._glos.setInfo(key, unwrap_quotes(value))

	def processHeaderLine(self, line: str) -> None:
		if line.startswith("#NAME"):
			self.setInfo("name", unwrap_quotes(line[6:].strip()))
		elif line.startswith("#INDEX_LANGUAGE"):
			self._glos.sourceLangName = unwrap_quotes(line[16:].strip())
		elif line.startswith("#CONTENTS_LANGUAGE"):
			self._glos.targetLangName = unwrap_quotes(line[19:].strip())

	def _iterLines(self) -> "Iterator[str]":
		if self._bufferLine:
			line = self._bufferLine
			self._bufferLine = ""
			yield line
		for line in self._file:
			yield line

	def sub_title_line(self, m) -> str:
		line = m.group(0)[1:-1]
		line = line.replace("[']", "")  # FIXME
		line = line.replace("[/']", "")
		return line  # noqa: RET504

	def __iter__(self) -> "Iterator[EntryType]":
		term_lines: "list[str]" = []
		text_lines: "list[str]" = []
		for line in self._iterLines():
			if not line.strip():
				continue
			if line.startswith((" ", "\t")):  # text
				text_lines.append(line)
				continue

			# header or alt
			if text_lines:
				yield self.parseEntryBlock(term_lines, text_lines)
				term_lines = []
				text_lines = []

			term_lines.append(line)

		if text_lines:
			yield self.parseEntryBlock(term_lines, text_lines)

		resDir = dirname(self._filename)
		for fname in sorted(self._resFileSet):
			fpath = join(resDir, fname)
			if not isfile(fpath):
				log.warning(f"resource file not found: {fname}")
				continue
			with open(fpath, mode="rb") as _file:
				data = _file.read()
			yield self._glos.newDataEntry(fname, data)

	def parseEntryBlock(
		self,
		term_lines: "list[str]",
		text_lines: "list[str]",
	) -> EntryType:
		terms = []
		defiTitles = []
		for line in term_lines:
			tr = TitleTransformer(line)
			res, err = tr.transform()
			if err:
				log.error(err)
				continue
			if res is None:
				log.error("res is None for line={line!r}")
				continue
			term = res.output.strip()
			terms.append(term)
			term2 = res.outputAlt.strip()
			if term2 != term:
				terms.append(term2)
			title = tr.title.strip()
			if title != term:
				defiTitles.append("<b>" + title + "</b>")

		defi = self.transform(
			text="".join(text_lines),
			header=terms[0],
		)
		if defiTitles:
			defi = "<br/>".join(defiTitles + [defi])

		return self._glos.newEntry(
			terms,
			defi,
			byteProgress=(
				(self._file.tell(), self._fileSize)
				if self._fileSize
				else None
			),
		)
