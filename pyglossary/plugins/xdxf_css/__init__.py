# -*- coding: utf-8 -*-
# xdxf/__init__.py
from __future__ import annotations

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
from os.path import join
from typing import TYPE_CHECKING, cast

from pyglossary.option import BoolOption

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator, Sequence

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.lxml_types import Element
	from pyglossary.option import Option


from lxml import etree as ET

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log, rootDir
from pyglossary.io_utils import nullBinaryIO
from pyglossary.text_utils import toStr

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
lname = "xdxf_css"
name = "XdxfCss"
description = "XDXF with CSS and JS"
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

if TYPE_CHECKING:

	class TransformerType(typing.Protocol):
		def transform(self, article: Element) -> str: ...


class Reader:
	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	_html: bool = True

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
		self._has_added_css: bool = False
		self._has_added_js: bool = False
		self._abbr_defs_js: bytes

	def makeTransformer(self) -> None:
		from pyglossary.xdxf.css_js_transform import XdxfTransformer

		self._htmlTr = XdxfTransformer(encoding=self._encoding)

	def open(self, filename: str) -> None:  # noqa: PLR0912
		# <!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">

		self._filename = filename
		self.makeTransformer()
		self._glos.setDefaultDefiFormat("h")

		cfile = self._file = cast(
			"io.IOBase",
			compressionOpen(
				self._filename,
				mode="rb",
			),
		)

		context = ET.iterparse(  # type: ignore
			cfile,
			events=("end",),
		)
		abbr_defs: list[Element] = []
		for _, _elem in context:
			elem = cast("Element", _elem)
			if elem.tag in {"meta_info", "ar", "k", "abr", "dtrn"}:
				break
			# every other tag before </meta_info> or </ar> is considered info
			if elem.tag == "abbr_def":
				abbr_defs.append(elem)
				continue
			# in case of multiple <from> or multiple <to> tags, the last one
			# will be stored.
			# Very few formats support more than one language pair in their
			# metadata, so it's not very useful to have multiple
			if elem.tag == "from":
				for key, value in elem.attrib.items():
					if key.endswith("}lang"):
						self._glos.sourceLangName = value.split("-")[0]
						break
				continue
			if elem.tag == "to":
				for key, value in elem.attrib.items():
					if key.endswith("}lang"):
						self._glos.targetLangName = value.split("-")[0]
						break
				continue
			if not elem.text:
				if elem.tag != "br":
					log.warning(f"empty tag <{elem.tag}>")
				continue
			key = self.infoKeyMap.get(elem.tag, elem.tag)
			self._glos.setInfo(key, elem.text)
		self._abbr_defs_js = self.generate_abbr_js(abbr_defs)
		del context

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			self._glos.setInfo("input_file_size", str(self._fileSize))
		else:
			log.warning("XDXF Reader: file is not seekable")
			self._file.close()
			self._file = compressionOpen(self._filename, mode="rb")

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType]:
		context = ET.iterparse(  # type: ignore
			self._file,
			events=("end",),
			tag="ar",
		)

		if not self._has_added_css:
			self._has_added_css = True
			cssPath = join(rootDir, "pyglossary", "xdxf", "xdxf.css")
			with open(cssPath, "rb") as css_file:
				yield self._glos.newDataEntry("css/xdxf.css", css_file.read())

		if self._abbr_defs_js is not None and not self._has_added_js:
			self._has_added_js = True
			yield self._glos.newDataEntry("js/xdxf.js", self._abbr_defs_js)

		for _, _article in context:
			article = cast("Element", _article)
			article.tail = None
			words = [toStr(w) for w in self.titles(article)]

			defi = self._htmlTr.transform(article)
			defiFormat = "h"
			if len(words) == 1:
				defi = self._re_span_k.sub("", defi)

			defi = f"""<!DOCTYPE html>
<html>
	<head>
		<link rel="stylesheet" href="css/xdxf.css"/>
	</head>
	<body>
		{defi}
		<script type="text/javascript" src="js/xdxf.js"></script>
	</body>
</html>"""
			# log.info(f"{defi=}, {words=}")
			yield self._glos.newEntry(
				words,
				defi,
				defiFormat=defiFormat,
				byteProgress=(self._file.tell(), self._fileSize),
			)
			# clean up preceding siblings to save memory
			# this can reduce memory usage from 1 GB to ~25 MB
			parent = article.getparent()
			if parent is None:
				continue
			while article.getprevious() is not None:
				del parent[0]

	def close(self) -> None:
		self._file.close()
		self._file = nullBinaryIO

	def generate_abbr_js(self, abbr_defs: list[Element]) -> bytes:
		abbr_map_js = """const abbr_map = new Map();\n"""
		for abbr_def in abbr_defs:
			abbr_k_list: list[str] = []
			abbr_v_text = ""
			for child in abbr_def.xpath("child::node()"):
				if child.tag == "abbr_k":
					abbr_k_list.append(self._htmlTr.stringify_children(child))
				if child.tag == "abbr_v":
					abbr_v_text = self._htmlTr.stringify_children(child)
			# TODO escape apostrophes
			for abbr_k in abbr_k_list:
				if abbr_k and abbr_v_text:
					abbr_map_js += f"abbr_map.set('{abbr_k}', '{abbr_v_text}');\n"
		with open(join(rootDir, "pyglossary", "xdxf", "xdxf.js"), "rb") as js_file:
			return abbr_map_js.encode(encoding="utf-8") + js_file.read()

	@staticmethod
	def tostring(
		elem: Element,
	) -> str:
		return (
			ET.tostring(
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
