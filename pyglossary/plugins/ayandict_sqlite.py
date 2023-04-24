# -*- coding: utf-8 -*-

import typing
from typing import (
	TYPE_CHECKING,
	Generator,
)

if TYPE_CHECKING:
	import sqlite3

from pyglossary.core import log
from pyglossary.glossary_types import EntryType, GlossaryType

enable = True
lname = "ayandict_sqlite"
format = "AyanDictSQLite"
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

class Writer(object):
	depends = {
		# "sqlite_spellfix": "sqlite-spellfix",
	}

	def __init__(self: "typing.Self", glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self: "typing.Self") -> None:
		self._filename = ""
		self._con: "sqlite3.Connection | None" = None
		self._cur: "sqlite3.Cursor | None" = None
		self._fuzzy = False

	def open(self: "typing.Self", filename: str) -> None:
		from sqlite3 import connect

		self._filename = filename
		con = self._con = connect(filename)
		self._cur = self._con.cursor()

		for query in (
			"CREATE TABLE meta ('key' TEXT PRIMARY KEY NOT NULL, 'value' TEXT);",
			"CREATE TABLE entry ('id' INTEGER PRIMARY KEY NOT NULL, "
				"'term' TEXT, 'article' TEXT);",
			"CREATE TABLE alt ('id' INTEGER NOT NULL, 'term' TEXT);",
			"CREATE INDEX idx_meta ON meta(key);",
			"CREATE INDEX idx_entry_term ON entry(term COLLATE NOCASE);",
			"CREATE INDEX idx_alt_id ON alt(id);",
			"CREATE INDEX idx_alt_term ON alt(term COLLATE NOCASE);",
		):
			try:
				con.execute(query)
			except Exception as e:
				log.error(f"query: {query}")
				raise e

		for key, value in self._glos.iterInfo():
			con.execute(
				"INSERT	INTO meta (key, value) VALUES (?, ?);",
				(key, value),
			)

		con.commit()

		try:
			import sqlite_spellfix
		except ImportError:
			log.warning("sqlite_spellfix is not installed, fuzzy table is not created")
		else:
			self._fuzzy = True
			log.info(f"Using sqlite spellfix: {sqlite_spellfix.extension_path()}")
			con.load_extension(sqlite_spellfix.extension_path())

	def finish(self):
		if self._con is None or self._cur is None:
			return

		if self._fuzzy:
			self._con.execute("CREATE VIRTUAL TABLE fuzzy USING spellfix1;")
			self._con.execute("INSERT INTO fuzzy(word, rank) SELECT term, id FROM entry;")
			self._con.commit()

		self._con.commit()
		self._con.close()
		self._con = None
		self._cur = None

	def write(self: "typing.Self") -> "Generator[None, EntryType, None]":
		import hashlib

		cur = self._cur
		_hash = hashlib.md5()
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# can save it with entry.save(directory)
				continue
			cur.execute(
				"INSERT INTO entry(term, article) VALUES (?, ?);",
				(entry.l_word[0], entry.defi),
			)
			for alt in entry.l_word[1:]:
				cur.execute(
					"INSERT INTO alt(id, term) VALUES (?, ?);",
					(cur.lastrowid, alt),
				)
			_hash.update(entry.s_word.encode("utf-8"))

		cur.execute(
			"INSERT INTO meta (key, value) VALUES (?, ?);",
			("hash", _hash.hexdigest()),
		)
