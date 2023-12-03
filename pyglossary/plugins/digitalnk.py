# -*- coding: utf-8 -*-

import html
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import sqlite3

	from pyglossary.glossary_types import EntryType, GlossaryType


enable = True
lname = "digitalnk"
format = 'DigitalNK'
description = 'DigitalNK (SQLite3, N-Korean)'
extensions = ()
extensionCreate = ".db"
kind = "binary"
wiki = ""
website = (
	"https://github.com/digitalprk/dicrs",
	"@digitalprk/dicrs",
)


class Reader:
	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._con: "sqlite3.Connection | None" = None
		self._cur: "sqlite3.Cursor | None" = None

	def open(self, filename: str) -> None:
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._glos.setDefaultDefiFormat("m")

	def __len__(self) -> int:
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute("select count(*) from dictionary")
		return self._cur.fetchone()[0]

	def __iter__(self) -> "Iterator[EntryType]":
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute(
			"select word, definition from dictionary"
			" order by word",
		)
		# iteration over self._cur stops after one entry
		# and self._cur.fetchone() returns None
		# no idea why!
		# https://github.com/ilius/pyglossary/issues/282
		# for row in self._cur:
		for row in self._cur.fetchall():
			word = html.unescape(row[0])
			definition = row[1]
			yield self._glos.newEntry(word, definition, defiFormat="m")

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
