
import typing

# -*- coding: utf-8 -*-
from os.path import isfile
from typing import TYPE_CHECKING

from .core import log

if TYPE_CHECKING:
	import sqlite3
	from typing import Generator, Iterator

	from .glossary_types import EntryType, GlossaryType

from .text_utils import (
	joinByBar,
	splitByBar,
)


class Writer(object):
	def __init__(self: "typing.Self", glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self: "typing.Self") -> None:
		self._filename = ''
		self._con: "sqlite3.Connection | None"
		self._cur: "sqlite3.Cursor | None"

	def open(self: "typing.Self", filename: str) -> None:
		import sqlite3
		if isfile(filename):
			raise IOError(f"file {filename!r} already exists")
		self._filename = filename
		self._con = sqlite3.connect(filename)
		self._cur = self._con.cursor()
		self._con.execute(
			"CREATE TABLE dict ("
			"word TEXT,"
			"wordlower TEXT,"
			"alts TEXT,"
			"defi TEXT,"
			"defiFormat CHAR(1),"
			"bindata BLOB)",
		)
		self._con.execute(
			"CREATE INDEX dict_sortkey ON dict(wordlower, word);",
		)

	def write(self: "typing.Self") -> "Generator[None, EntryType, None]":
		con = self._con
		cur = self._cur
		if not (con and cur):
			log.error(f"write: {con=}, {cur=}")
			return
		count = 0
		while True:
			entry = yield
			if entry is None:
				break
			word = entry.l_word[0]
			alts = joinByBar(entry.l_word[1:])
			defi = entry.defi
			defiFormat = entry.defiFormat
			bindata = None
			if entry.isData():
				bindata = entry.data
			cur.execute(
				"insert into dict("
				"word, wordlower, alts, "
				"defi, defiFormat, bindata)"
				" values (?, ?, ?, ?, ?, ?)",
				(
					word, word.lower(), alts,
					defi, defiFormat, bindata,
				),
			)
			count += 1
			if count % 1000 == 0:
				con.commit()

		con.commit()

	def finish(self: "typing.Self") -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()


class Reader(object):
	def __init__(self: "typing.Self", glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self: "typing.Self") -> None:
		self._filename = ""
		self._con: "sqlite3.Connection | None"
		self._cur: "sqlite3.Cursor | None"

	def open(self: "typing.Self", filename: str) -> None:
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		# self._glos.setDefaultDefiFormat("m")

	def __len__(self: "typing.Self") -> int:
		if self._cur is None:
			return 0
		self._cur.execute("select count(*) from dict")
		return self._cur.fetchone()[0]

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		if self._cur is None:
			return
		self._cur.execute(
			"select word, alts, defi, defiFormat from dict"
			" order by wordlower, word",
		)
		for row in self._cur:
			words = [row[0]] + splitByBar(row[1])
			defi = row[2]
			defiFormat = row[3]
			yield self._glos.newEntry(words, defi, defiFormat=defiFormat)

	def close(self: "typing.Self") -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
