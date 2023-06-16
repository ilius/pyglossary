# -*- coding: utf-8 -*-
# xdxf/__init__.py
"""xdxf file format reader and utils to convert xdxf to html."""
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
	from lxml.etree import Element

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
from pyglossary.xdxf_transform import (
	XdxfTransformer,
	XslXdxfTransformer,
)

enable = True
lname = "xdxf"
format = "Xdxf"
description = "XDXF (.xdxf)"
extensions = (".xdxf",)
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


"""
new format
<xdxf ...>
	<meta_info>
		<!--All meta information about the dictionary: its title, author etc.!-->
		<basename>...</basename>
		<full_title>...</full_title>
		<description>...</description>
	</meta_info>
	<lexicon>
		<ar>article 1</ar>
		<ar>article 2</ar>
		<ar>article 3</ar>
		<ar>article 4</ar>
		...
	</lexicon>
</xdxf>

old format
<xdxf ...>
	<full_name>...</full_name>
	<description>...</description>
	<ar>article 1</ar>
	<ar>article 2</ar>
	<ar>article 3</ar>
	<ar>article 4</ar>
	...
</xdxf>
"""


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

	def open(self: "typing.Self", filename: str) -> None:
		# <!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">
		from lxml import etree as ET
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

		context = ET.iterparse(
			cfile,
			events=("end",),
		)
		for _, elem in context:
			if elem.tag in ("meta_info", "ar", "k", "abr", "dtrn"):
				break
			# every other tag before </meta_info> or </ar> is considered info
			if elem.tag in ("abbr_def",):
				continue
			if not elem.text:
				log.warning(f"empty tag <{elem.tag}>")
				continue
			key = self.infoKeyMap.get(elem.tag, elem.tag)
			self._glos.setInfo(key, elem.text)

		del context

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("XDXF Reader: file is not seekable")
			self._file.close()
			self._file = compressionOpen(self._filename, mode="rb")

	def __len__(self: "typing.Self") -> int:
		return 0

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		from lxml import etree as ET
		from lxml.etree import tostring

		context = ET.iterparse(
			self._file,
			events=("end",),
			tag="ar",
		)
		for _, article in context:
			article.tail = None
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
			# clean up preceding siblings to save memory
			# this reduces memory usage from ~64 MB to ~30 MB
			while article.getprevious() is not None:
				del article.getparent()[0]

	def close(self: "typing.Self") -> None:
		if self._file:
			self._file.close()
			self._file = None

	def read_metadata_old(self: "typing.Self") -> None:
		full_name = self._xdxf.find("full_name").text
		desc = self._xdxf.find("description").text
		if full_name:
			self._glos.setInfo("name", full_name)
		if desc:
			self._glos.setInfo("description", desc)

	def read_metadata_new(self: "typing.Self") -> None:
		meta_info = self._xdxf.find("meta_info")
		if meta_info is None:
			raise ValueError("meta_info not found")

		title = meta_info.find("full_title").text
		if not title:
			title = meta_info.find("title").text
		desc = meta_info.find("description").text

		if title:
			self._glos.setInfo("name", title)
		if desc:
			self._glos.setInfo("description", desc)

	def tostring(
		self: "typing.Self",
		elem: "Element",
	) -> str:
		from lxml import etree as ET
		return ET.tostring(
			elem,
			method="html",
			pretty_print=True,
		).decode("utf-8").strip()

	def titles(self: "typing.Self", article: "Element") -> "list[str]":
		"""

		:param article: <ar> tag
		:return: (title (str) | None, alternative titles (set))
		"""
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
