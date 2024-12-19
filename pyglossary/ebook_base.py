# -*- coding: utf-8 -*-
# The MIT License (MIT)

# Copyright © 2012-2016 Alberto Pettarin (alberto@albertopettarin.it)
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com>

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

import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from os.path import join
from typing import TYPE_CHECKING, cast

from pyglossary.os_utils import indir, rmtree

if TYPE_CHECKING:
	import io
	from collections.abc import Generator
	from typing import Any

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = ["EbookWriter"]

log = logging.getLogger("pyglossary")


class GroupState:
	def __init__(self, writer: EbookWriter) -> None:
		self.writer = writer
		self.last_prefix = ""
		self.group_index = -1
		self.reset()

	def reset(self) -> None:
		self.first_word = ""
		self.last_word = ""
		self.group_contents: list[str] = []

	def is_new(self, prefix: str) -> bool:
		return bool(self.last_prefix) and prefix != self.last_prefix

	def add(self, entry: EntryType, prefix: str) -> None:
		word = entry.s_word
		defi = entry.defi
		if not self.first_word:
			self.first_word = word
		self.last_word = word
		self.last_prefix = prefix
		self.group_contents.append(self.writer.format_group_content(word, defi))


class EbookWriter:

	"""
	A class representing a generic ebook containing a dictionary.

	It can be used to output a MOBI or an EPUB 2 container.

	The ebook must have an OPF, and one or more group XHTML files.

	Optionally, it can have a cover image, an NCX TOC, an index XHTML file.

	The actual file templates are provided by the caller.
	"""

	_keep: bool = False
	_group_by_prefix_length: int = 2
	_include_index_page: bool = False
	_compress: bool = True
	_css: str = ""  # path to css file, or ""
	_cover_path: str = ""  # path to cover file, or ""

	CSS_CONTENTS = b""
	GROUP_XHTML_TEMPLATE = ""
	GROUP_XHTML_INDEX_LINK = ""

	GROUP_XHTML_WORD_DEFINITION_TEMPLATE = ""
	GROUP_XHTML_WORD_DEFINITION_JOINER = "\n"

	MIMETYPE_CONTENTS = ""
	CONTAINER_XML_CONTENTS = ""

	GROUP_START_INDEX = 2

	COVER_TEMPLATE = "{cover}"

	INDEX_XHTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8"
	standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
	"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
	<head>
		<title>{title}</title>
		<link rel="stylesheet" type="text/css" href="style.css" />
	</head>
	<body class="indexPage">
	<h1 class="indexTitle">{indexTitle}</h1>
	<p class="indexGroupss">
{links}
	</p>
	</body>
</html>"""
	INDEX_XHTML_LINK_TEMPLATE = (
		'   <span class="indexGroup"><a href="{ref}">{label}</a></span>'
	)

	INDEX_XHTML_LINK_JOINER = " &#8226;\n"

	OPF_MANIFEST_ITEM_TEMPLATE = (
		'  <item href="{ref}" id="{id}" media-type="{mediaType}" />'
	)

	OPF_SPINE_ITEMREF_TEMPLATE = '  <itemref idref="{id}" />'

	OPF_TEMPLATE = ""

	def __init__(
		self,
		glos: GlossaryType,
		escape_strings: bool = False,
		# ignore_synonyms=False,
		# flatten_synonyms=False,
	) -> None:
		self._glos = glos
		self._filename = ""

		self._escape_strings = escape_strings
		# self._ignore_synonyms = ignore_synonyms
		# self._flatten_synonyms = flatten_synonyms

		# Penelope's extra options:
		# "bookeen_collation_function": None,  # bookeen format
		# "bookeen_install_file": False,  # bookeen format
		# "group_by_prefix_merge_across_first": False,
		# "group_by_prefix_merge_min_size": 0,

		self._tmpDir = tempfile.mkdtemp()
		self.cover = ""
		self.files: list[dict[str, Any]] = []
		self.manifest_files: list[dict[str, str]] = []
		self._group_labels: list[str] = []

	def finish(self) -> None:
		self._filename = ""

	def myOpen(self, fname: str, mode: str) -> io.IOBase:
		return cast(
			"io.IOBase",
			open(
				join(self._tmpDir, fname),
				mode=mode,
			),
		)

	def add_file(
		self,
		relative_path: str,
		contents: bytes,
		mode: int | None = None,
	) -> None:
		if mode is None:
			mode = zipfile.ZIP_DEFLATED
		file_path = os.path.join(self._tmpDir, relative_path)
		with self.myOpen(file_path, "wb") as file_obj:
			file_obj.write(contents)
		self.files.append(
			{
				"path": relative_path,
				"mode": mode,
			},
		)

	def write_cover(self, cover_path: str) -> None:
		if not cover_path:
			return
		basename = os.path.basename(cover_path)
		with self.myOpen(cover_path, "rb") as cover_obj:
			cover = cover_obj.read()
		b = basename.lower()
		mimetype = "image/jpeg"
		if b.endswith(".png"):
			mimetype = "image/png"
		elif b.endswith(".gif"):
			mimetype = "image/gif"
		self.add_file_manifest("OEBPS/" + basename, basename, cover, mimetype)
		self.cover = basename

	def write_css(self, custom_css_path_absolute: str) -> None:
		css = self.CSS_CONTENTS
		if custom_css_path_absolute:
			try:
				with self.myOpen(custom_css_path_absolute, "rb") as css_obj:
					css = css_obj.read()  # NESTED 4
			except Exception:
				log.exception("")
		if not css:
			return
		self.add_file_manifest("OEBPS/style.css", "style.css", css, "text/css")

	def add_file_manifest(
		self,
		relative_path: str,
		id_: str,
		contents: bytes,
		mimetype: str,
	) -> None:
		self.add_file(relative_path, contents)
		self.manifest_files.append(
			{
				"path": relative_path,
				"id": id_,
				"mimetype": mimetype,
			},
		)

	def get_group_xhtml_file_name_from_index(self, index: int) -> str:
		if index < self.GROUP_START_INDEX:
			# or index >= groupCount + self.GROUP_START_INDEX:
			# number of groups are not known, FIXME
			# so we can191 not say if the current group is the last or not
			return "#groupPage"
		return f"g{index:06d}.xhtml"

	def _add_group(
		self,
		group_labels: list[str],
		state: GroupState,
	) -> None:
		if not state.last_prefix:
			return
		state.group_index += 1
		index = state.group_index + self.GROUP_START_INDEX
		group_label = state.last_prefix
		if group_label != "SPECIAL":
			group_label = state.first_word + "&#8211;" + state.last_word
		log.debug(f"add_group: {state.group_index}, {state.last_prefix!r}")
		group_labels.append(group_label)
		previous_link = self.get_group_xhtml_file_name_from_index(index - 1)
		next_link = self.get_group_xhtml_file_name_from_index(index + 1)
		group_xhtml_path = self.get_group_xhtml_file_name_from_index(index)
		contents = self.GROUP_XHTML_TEMPLATE.format(
			title=group_label,
			group_title=group_label,
			previous_link=previous_link,
			index_link=(
				self.GROUP_XHTML_INDEX_LINK if self._include_index_page else ""
			),
			next_link=next_link,
			group_contents=self.GROUP_XHTML_WORD_DEFINITION_JOINER.join(
				state.group_contents,
			),
		).encode("utf-8")
		self.add_file_manifest(
			"OEBPS/" + group_xhtml_path,
			group_xhtml_path,
			contents,
			"application/xhtml+xml",
		)

	def write_data_entry(self, entry: EntryType) -> None:
		if entry.getFileName() == "style.css":
			self.add_file_manifest(
				"OEBPS/style.css",
				"style.css",
				entry.data,
				"text/css",
			)

	def get_prefix(self, word: str) -> str:
		raise NotImplementedError

	def write_groups(self) -> Generator[None, EntryType, None]:
		# TODO: rtl=False option
		# TODO: handle alternates better (now shows word1|word2... in title)

		group_labels: list[str] = []

		state = GroupState(self)
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				self.write_data_entry(entry)
				continue

			prefix = self.get_prefix(entry.s_word)
			if state.is_new(prefix):
				self._add_group(group_labels, state)
				state.reset()

			state.add(entry, prefix)

		self._add_group(group_labels, state)

		self._group_labels = group_labels

	def format_group_content(
		self,
		word: str,
		defi: str,
		variants: list[str] | None = None,  # noqa: ARG002
	) -> str:
		return self.GROUP_XHTML_WORD_DEFINITION_TEMPLATE.format(
			headword=self.escape_if_needed(word),
			definition=self.escape_if_needed(defi),
		)

	def escape_if_needed(self, string: str) -> str:
		if not self._escape_strings:
			return string

		return (
			string.replace("&", "&amp;")
			.replace('"', "&quot;")
			.replace("'", "&apos;")
			.replace(">", "&gt;")
			.replace("<", "&lt;")
		)

	def write_index(self, group_labels: list[str]) -> None:
		"""group_labels: a list of labels."""
		links = []
		for label_i, label in enumerate(group_labels):
			ref = self.get_group_xhtml_file_name_from_index(
				self.GROUP_START_INDEX + label_i,
			)
			links.append(
				self.INDEX_XHTML_LINK_TEMPLATE.format(
					ref=ref,
					label=label,
				),
			)
		links_str = self.INDEX_XHTML_LINK_JOINER.join(links)
		title = self._glos.getInfo("name")
		contents = self.INDEX_XHTML_TEMPLATE.format(
			title=title,
			indexTitle=title,
			links=links_str,
		).encode("utf-8")
		self.add_file_manifest(
			"OEBPS/index.xhtml",
			"index.xhtml",
			contents,
			"application/xhtml+xml",
		)

	def get_opf_contents(  # noqa: F811
		self,
		manifest_contents: str,
		spine_contents: str,
	) -> bytes:
		cover = ""
		if self.cover:
			cover = self.COVER_TEMPLATE.format(cover=self.cover)

		creationDate = datetime.now().strftime("%Y-%m-%d")

		return self.OPF_TEMPLATE.format(
			identifier=self._glos.getInfo("uuid"),
			sourceLang=self._glos.sourceLangName,
			targetLang=self._glos.targetLangName,
			title=self._glos.getInfo("name"),
			creator=self._glos.author,
			copyright=self._glos.getInfo("copyright"),
			creationDate=creationDate,
			cover=cover,
			manifest=manifest_contents,
			spine=spine_contents,
		).encode("utf-8")

	def write_opf(self) -> None:
		manifest_lines = []
		spine_lines = []
		for mi in self.manifest_files:
			manifest_lines.append(
				self.OPF_MANIFEST_ITEM_TEMPLATE.format(
					ref=mi["id"],
					id=mi["id"],
					mediaType=mi["mimetype"],
				),
			)
			if mi["mimetype"] == "application/xhtml+xml":
				spine_lines.append(
					self.OPF_SPINE_ITEMREF_TEMPLATE.format(
						id=mi["id"],  # NESTED 4
					),
				)

		manifest_contents = "\n".join(manifest_lines)
		spine_contents = "\n".join(spine_lines)
		opf_contents = self.get_opf_contents(
			manifest_contents,
			spine_contents,
		)

		self.add_file("OEBPS/content.opf", opf_contents)

	def write_ncx(self, group_labels: list[str]) -> None:
		"""
		write_ncx.

		only for epub.
		"""

	def open(self, filename: str) -> None:
		self._filename = filename

	def _doZip(self) -> None:
		with zipfile.ZipFile(
			self._filename,
			mode="w",
			compression=zipfile.ZIP_DEFLATED,
		) as zipFp:
			for fileDict in self.files:
				zipFp.write(
					fileDict["path"],
					compress_type=fileDict["mode"],
				)
		if not self._keep:
			rmtree(self._tmpDir)

	def write(self) -> Generator[None, EntryType, None]:
		filename = self._filename
		# self._group_by_prefix_length
		# self._include_index_page
		css = self._css
		cover_path = self._cover_path

		with indir(self._tmpDir):
			if cover_path:
				cover_path = os.path.abspath(cover_path)

			if css:
				css = os.path.abspath(css)

			os.makedirs("META-INF")
			os.makedirs("OEBPS")

			if self.MIMETYPE_CONTENTS:
				self.add_file(
					"mimetype",
					self.MIMETYPE_CONTENTS.encode("utf-8"),
					mode=zipfile.ZIP_STORED,
				)
			if self.CONTAINER_XML_CONTENTS:
				self.add_file(
					"META-INF/container.xml",
					self.CONTAINER_XML_CONTENTS.encode("utf-8"),
				)

			try:
				self.write_cover(cover_path)
			except Exception:
				log.exception("")

			self.write_css(css)

			yield from self.write_groups()
			group_labels = self._group_labels

			if self._include_index_page:
				self.write_index(group_labels)

			self.write_ncx(group_labels)

			self.write_opf()

			if self._compress:
				self._doZip()
				return

			if self._keep:
				shutil.copytree(self._tmpDir, filename)
				return

			if os.sep == "\\":
				shutil.copytree(self._tmpDir, filename)
				self._glos.addCleanupPath(self._tmpDir)
				return

			shutil.move(self._tmpDir, filename)
