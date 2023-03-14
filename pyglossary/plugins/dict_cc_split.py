# -*- coding: utf-8 -*-

import html
import typing
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
	import sqlite3

from pyglossary.core import log
from pyglossary.glossary_types import EntryType, GlossaryType

enable = True
lname = "dict_cc_split"
format = 'Dictcc_split'
description = 'Dict.cc (SQLite3) - Split'
extensions = ()
extensionCreate = ".db"
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/Dict.cc"
website = (
	"https://play.google.com/store/apps/details?id=cc.dict.dictcc",
	"dict.cc dictionary - Google Play",
)


class Reader(object):
	def __init__(self: "typing.Self", glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self: "typing.Self") -> None:
		self._filename = ''
		self._con: "sqlite3.Connection | None" = None
		self._cur: "sqlite3.Cursor | None" = None

	def open(self: "typing.Self", filename: str) -> None:
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._glos.setDefaultDefiFormat("m")

	def __len__(self: "typing.Self") -> int:
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute("select count(*) * 2 from main_ft")
		return self._cur.fetchone()[0]

	def iterRows(
		self: "typing.Self",
		column1: str,
		column2: str,
	) -> "Iterator[tuple[str, str, str]]":
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

	def _iterOneDirection(
		self: "typing.Self",
		column1: str,
		column2: str,
	) -> "Iterator[EntryType]":
		for word, defi, entry_type in self.iterRows(column1, column2):
			if entry_type:
				word = f"{word} {{{entry_type}}}"
			yield self._glos.newEntry(word, defi, defiFormat="m")

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		yield from self._iterOneDirection("term1", "term2")
		yield from self._iterOneDirection("term2", "term1")

	def close(self: "typing.Self") -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
