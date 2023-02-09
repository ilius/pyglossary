# -*- coding: utf-8 -*-
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from pickle import dumps, loads
import os
from os.path import isfile
from .entry import Entry
from .sort_keys import NamedSortKey, sqliteSortKeyType

from typing import Any, Optional, List, Dict

import logging
log = logging.getLogger("pyglossary")

PICKLE_PROTOCOL = 4

# Pickle protocol 4 performed better than protocol 5 on Python 3.9.2
# Slightly lower running time, lower memory usage, and same .db file size

# Pickle protocol 5		added in Python 3.8		PEP 574
# Pickle protocol 4		added in Python 3.4		PEP 3154
# Pickle Protocol 3		added in Python 3.0

# https://docs.python.org/3/library/pickle.html


class SqEntryList(list):
	def __init__(
		self,
		glos,
		filename: str,
		create: bool = True,
		persist: bool = False,
	):
		"""
			sqliteSortKey[i] == (name, type, valueFunc)

			persist: do not delete the file when variable is deleted
		"""
		from sqlite3 import connect

		self._glos = glos
		self._filename = filename
		self._persist = persist
		self._con = connect(filename)
		self._cur = self._con.cursor()

		if not filename:
			raise ValueError(f"invalid {filename=}")

		self._orderBy = "rowid"
		self._sorted = False
		self._reverse = False
		self._len = 0
		self._create = create
		self._sqliteSortKey = None
		self._columnNames = ""

	def _getLocaleSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortLocale: str,
		writeOptions: "Dict[str, Any]",
	) -> "sqliteSortKeyType":
		from icu import Locale, Collator

		if namedSortKey.sqlite_locale is None:
			raise ValueError(
				f"locale-sorting is not supported "
				f"for sortKey={namedSortKey.name}"
			)

		localeObj = Locale(sortLocale)
		if not localeObj.getISO3Language():
			raise ValueError(f"invalid locale {sortLocale!r}")

		log.info(f"Sorting based on locale {localeObj.getName()}")

		collator = Collator.createInstance(localeObj)

		return namedSortKey.sqlite_locale(collator, **writeOptions)

	def _applySortScript(
		self,
		sqliteSortKey: "sqliteSortKeyType",
		sortScript: "List[str]",
	) -> "sqliteSortKeyType":
		from pyglossary.langs.writing_system import (
			writingSystemByLowercaseName,
			getWritingSystemFromText,
		)

		wsNames = []
		for wsNameInput in sortScript:
			ws = writingSystemByLowercaseName.get(wsNameInput.lower())
			if ws is None:
				log.error(f"invalid script name {wsNameInput!r}")
				continue
			wsNames.append(ws.name)

		log.info(f"Sorting based on scripts: {wsNames}")

		def getScriptIndex(words: "List[str]") -> int:
			ws = getWritingSystemFromText(words[0], True)
			if ws is None:
				return -1  # FIXME
			try:
				return wsNames.index(ws.name)
			except ValueError:
				return len(wsNames)

		return [(
			"script_index",  # name
			"INTEGER",  # type,
			getScriptIndex,  # valueFunc
		)] + sqliteSortKey

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "Optional[str]",
		sortLocale: "Optional[str]",
		sortScript: "Optional[List[str]]",
		writeOptions: "Dict[str, Any]",
	):
		"""
			sqliteSortKey[i] == (name, type, valueFunc)
		"""

		if self._sqliteSortKey is not None:
			raise RuntimeError("Called setSortKey twice")

		if sortLocale:
			sqliteSortKey = self._getLocaleSortKey(
				namedSortKey,
				sortLocale,
				writeOptions,
			)
		else:
			sqliteSortKey = namedSortKey.sqlite(sortEncoding, **writeOptions)

		if sortScript:
			sqliteSortKey = self._applySortScript(sqliteSortKey, sortScript)

		self._sqliteSortKey = sqliteSortKey
		self._columnNames = ",".join([
			col[0] for col in sqliteSortKey
		])

		if not self._create:
			self._parseExistingIndex()
			return

		colDefs = ",".join([
			f"{col[0]} {col[1]}"
			for col in sqliteSortKey
		] + ["pickle BLOB"])
		self._con.execute(
			f"CREATE TABLE data ({colDefs})"
		)

	def __len__(self):
		return self._len

	def append(self, entry):
		rawEntry = entry.getRaw(self._glos)
		self._len += 1
		colCount = len(self._sqliteSortKey)
		try:
			values = [
				col[2](entry.l_word) for col in self._sqliteSortKey
			]
		except Exception:
			log.critical(f"error in _sqliteSortKey funcs for {rawEntry = }")
			raise
		try:
			pickleEntry = dumps(rawEntry, protocol=PICKLE_PROTOCOL)
		except Exception:
			log.critical(f"error in pickle.dumps for {rawEntry = }")
			raise
		self._cur.execute(
			f"insert into data({self._columnNames}, pickle)"
			f" values (?{', ?' * colCount})",
			values + [pickleEntry],
		)
		if self._len % 1000 == 0:
			self._con.commit()

	def __iadd__(self, other):
		for item in other:
			self.append(item)
		return self

	def sort(self, reverse=False):
		if self._sorted:
			raise NotImplementedError("can not sort more than once")

		self._reverse = reverse
		self._sorted = True
		sortColumnNames = self._columnNames
		self._orderBy = sortColumnNames
		if reverse:
			self._orderBy = ",".join([
				f"{col[0]} DESC" for col in self._sqliteSortKey
			])
		self._con.commit()
		self._con.execute(
			f"CREATE INDEX sortkey ON data({sortColumnNames});"
		)
		self._con.commit()

	def _parseExistingIndex(self) -> bool:
		self._cur.execute("select sql FROM sqlite_master WHERE name='sortkey'")
		row = self._cur.fetchone()
		if row is None:
			return False
		sql = row[0]
		# sql == "CREATE INDEX sortkey ON data(wordlower,word)"
		i = sql.find("(")
		if i < 0:
			log.error(f"error parsing index {sql=}")
			return False
		j = sql.find(")", i)
		if j < 0:
			log.error(f"error parsing index {sql=}")
			return False
		columnNames = sql[i + 1:j]
		self._sorted = True
		self._orderBy = columnNames
		return True

	def deleteAll(self):
		if self._con is None:
			return
		self._con.execute("DELETE FROM data;")
		self._con.commit()
		self._len = 0

	def clear(self):
		self.close()

	def close(self):
		if self._con is None:
			return
		self._con.commit()
		self._cur.close()
		self._con.close()
		self._con = None
		self._cur = None

	def __del__(self):
		try:
			self.close()
			if not self._persist and isfile(self._filename):
				os.remove(self._filename)
		except AttributeError as e:
			log.error(str(e))

	def __iter__(self):
		glos = self._glos
		query = f"SELECT pickle FROM data ORDER BY {self._orderBy}"
		self._cur.execute(query)
		for row in self._cur:
			yield Entry.fromRaw(
				glos, loads(row[0]),
				defaultDefiFormat=glos._defaultDefiFormat,
			)
