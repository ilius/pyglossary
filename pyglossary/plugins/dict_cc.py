# -*- coding: utf-8 -*-
from __future__ import annotations

import html
from operator import itemgetter
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
	import sqlite3
	from collections.abc import Callable, Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.lxml_types import Element, T_htmlfile
	from pyglossary.option import Option


from pyglossary.core import log

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
lname = "dict_cc"
name = "Dictcc"
description = "Dict.cc (SQLite3)"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/Dict.cc"
website = (
	"https://play.google.com/store/apps/details?id=cc.dict.dictcc",
	"dict.cc dictionary - Google Play",
)
optionsProp: dict[str, Option] = {}


class Reader:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._con: sqlite3.Connection | None = None
		self._cur: sqlite3.Cursor | None = None

	def open(self, filename: str) -> None:
		from sqlite3 import connect

		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._glos.setDefaultDefiFormat("h")

	def __len__(self) -> int:
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute(
			"select count(distinct term1)+count(distinct term2) from main_ft",
		)
		return self._cur.fetchone()[0]

	@staticmethod
	def makeList(
		hf: T_htmlfile,
		input_elements: list[Element],
		processor: Callable,
		single_prefix: str = "",
		skip_single: bool = True,
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
		if not input_elements:
			return

		if skip_single and len(input_elements) == 1:
			hf.write(single_prefix)
			processor(hf, input_elements[0])
			return

		with hf.element("ol"):
			for el in input_elements:
				with hf.element("li"):
					processor(hf, el)

	@staticmethod
	def makeGroupsList(
		hf: T_htmlfile,
		groups: list[tuple[str, str]],
		processor: Callable[[T_htmlfile, tuple[str, str]], None],
		single_prefix: str = "",
		skip_single: bool = True,
	) -> None:
		"""Wrap elements into <ol> if more than one element."""
		if not groups:
			return

		if skip_single and len(groups) == 1:
			hf.write(single_prefix)
			processor(hf, groups[0])
			return

		with hf.element("ol"):
			for el in groups:
				with hf.element("li"):
					processor(hf, el)

	def writeSense(  # noqa: PLR6301
		self,
		hf: T_htmlfile,
		row: tuple[str, str],
	) -> None:
		from lxml import etree as ET

		trans, entry_type = row
		if entry_type:
			with hf.element("i"):
				hf.write(f"{entry_type}")  # noqa: FURB183
			hf.write(ET.Element("br"))
		try:
			hf.write(trans + " ")
		except Exception as e:
			log.error(f"error in writing {trans!r}, {e}")
			hf.write(repr(trans) + " ")
		else:
			with hf.element("big"):
				with hf.element("a", href=f"bword://{trans}"):
					hf.write("⏎")

	def iterRows(
		self,
		column1: str,
		column2: str,
	) -> Iterator[tuple[str, str, str]]:
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute(
			f"select {column1}, {column2}, entry_type from main_ft"
			f" order by {column1}",
		)
		for row in self._cur.fetchall():
			term1 = row[0]
			term2 = row[1]
			try:
				term1 = html.unescape(term1)
			except Exception as e:
				log.error(f"html.unescape({term1!r}) -> {e}")
			try:
				term2 = html.unescape(term2)
			except Exception as e:
				log.error(f"html.unescape({term2!r}) -> {e}")
			yield term1, term2, row[2]

	def parseGender(self, headword: str) -> tuple[str | None, str]:  # noqa: PLR6301
		# {m}	masc	masculine	German: maskulin
		# {f}	fem 	feminine	German: feminin
		# {n}	neut	neutral		German: neutral
		# { }	????
		i = headword.find(" {")
		if i <= 0:
			return None, headword
		if len(headword) < i + 4:
			return None, headword
		if headword[i + 3] != "}":
			return None, headword
		g = headword[i + 2]
		gender = None
		if g == "m":
			gender = "masculine"
		elif g == "f":
			gender = "feminine"
		elif g == "n":
			gender = "neutral"
		else:
			log.warning(f"invalid gender {g!r}")
			return None, headword
		headword = headword[:i] + headword[i + 4 :]
		return gender, headword

	def _iterOneDirection(
		self,
		column1: str,
		column2: str,
	) -> Iterator[EntryType]:
		from io import BytesIO
		from itertools import groupby

		from lxml import etree as ET

		glos = self._glos
		for headwordEscaped, groupsOrig in groupby(
			self.iterRows(column1, column2),
			key=itemgetter(0),
		):
			headword = html.unescape(headwordEscaped)
			groups: list[tuple[str, str]] = [
				(term2, entry_type) for _, term2, entry_type in groupsOrig
			]
			f = BytesIO()
			gender, headword = self.parseGender(headword)
			with ET.htmlfile(f, encoding="utf-8") as hf:
				with hf.element("div"):
					if gender:
						with hf.element("i"):
							hf.write(gender)
						hf.write(ET.Element("br"))
					self.makeGroupsList(
						cast("T_htmlfile", hf),
						groups,
						self.writeSense,
					)
			defi = f.getvalue().decode("utf-8")
			yield glos.newEntry(headword, defi, defiFormat="h")

	def __iter__(self) -> Iterator[EntryType]:
		yield from self._iterOneDirection("term1", "term2")
		yield from self._iterOneDirection("term2", "term1")

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
