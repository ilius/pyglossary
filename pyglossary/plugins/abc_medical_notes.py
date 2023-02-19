# -*- coding: utf-8 -*-

import html

enable = True
lname = "abc_medical_notes"
format = 'ABCMedicalNotes'
description = 'ABC Medical Notes (SQLite3)'
extensions = ()
extensionCreate = ".db"
kind = "binary"
wiki = ""
_url = (
	"https://play.google.com/store/apps/details?id="
	"com.pocketmednotes2014.secondapp"
)
website = (
	_url,
	"ABC Medical Notes 2021 - Google Play",
)

from typing import Iterator

from pyglossary.glossary_type import EntryType, GlossaryType


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
		self._glos.setDefaultDefiFormat("h")

	def __len__(self) -> int:
		self._cur.execute("select count(*) from NEW_TABLE")
		return self._cur.fetchone()[0]

	def __iter__(self) -> "Iterator[EntryType]":
		self._cur.execute(
			"select _id, contents from NEW_TABLE where _id is not null",
		)
		# FIXME: iteration over self._cur stops after one entry
		# and self._cur.fetchone() returns None
		# for row in self._cur:
		for row in self._cur.fetchall():
			word = html.unescape(row[0])
			definition = row[1].decode("utf-8", errors="ignore")
			# print(f"{word!r}, {definition!r}")
			yield self._glos.newEntry(word, definition, defiFormat="h")

	def close(self) -> None:
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
