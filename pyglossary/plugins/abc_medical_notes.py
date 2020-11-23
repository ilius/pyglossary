# -*- coding: utf-8 -*-

from formats_common import *
import html

enable = True
format = 'ABCMedicalNotes'
description = 'ABC Medical Notes (SQLite3)'
extensions = ()
readOptions = []
writeOptions = []

tools = [
	{
		"name": "ABC Medical Notes 2020",
		"web": "https://ply.gl/com.pocketmednotes2014.secondapp",
		"platforms": ["Android"],
		# "license": "",
	},
]


class Reader(object):
	def __init__(self, glos):
		self._glos = glos
		self._clear()

	def _clear(self):
		self._filename = ''
		self._con = None
		self._cur = None

	def open(self, filename):
		from sqlite3 import connect
		self._filename = filename
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._glos.setDefaultDefiFormat("h")

	def __len__(self):
		self._cur.execute("select count(*) from NEW_TABLE")
		return self._cur.fetchone()[0]

	def __iter__(self):
		self._cur.execute(
			"select _id, contents from NEW_TABLE where _id is not null"
		)
		# FIXME: iteration over self._cur stops after one entry
		# and self._cur.fetchone() returns None
		# for row in self._cur:
		for row in self._cur.fetchall():
			word = html.unescape(row[0])
			definition = row[1].decode("utf-8", errors="ignore")
			# print(f"{word!r}, {definition!r}")
			yield self._glos.newEntry(word, definition, defiFormat="h")

	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
