# -*- coding: utf-8 -*-

from os.path import isfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Iterator

	from .glossary_type import EntryType, GlossaryType

from .text_utils import (
	joinByBar,
	splitByBar,
)


class Writer(object):
	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ''
		self._con = None
		self._cur = None

	def open(self, filename: str) -> None:
		from sqlite3 import connect
		if isfile(filename):
			raise IOError(f"file {filename!r} already exists")
		self._filename = filename
		self._con = connect(filename)
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

	def write(self) -> None:
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
			self._cur.execute(
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
				self._con.commit()

		self._con.commit()

	def finish(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()


class Reader(object):
	def __init__(self, glos: "GlossaryType") -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ''
		self._con = None
		self._cur = None

	def open(self, filename: str) -> None:
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		# self._glos.setDefaultDefiFormat("m")

	def __len__(self) -> int:
		self._cur.execute("select count(*) from dict")
		return self._cur.fetchone()[0]

	def __iter__(self) -> "Iterator[EntryType]":
		self._cur.execute(
			"select word, alts, defi, defiFormat from dict"
			" order by wordlower, word",
		)
		for row in self._cur:
			words = [row[0]] + splitByBar(row[1])
			defi = row[2]
			defiFormat = row[3]
			yield self._glos.newEntry(words, defi, defiFormat=defiFormat)

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
