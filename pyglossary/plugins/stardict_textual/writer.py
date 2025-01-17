# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from os.path import dirname, isdir, join
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	from collections.abc import Generator

	from lxml import builder

	from pyglossary.glossary_types import EntryType, WriterGlossaryType


from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)

__all__ = ["Writer"]


class Writer:
	_encoding: str = "utf-8"

	compressions = stdCompressions
	depends = {
		"lxml": "lxml",
	}

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resDir = ""

	def open(
		self,
		filename: str,
	) -> None:
		self._filename = filename
		self._resDir = join(dirname(self._filename), "res")
		self._file = compressionOpen(
			self._filename,
			mode="w",
			encoding=self._encoding,
		)

	def finish(self) -> None:
		self._file.close()

	def writeInfo(
		self,
		maker: builder.ElementMaker,
		pretty: bool,
	) -> None:
		from lxml import etree as ET

		glos = self._glos

		desc = glos.getInfo("description")
		copyright_ = glos.getInfo("copyright")
		if copyright_:
			desc = f"{copyright_}\n{desc}"
		publisher = glos.getInfo("publisher")
		if publisher:
			desc = f"Publisher: {publisher}\n{desc}"

		info = maker.info(
			maker.version("3.0.0"),
			maker.bookname(glos.getInfo("name")),
			maker.author(glos.getInfo("author")),
			maker.email(glos.getInfo("email")),
			maker.website(glos.getInfo("website")),
			maker.description(desc),
			maker.date(glos.getInfo("creationTime")),
			maker.dicttype(""),
		)
		file = self._file
		file.write(
			cast(
				"bytes",
				ET.tostring(
					info,
					encoding=self._encoding,
					pretty_print=pretty,
				),
			).decode(self._encoding)
			+ "\n",
		)

	def writeDataEntry(
		self,
		maker: builder.ElementMaker,  # noqa: ARG002
		entry: EntryType,
	) -> None:
		entry.save(self._resDir)
		# TODO: create article tag with "definition-r" in it?
		# or just save the file to res/ directory? or both?
		# article = maker.article(
		# 	maker.key(entry.s_word),
		# 	maker.definition_r(
		# 		ET.CDATA(entry.defi),
		# 		**{"type": ext})
		# 	)
		# )

	def write(self) -> Generator[None, EntryType, None]:
		from lxml import builder
		from lxml import etree as ET

		file = self._file
		encoding = self._encoding
		maker = builder.ElementMaker()

		file.write(
			"""<?xml version="1.0" encoding="UTF-8" ?>
<stardict xmlns:xi="http://www.w3.org/2003/XInclude">
""",
		)

		self.writeInfo(maker, pretty=True)

		if not isdir(self._resDir):
			os.mkdir(self._resDir)

		pretty = True
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				self.writeDataEntry(maker, entry)
				continue
			entry.detectDefiFormat()
			article = maker.article(
				maker.key(entry.l_word[0]),
			)
			for alt in entry.l_word[1:]:
				article.append(maker.synonym(alt))
			article.append(
				maker.definition(
					ET.CDATA(entry.defi),
					type=entry.defiFormat,
				),
			)
			ET.indent(article, space="")
			articleStr = cast(
				"bytes",
				ET.tostring(
					article,
					pretty_print=pretty,
					encoding=encoding,
				),
			).decode(encoding)
			# for some reason, "´k" becomes " ́k" (for example) # noqa: RUF003
			# stardict-text2bin tool also does this.
			# https://en.wiktionary.org/wiki/%CB%88#Translingual
			self._file.write(articleStr + "\n")

		file.write("</stardict>")

		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)
