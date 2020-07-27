# -*- coding: utf-8 -*-

from formats_common import *
import html

enable = True
format = 'Dictcc'
description = 'Dict.cc (SQLite3)'
extensions = ('.db',)
readOptions = []
writeOptions = []

tools = [
	{
		"name": "dict.cc dictionary",
		"web": "https://play.google.com/store/apps/details?id=cc.dict.dictcc",
		"platforms": ["Android"],
		"license": "Proprietary",
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

	def __len__(self):
		self._cur.execute("select count(*) from main_ft")
		return self._cur.fetchone()[0]

	def __iter__(self):
		self._cur.execute(
			"select term1, term2, entry_type from main_ft"
			" order by term1"
		)
		for row in self._cur:
			term1 = html.unescape(row[0])
			term2 = row[1]
			term2 = html.escape(html.unescape(term2))
			entry_type = row[2]
			defi = term2
			if entry_type:
				defi = f"<i>{entry_type}</i><br>{defi}"
			yield self._glos.newEntry(term1, defi)

	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
