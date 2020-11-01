# -*- coding: utf-8 -*-

from os.path import isfile


class Writer(object):
	def __init__(self, glos):
		self._glos = glos
		self._clear()

	def _clear(self):
		self._filename = ''
		self._con = None
		self._cur = None

	def open(self, filename):
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
			"bindata BLOB)"
		)
		self._con.execute(
			"CREATE INDEX dict_sortkey ON dict(wordlower, word);"
		)

	def write(self):
		count = 0
		while True:
			entry = yield
			if entry is None:
				break
			word = entry.l_word[0]
			alts = "|".join(entry.l_word[1:])
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

	def finish(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()


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
		# self._glos.setDefaultDefiFormat("m")

	def __len__(self):
		self._cur.execute("select count(*) from dict")
		return self._cur.fetchone()[0]

	def __iter__(self):
		self._cur.execute(
			"select word, alts, defi, defiFormat from dict"
			" order by wordlower, word"
		)
		for row in self._cur:
			words = [row[0]] + row[1].split("|")
			defi = row[2]
			defiFormat = row[3]
			yield self._glos.newEntry(words, defi, defiFormat=defiFormat)

	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
