# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
	TYPE_CHECKING,
)

if TYPE_CHECKING:
	import sqlite3
	from collections.abc import Generator, Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.xdxf.transform import XdxfTransformer

from pyglossary.core import log
from pyglossary.option import BoolOption, Option

__all__ = [
	"Reader",
	"Writer",
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
lname = "ayandict_sqlite"
name = "AyanDictSQLite"
description = "AyanDict SQLite"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://github.com/ilius/ayandict",
	"ilius/ayandict",
)
optionsProp: dict[str, Option] = {
	"fuzzy": BoolOption(
		comment="Create fuzzy search data",
	),
}


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


class Writer:
	_fuzzy: int = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._con: sqlite3.Connection | None = None
		self._cur: sqlite3.Cursor | None = None
		self._xdxfTr: XdxfTransformer | None = None

	def open(self, filename: str) -> None:
		from sqlite3 import connect

		self._filename = filename
		con = self._con = connect(filename)
		self._cur = self._con.cursor()

		for query in (
			"CREATE TABLE meta ('key' TEXT PRIMARY KEY NOT NULL, 'value' TEXT);",
			(
				"CREATE TABLE entry ('id' INTEGER PRIMARY KEY NOT NULL, "
				"'term' TEXT, 'article' TEXT);"
			),
			"CREATE TABLE alt ('id' INTEGER NOT NULL, 'term' TEXT);",
			"CREATE INDEX idx_meta ON meta(key);",
			"CREATE INDEX idx_entry_term ON entry(term COLLATE NOCASE);",
			"CREATE INDEX idx_alt_id ON alt(id);",
			"CREATE INDEX idx_alt_term ON alt(term COLLATE NOCASE);",
		):
			try:
				con.execute(query)
			except Exception as e:  # noqa: PERF203
				log.error(f"query: {query}")
				raise e

		for key, value in self._glos.iterInfo():
			con.execute(
				"INSERT	INTO meta (key, value) VALUES (?, ?);",
				(key, value),
			)

		if self._fuzzy:
			con.execute(
				"CREATE TABLE fuzzy3 ('sub' TEXT NOT NULL, "
				"'term' TEXT NOT NULL, "
				"id INTEGER NOT NULL);",
			)
			con.execute(
				"CREATE INDEX idx_fuzzy3_sub ON fuzzy3(sub COLLATE NOCASE);",
			)

		con.commit()

	def finish(self) -> None:
		if self._con is None or self._cur is None:
			return

		self._con.commit()
		self._con.close()
		self._con = None
		self._cur = None

	def xdxf_setup(self) -> None:
		from pyglossary.xdxf.transform import XdxfTransformer

		# if self._xsl:
		# 	self._xdxfTr = XslXdxfTransformer(encoding="utf-8")
		# 	return
		self._xdxfTr = XdxfTransformer(encoding="utf-8")

	def xdxf_transform(self, text: str) -> str:
		if self._xdxfTr is None:
			self.xdxf_setup()
		return self._xdxfTr.transformByInnerString(text)  # type: ignore

	def write(self) -> Generator[None, EntryType, None]:
		import hashlib

		cur = self._cur
		if cur is None:
			raise ValueError("cur is None")
		hash_ = hashlib.md5()
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# can save it with entry.save(directory)
				continue
			defi = entry.defi
			entry.detectDefiFormat()
			if entry.defiFormat == "m":
				if "\n" in defi:
					defi = f"<pre>{defi}</pre>"
			elif entry.defiFormat == "x":
				defi = self.xdxf_transform(defi)

			cur.execute(
				"INSERT INTO entry(term, article) VALUES (?, ?);",
				(entry.l_word[0], defi),
			)
			id_ = cur.lastrowid
			if id_ is None:
				raise ValueError("lastrowid is None")
			for alt in entry.l_word[1:]:
				cur.execute(
					"INSERT INTO alt(id, term) VALUES (?, ?);",
					(id_, alt),
				)
			hash_.update(entry.s_word.encode("utf-8"))
			if self._fuzzy:
				self.addFuzzy(id_, entry.l_word)

		cur.execute(
			"INSERT INTO meta (key, value) VALUES (?, ?);",
			("hash", hash_.hexdigest()),
		)

	def addFuzzy(self, id_: int, terms: list[str]) -> None:
		cur = self._cur
		if cur is None:
			raise ValueError("cur is None")
		for term in terms:
			subs: set[str] = set()
			for word in term.split(" "):
				eword = "\n" + word
				subs.update(eword[i : i + 3] for i in range(len(eword) - 2))
			for sub in subs:
				cur.execute(
					"INSERT INTO fuzzy3(sub, term, id) VALUES (?, ?, ?);",
					(sub, term, id_),
				)
