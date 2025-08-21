# -*- coding: utf-8 -*-
from __future__ import annotations

import html
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

	def __len__(self) -> int:
		if self._cur is None:
			raise ValueError("cur is None")
		self._cur.execute("select count(*) from WordsTable")
		return self._cur.fetchone()[0]

	def __iter__(self) -> Iterator[EntryType]:
		if self._cur is None:
			raise ValueError("cur is None")
		from pyglossary.langs.writing_system import getWritingSystemFromText

		alternateDict: dict[str, list[str]] = {}
		self._cur.execute("select wordkey, searchwordkey from Keys")
		for row in self._cur.fetchall():
			if row[0] in alternateDict:
				alternateDict[row[0]].append(row[1])
			else:
				alternateDict[row[0]] = [row[1]]

		self._cur.execute(
			"select word, searchword, root, meaning from WordsTable order by id",
		)
		# FIXME: iteration over self._cur stops after one entry
		# and self._cur.fetchone() returns None
		# for row in self._cur:
		for row in self._cur.fetchall():
			term = row[0]
			searchword = row[1]
			root = row[2]
			meaning = row[3]
			definition = meaning
			definition = definition.replace("|", "<br>")

			if root:
				definition += (
					f'<br>Root: <a href="bword://{html.escape(root)}">{root}</a>'
				)

			ws = getWritingSystemFromText(meaning)
			if ws and ws.direction == "rtl":
				definition = f'<div dir="rtl">{definition}</div>'

			terms = [term, searchword]
			if term in alternateDict:
				terms += alternateDict[term]
			yield self._glos.newEntry(
				terms,
				definition,
				defiFormat="h",
			)

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
