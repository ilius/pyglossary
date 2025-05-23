# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import sqlite3
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
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

		self._cur.execute("SELECT key, value FROM meta;")
		for row in self._cur.fetchall():
			if row[0] == "hash":
				continue
			self._glos.setInfo(row[0], row[1])

	def __len__(self) -> int:
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute("select count(id) from entry")
		return self._cur.fetchone()[0]

	def __iter__(self) -> Iterator[EntryType]:
		from json import loads

		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute(
			"SELECT entry.term, entry.article, "
			"json_group_array(alt.term)"
			"FROM entry LEFT JOIN alt ON entry.id=alt.id "
			"GROUP BY entry.id;",
		)
		for row in self._cur.fetchall():
			terms = [row[0]] + [alt for alt in loads(row[2]) if alt]
			article = row[1]
			yield self._glos.newEntry(terms, article, defiFormat="h")

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
