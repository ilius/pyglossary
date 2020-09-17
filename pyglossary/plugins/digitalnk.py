# -*- coding: utf-8 -*-

from formats_common import *
import html

enable = True
format = 'DigitalNK'
description = 'DigitalNK (SQLite3, N-Korean)'
extensions = ()
readOptions = []
writeOptions = []

tools = [
	{
		"name": "Dic.rs",
		"web": "https://github.com/digitalprk/dicrs",
		"platforms": ["Linux"],
		"license": " BSD-2-Clause",
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
		self._glos.setDefaultDefiFormat("m")

	def __len__(self):
		self._cur.execute("select count(*) from dictionary")
		return self._cur.fetchone()[0]

	def __iter__(self):
		self._cur.execute(
			"select word, definition from dictionary"
			" order by word"
		)
		for row in self._cur:
			word = html.unescape(row[0])
			definition = row[1]
			yield self._glos.newEntry(word, definition, defiFormat="m")

	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
