# -*- coding: utf-8 -*-
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

from __future__ import annotations

import html
import html.entities
import re
import zipfile
from os.path import abspath, dirname, isfile, join, splitext
from typing import TYPE_CHECKING, cast

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.io_utils import nullTextIO
from pyglossary.os_utils import indir
from pyglossary.text_reader import TextFilePosWrapper

from .title import TitleTransformer
from .transform import Transformer

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType


__all__ = ["Reader"]

htmlEntityPattern = re.compile(r"&#?\w+;")


def _unescape(text: str) -> str:
	def fixup(m: re.Match) -> str:
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


# precompiled regexs
_re_wrapped_in_quotes = re.compile("^(\\'|\")(.*)(\\1)$")


def _unwrap_quotes(s: str) -> str:
	return _re_wrapped_in_quotes.sub("\\2", s)


class Reader:
	useByteProgress = True
	compressions = stdCompressions + ("dz",)

	_encoding: str = ""
	_audio: bool = True
	_example_color: str = "steelblue"
	_abbrev: str = "hover"

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dirPath = ""
		self._file: io.TextIOBase = nullTextIO
		self._fileSize = 0
		self._bufferLine = ""
		self._resFileSet: set[str] = set()
		self._includes: list[Reader] = []
		self._abbrevDict: dict[str, str] = {}

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
			abbrev=self._abbrev,
			abbrevDict=self._abbrevDict if self._abbrev else None,
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
		self._dirPath = abspath(dirname(self._filename))

		encoding = self._encoding
		if not encoding:
			encoding = self.detectEncoding()
		cfile = cast(
			"io.TextIOBase",
			compressionOpen(
				filename,
				dz=True,
				mode="rt",
				encoding=encoding,
			),
		)

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
			line = line.rstrip().lstrip("\ufeff")  # noqa: B005, PLW2901
			# \ufeff -> https://github.com/ilius/pyglossary/issues/306
			if not line:
				continue
			if not line.startswith("#"):
				self._bufferLine = line
				break
			self.processHeaderLine(line)

		if self._abbrev:
			self.loadAbbrevFile()

	def loadAbbrevFile(self) -> None:
		baseName, _ = splitext(self._filename)
		abbrevName = baseName + "_abrv.dsl"
		if not isfile(abbrevName):
			return
		log.info(f"Reading abbrevation file {abbrevName!r}")
		reader = Reader(self._glos)
		reader.open(abbrevName)
		for entry in reader:
			for word in entry.l_term:
				self._abbrevDict[word] = entry.defi
		reader.close()

	def detectEncoding(self) -> str:
		for testEncoding in (
			"utf-8",
			"utf-16",
			"utf-16-le",
			"utf-16-be",
		):
			with compressionOpen(
				self._filename,
				dz=True,
				mode="rt",
				encoding=testEncoding,
			) as fileObj:
				try:
					for _ in range(10):
						fileObj.readline()
				except (UnicodeDecodeError, UnicodeError):
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
		self._glos.setInfo(key, _unwrap_quotes(value))

	def processHeaderLine(self, line: str) -> None:
		if line.startswith("#NAME"):
			self.setInfo("name", _unwrap_quotes(line[6:].strip()))
		elif line.startswith("#INDEX_LANGUAGE"):
			self._glos.sourceLangName = _unwrap_quotes(line[16:].strip())
		elif line.startswith("#CONTENTS_LANGUAGE"):
			self._glos.targetLangName = _unwrap_quotes(line[19:].strip())
		elif line.startswith("#INCLUDE"):
			self.processInclude(_unwrap_quotes(line[9:].strip()))

	def processInclude(self, filename: str) -> None:
		reader = Reader(self._glos)
		reader._audio = self._audio
		reader._example_color = self._example_color
		with indir(self._dirPath):
			reader.open(filename)
		self._includes.append(reader)

	def _iterLines(self) -> Iterator[str]:
		if self._bufferLine:
			line = self._bufferLine
			self._bufferLine = ""
			yield line
		for line in self._file:
			yield line

	# @staticmethod
	# def sub_title_line(m: re.Match) -> str:
	# 	line = m.group(0)[1:-1]
	# 	line = line.replace("[']", "")  # FIXME
	# 	line = line.replace("[/']", "")
	# 	return line  # noqa: RET504

	def __iter__(self) -> Iterator[EntryType]:
		for reader in self._includes:
			yield from reader
			reader.close()

		term_lines: list[str] = []
		text_lines: list[str] = []
		for line in self._iterLines():
			if not line.strip():
				continue
			if line.startswith((" ", "\t")):  # text
				text_lines.append(line)
				continue

			# header or alt
			if text_lines:
				yield from self.parseEntryBlock(term_lines, text_lines)
				term_lines = []
				text_lines = []

			term_lines.append(line)

		if text_lines:
			yield from self.parseEntryBlock(term_lines, text_lines)

		resFileSet = self._resFileSet.copy()

		resZipPath = self._filename + ".files.zip"
		if isfile(resZipPath):
			with zipfile.ZipFile(resZipPath, mode="r") as zf:
				fnameList = zf.namelist()
				resFileSet -= set(fnameList)
				for fname in sorted(fnameList):
					with zf.open(fname) as file:
						data = file.read()
					yield self._glos.newDataEntry(fname, data)

		resDir = dirname(self._filename)
		for fname in sorted(resFileSet):
			fpath = join(resDir, fname)
			if not isfile(fpath):
				log.warning(f"resource file not found: {fname}")
				continue
			with open(fpath, mode="rb") as file:
				data = file.read()
			yield self._glos.newDataEntry(fname, data)

	def parseEntryBlock(  # noqa: PLR0912 Too many branches (14 > 12)
		self,
		term_lines: list[str],
		text_lines: list[str],
	) -> Iterator[EntryType]:
		terms: list[str] = []
		defiTitles: list[str] = []
		for line in term_lines:
			tr = TitleTransformer(line)
			res, err = tr.transform()
			if err:
				log.error(err)
				continue
			if res is None:
				log.error(f"res is None for line={line!r}")
				continue
			term = res.output.strip()
			terms.append(term)
			term2 = res.outputAlt.strip()
			if term2 != term:
				terms.append(term2)
			title = tr.title.strip()
			if title != term:
				defiTitles.append("<b>" + title + "</b>")

		main_text: str = ""
		subglos_list: list[tuple[str, str]] = []
		subglos_key, subglos_text = "", ""

		def add_subglos() -> None:
			nonlocal main_text, subglos_key, subglos_text
			subglos_list.append((subglos_key, subglos_text))
			main_text += f"\t[m2][ref]{subglos_key}[/ref]\n"
			subglos_key, subglos_text = "", ""

		for line in text_lines:
			s_line = line.strip()
			if s_line == "@":
				if subglos_key:
					add_subglos()
				continue
			if s_line.startswith("@ "):
				if subglos_key:
					add_subglos()
				subglos_key = s_line[2:].strip()
				continue
			if subglos_key:
				subglos_text += line
				continue
			main_text += line
		if subglos_key:
			add_subglos()

		if not terms:
			log.warning(f"No terms: {main_text=}")
			return

		defi = self.transform(
			text=main_text,
			header=terms[0],
		)
		if defiTitles:
			defi = "<br/>".join(defiTitles + [defi])

		byteProgress = (self._file.tell(), self._fileSize) if self._fileSize else None

		yield self._glos.newEntry(
			terms,
			defi,
			byteProgress=byteProgress,
		)

		for term, text in subglos_list:
			yield self._glos.newEntry(
				[term],
				self.transform(
					text=text,
					header=term,
				),
				byteProgress=byteProgress,
			)
