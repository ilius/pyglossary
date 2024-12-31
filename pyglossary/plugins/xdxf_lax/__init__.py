# -*- coding: utf-8 -*-
#
from __future__ import annotations

"""Lax implementation of xdxf reader."""
#
# Copyright © 2023 Saeed Rasooli
# Copyright © 2016 ivan tkachenko me@ratijas.tk
#
# some parts of this file include code from:
# Aard Dictionary Tools <http://aarddict.org>.
# Copyright © 2008-2009  Igor Tkach
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

import re
import typing
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator, Sequence

	from lxml.html import HtmlElement as Element

	from pyglossary.glossary_types import EntryType, GlossaryType

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.io_utils import nullBinaryIO
from pyglossary.option import (
	BoolOption,
	Option,
)
from pyglossary.text_utils import toStr
from pyglossary.xdxf.transform import XdxfTransformer
from pyglossary.xdxf.xsl_transform import XslXdxfTransformer

__all__ = [
	"Reader",
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
lname = "xdxf_lax"
name = "XdxfLax"
description = "XDXF Lax (.xdxf)"
extensions = ()
extensionCreate = ".xdxf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/XDXF"
website = (
	"https://github.com/soshial/xdxf_makedict/tree/master/format_standard",
	"XDXF standard - @soshial/xdxf_makedict",
)
optionsProp: dict[str, Option] = {
	"html": BoolOption(comment="Entries are HTML"),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
}


if TYPE_CHECKING:

	class TransformerType(typing.Protocol):
		def transform(self, article: Element) -> str: ...


class Reader:
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_html: bool = True
	_xsl: bool = False

	infoKeyMap = {
		"full_name": "name",
		"full_title": "name",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.IOBase = nullBinaryIO
		self._encoding = "utf-8"
		self._htmlTr: TransformerType | None = None
		self._re_span_k = re.compile(
			'<span class="k">[^<>]*</span>(<br/>)?',
		)

	def readUntil(self, untilByte: bytes) -> tuple[int, bytes]:
		file = self._file
		buf = b""
		while True:
			tmp = file.read(100)
			if not tmp:
				break
			buf += tmp
			index = buf.find(untilByte)
			if index < 0:
				continue
			file.seek(file.tell() - len(buf) + index)
			return index, buf[:index]
		return -1, buf

	def _readOneMetadata(self, tag: str, infoKey: str) -> None:
		from lxml.etree import XML

		endTag = f"</{tag}>".encode("ascii")
		descStart, _ = self.readUntil(f"<{tag}>".encode("ascii"))
		if descStart < 0:
			log.warning(f"did not find {tag} open")
			return

		descEnd, desc = self.readUntil(endTag)
		if descEnd < 0:
			log.warning(f"did not find {tag} close")
			return

		desc += endTag
		elem = XML(desc)
		if elem.text:
			self._glos.setInfo(infoKey, elem.text)

	def readMetadata(self) -> None:
		file = self._file
		pos = file.tell()
		self._readOneMetadata("full_name", "title")
		file.seek(pos)
		self._readOneMetadata("description", "description")

	def open(self, filename: str) -> None:
		# <!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">
		self._filename = filename
		if self._html:
			if self._xsl:
				self._htmlTr = XslXdxfTransformer(encoding=self._encoding)
			else:
				self._htmlTr = XdxfTransformer(encoding=self._encoding)
			self._glos.setDefaultDefiFormat("h")
		else:
			self._glos.setDefaultDefiFormat("x")

		cfile = self._file = compressionOpen(self._filename, mode="rb")

		self.readMetadata()

		cfile.seek(0, 2)
		self._fileSize = cfile.tell()
		cfile.seek(0)
		self._glos.setInfo("input_file_size", str(self._fileSize))

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType]:
		from lxml.html import fromstring, tostring

		while True:
			start, _ = self.readUntil(b"<ar")
			if start < 0:
				break
			end, b_article = self.readUntil(b"</ar>")
			if end < 0:
				break
			b_article += b"</ar>"
			s_article = b_article.decode("utf-8")
			try:
				article = cast("Element", fromstring(s_article))
			except Exception as e:
				log.exception(s_article)
				raise e from None
			words = [toStr(w) for w in self.titles(article)]
			if self._htmlTr:
				defi = self._htmlTr.transform(article)
				defiFormat = "h"
				if len(words) == 1:
					defi = self._re_span_k.sub("", defi)
			else:
				b_defi = cast("bytes", tostring(article, encoding=self._encoding))
				defi = b_defi[4:-5].decode(self._encoding).strip()
				defiFormat = "x"

			# log.info(f"{defi=}, {words=}")
			yield self._glos.newEntry(
				words,
				defi,
				defiFormat=defiFormat,
				byteProgress=(self._file.tell(), self._fileSize),
			)

	def close(self) -> None:
		if self._file:
			self._file.close()
			self._file = nullBinaryIO

	@staticmethod
	def tostring(
		elem: Element,
	) -> str:
		from lxml.html import tostring

		return (
			tostring(
				elem,
				method="html",
				pretty_print=True,
			)
			.decode("utf-8")
			.strip()
		)

	def titles(self, article: Element) -> list[str]:
		"""
		:param article: <ar> tag
		:return: (title (str) | None, alternative titles (set))
		"""
		from itertools import combinations

		titles: list[str] = []
		for title_element in article.findall("k"):
			if title_element.text is None:
				# TODO: look for <opt> tag?
				log.warning(f"empty title element: {self.tostring(title_element)}")
				continue
			n_opts = len([c for c in title_element if c.tag == "opt"])
			if n_opts:
				titles += [
					self._mktitle(title_element, comb)
					for j in range(n_opts + 1)
					for comb in combinations(list(range(n_opts)), j)
				]
			else:
				titles.append(self._mktitle(title_element))

		return titles

	def _mktitle(  # noqa: PLR6301
		self,
		title_element: Element,
		include_opts: Sequence | None = None,
	) -> str:
		if include_opts is None:
			include_opts = ()
		title = title_element.text or ""
		opt_i = -1
		for c in title_element:
			if c.tag == "nu" and c.tail:
				if title:
					title += c.tail
				else:
					title = c.tail
			if c.tag == "opt" and c.text is not None:
				opt_i += 1
				if opt_i in include_opts:
					title += c.text
				if c.tail:
					title += c.tail
		return title.strip()
