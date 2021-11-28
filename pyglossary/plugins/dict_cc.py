# -*- coding: utf-8 -*-

from formats_common import *
import html

enable = True
lname = "dict_cc"
format = 'Dictcc'
description = 'Dict.cc (SQLite3)'
extensions = ()
extensionCreate = ".db"
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/Dict.cc"
website = (
	"https://play.google.com/store/apps/details?id=cc.dict.dictcc",
	"dict.cc dictionary - Google Play",
)


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
		self._cur.execute(
			"select count(distinct term1)+count(distinct term2) from main_ft"
		)
		return self._cur.fetchone()[0]

	def makeList(
		self,
		hf: "lxml.etree.htmlfile",
		input_elements: "List[lxml.etree.Element]",
		processor: "Callable",
		single_prefix=None,
		skip_single=True
	):
		""" Wrap elements into <ol> if more than one element """
		if len(input_elements) == 0:
			return

		if len(input_elements) == 1:
			hf.write(single_prefix)
			processor(hf, input_elements[0])
			return

		with hf.element("ol"):
			for el in input_elements:
				with hf.element("li"):
					processor(hf, el)

	def writeSense(
		self,
		hf: "lxml.etree.htmlfile",
		row: "Tuple[str, str, str]",
	):
		from lxml import etree as ET
		trans, entry_type = row
		if entry_type:
			with hf.element("i"):
				hf.write(f"{entry_type}")
			hf.write(ET.Element("br"))
		try:
			hf.write(trans + " ")
		except Exception as e:
			log.error(f"error in writing {trans!r}, {e}")
			hf.write(repr(trans) + " ")
		else:
			with hf.element("big"):
				with hf.element("a", href=f'bword://{trans}'):
					hf.write(f"⏎")

	def iterRows(self, column1, column2):
		self._cur.execute(
			f"select {column1}, {column2}, entry_type from main_ft"
			f" order by {column1}"
		)
		for row in self._cur.fetchall():
			term1 = row[0]
			term2 = row[1]
			try:
				term1 = html.unescape(term1)
			except Exception as e:
				log.error(f"html.unescape({term1!r}) -> {e}")
			try:
				term2 = html.unescape(term2)
			except Exception as e:
				log.error(f"html.unescape({term2!r}) -> {e}")
			yield term1, term2, row[2]

	def parseGender(self, headword):
		# {m}	masc	masculine	German: maskulin
		# {f}	fem 	feminine	German: feminin
		# {n}	neut	neutral		German: neutral
		# { }	????
		i = headword.find(" {")
		if i <= 0:
			return None, headword
		if len(headword) < i + 4:
			return None, headword
		if headword[i + 3] != "}":
			return None, headword
		g = headword[i + 2]
		gender = None
		if g == "m":
			gender = "masculine"
		elif g == "f":
			gender = "feminine"
		elif g == "n":
			gender = "neutral"
		else:
			log.warning(f"invalid gender {g!r}")
			return None, headword
		headword = headword[:i] + headword[i + 4:]
		return gender, headword

	def _iterOneDirection(self, column1, column2):
		from itertools import groupby
		from lxml import etree as ET
		from io import BytesIO

		glos = self._glos
		for headword, groupsOrig in groupby(
			self.iterRows(column1, column2),
			key=lambda row: row[0],
		):
			headword = html.unescape(headword)
			groups = [
				(term2, entry_type)
				for _, term2, entry_type in groupsOrig
			]
			f = BytesIO()
			gender, headword = self.parseGender(headword)
			with ET.htmlfile(f, encoding="utf-8") as hf:
				with hf.element("div"):
					if gender:
						with hf.element("i"):
							hf.write(gender)
						hf.write(ET.Element("br"))
					self.makeList(
						hf,
						groups,
						self.writeSense,
					)
			defi = f.getvalue().decode("utf-8")
			yield self._glos.newEntry(headword, defi, defiFormat="h")

	def __iter__(self):
		yield from self._iterOneDirection("term1", "term2")
		yield from self._iterOneDirection("term2", "term1")

	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
