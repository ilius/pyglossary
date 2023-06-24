# -*- coding: utf-8 -*-
#
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
from typing import TYPE_CHECKING, Iterator, Sequence

if TYPE_CHECKING:
	from lxml.html import HtmlElement as Element

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	BoolOption,
	Option,
)
from pyglossary.text_utils import toStr
from pyglossary.xdxf.transform import XdxfTransformer
from pyglossary.xdxf.xsl_transform import XslXdxfTransformer

enable = True
lname = "xdxf_lax"
format = "XdxfLax"
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
optionsProp: "dict[str, Option]" = {
	"html": BoolOption(comment="Entries are HTML"),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
}


class Reader(object):
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

	def __init__(self: "typing.Self", glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file = None
		self._encoding = "utf-8"
		self._htmlTr = None
		self._re_span_k = re.compile(
			'<span class="k">[^<>]*</span>(<br/>)?',
		)

	def readUntil(self, untilByte: bytes) -> bytes:
		_file = self._file
		buf = b""
		while True:
			tmp = _file.read(100)
			if not tmp:
				break
			buf += tmp
			index = buf.rfind(untilByte)
			if index < 0:
				continue
			_file.seek(_file.tell() - len(buf) + index)
			return index, buf[:index]
		return -1, buf

	def readMetadata(self: "typing.Self"):
		from lxml.etree import XML

		descStart, _ = self.readUntil(b"<description")
		if descStart < 0:
			return

		descEnd, desc = self.readUntil(b"</description>")
		if descEnd < 0:
			return

		desc += b"</description>"
		xml = XML(desc)
		for elem in xml.iterchildren():
			if not elem.text:
				log.warning(f"empty tag <{elem.tag}>")
				continue
			key = self.infoKeyMap.get(elem.tag, elem.tag)
			self._glos.setInfo(key, elem.text)

	def open(self: "typing.Self", filename: str) -> None:
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
		self._glos.setInfo("input_file_size", f"{self._fileSize}")

	def __len__(self: "typing.Self") -> int:
		return 0

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
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
				article = fromstring(s_article)
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
				defi = tostring(article, encoding=self._encoding)
				defi = defi[4:-5].decode(self._encoding).strip()
				defiFormat = "x"

			# log.info(f"{defi=}, {words=}")
			yield self._glos.newEntry(
				words,
				defi,
				defiFormat=defiFormat,
				byteProgress=(self._file.tell(), self._fileSize),
			)


	def close(self: "typing.Self") -> None:
		if self._file:
			self._file.close()
			self._file = None

	def tostring(
		self: "typing.Self",
		elem: "Element",
	) -> str:
		from lxml.html import tostring
		return tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def titles(self: "typing.Self", article: "Element") -> "list[str]":
		"""

		:param article: <ar> tag
		:return: (title (str) | None, alternative titles (set))
		"""
		print(type(article))
		from itertools import combinations
		titles: "list[str]" = []
		for title_element in article.findall("k"):
			if title_element.text is None:
				# TODO: look for <opt> tag?
				log.warning(f"empty title element: {self.tostring(title_element)}")
				continue
			n_opts = len([c for c in title_element if c.tag == "opt"])
			if n_opts:
				for j in range(n_opts + 1):
					for comb in combinations(list(range(n_opts)), j):
						titles.append(self._mktitle(title_element, comb))
			else:
				titles.append(self._mktitle(title_element))

		return titles

	def _mktitle(
		self: "typing.Self",
		title_element: "Element",
		include_opts: "Sequence | None" = None,
	) -> str:
		if include_opts is None:
			include_opts = ()
		title = title_element.text
		opt_i = -1
		for c in title_element:
			if c.tag == "nu" and c.tail:
				if title:
					title += c.tail
				else:
					title = c.tail
			if c.tag == "opt":
				opt_i += 1
				if opt_i in include_opts:
					if title:
						title += c.text
					else:
						title = c.text
				if c.tail:
					if title:
						title += c.tail
					else:
						title = c.tail
		return title.strip()
