# -*- coding: utf-8 -*-

from formats_common import *
import html
from typing import List, Tuple, Callable

enable = True
format = 'Dictcc'
description = 'Dict.cc (SQLite3)'
extensions = ()
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
		self._glos.setDefaultDefiFormat("h")
		self._glos.setInfo("definition_has_headwords", "True")

	def __len__(self):
		self._cur.execute("select count(*) from main_ft")
		return self._cur.fetchone()[0]

	def makeList(
		self,
		hf: "lxml.etree.htmlfile",
		input_elements: "List[lxml.etree.Element]",
		processor: Callable,
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
		row: Tuple[str, str, str],
	):
		from lxml import etree as ET
		term1, term2, entry_type = row
		if entry_type:
			with hf.element("i"):
				hf.write(f"{entry_type}")
			hf.write(ET.Element("br"))
		try:
			hf.write(term2)
		except:
			log.error(f"term2={term2!r}")

	def iterRows(self):
		self._cur.execute(
			"select term1, term2, entry_type from main_ft"
			" order by term1"
		)
		for row in self._cur:
			term1 = html.unescape(row[0])
			term2 = row[1]
			entry_type = row[2]
			#defi = term2
			#if entry_type:
			#	defi = f"<i>{entry_type}</i><br>{defi}"
			yield term1, term2, entry_type

	def __iter__(self):
		from itertools import groupby
		from lxml import etree as ET
		from io import BytesIO

		glos = self._glos
		for headword, groups in groupby(
			self.iterRows(),
			key=lambda row: row[0],
		):
			groups = list(groups)
			f = BytesIO()
			with ET.htmlfile(f) as hf:
				with hf.element("div"):
					with glos.titleElement(hf, headword):
						hf.write(headword)
					if len(groups) == 1:
						hf.write(ET.Element("br"))
					self.makeList(
						hf,
						groups,
						self.writeSense,
					)
			defi = f.getvalue().decode("utf-8")
			yield self._glos.newEntry(headword, defi, defiFormat="h")


	def close(self):
		if self._cur:
			self._cur.close()
		if self._con:
			self._con.close()
		self._clear()
