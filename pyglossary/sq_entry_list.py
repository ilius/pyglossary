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

import logging
import os
from os.path import isfile
from pickle import dumps, loads
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterable, Iterator
	from typing import Any, Callable

	from .glossary_types import EntryType, RawEntryType
	from .sort_keys import NamedSortKey


log = logging.getLogger("pyglossary")

PICKLE_PROTOCOL = 4

# Pickle protocol 4 performed better than protocol 5 on Python 3.9.2
# Slightly lower running time, lower memory usage, and same .db file size

# Pickle protocol 5		added in Python 3.8		PEP 574
# Pickle protocol 4		added in Python 3.4		PEP 3154
# Pickle Protocol 3		added in Python 3.0

# https://docs.python.org/3/library/pickle.html


class SqEntryList:
	def __init__(
		self,
		entryToRaw: "Callable[[EntryType], RawEntryType]",
		entryFromRaw: "Callable[[RawEntryType], EntryType]",
		filename: str,
		create: bool = True,
		persist: bool = False,
	) -> None:
		"""
		sqliteSortKey[i] == (name, type, valueFunc).

		persist: do not delete the file when variable is deleted
		"""
		import sqlite3

		self._entryToRaw = entryToRaw
		self._entryFromRaw = entryFromRaw
		self._filename = filename

		self._persist = persist
		self._con: "sqlite3.Connection | None" = sqlite3.connect(filename)
		self._cur: "sqlite3.Cursor | None" = self._con.cursor()

		if not filename:
			raise ValueError(f"invalid {filename=}")

		self._orderBy = "rowid"
		self._sorted = False
		self._reverse = False
		self._len = 0
		self._create = create
		self._sqliteSortKey = None
		self._columnNames = ""

	@property
	def rawEntryCompress(self) -> bool:
		return False

	@rawEntryCompress.setter
	def rawEntryCompress(self, enable: bool) -> None:
		# just to comply with EntryListType
		pass

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		"""sqliteSortKey[i] == (name, type, valueFunc)."""
		if self._con is None:
			raise RuntimeError("self._con is None")

		if self._sqliteSortKey is not None:
			raise RuntimeError("Called setSortKey twice")

		if namedSortKey.sqlite is None:
			raise NotImplementedError(
				f"sort key {namedSortKey.name!r} is not supported",
			)

		kwargs = writeOptions.copy()
		if sortEncoding:
			kwargs["sortEncoding"] = sortEncoding

		sqliteSortKey = namedSortKey.sqlite(**kwargs)

		self._sqliteSortKey = sqliteSortKey
		self._columnNames = ",".join(
			col[0] for col in sqliteSortKey
		)

		if not self._create:
			self._parseExistingIndex()
			return

		colDefs = ",".join([
			f"{col[0]} {col[1]}"
			for col in sqliteSortKey
		] + ["pickle BLOB"])
		self._con.execute(
			f"CREATE TABLE data ({colDefs})",
		)

	def __len__(self) -> int:
		return self._len

	def append(self, entry: "EntryType") -> None:
		if self._sqliteSortKey is None:
			raise RuntimeError("self._sqliteSortKey is None")
		rawEntry = self._entryToRaw(entry)
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

	def __iadd__(self, other: "Iterable") -> "SqEntryList":
		for item in other:
			self.append(item)
		return self

	def sort(self, reverse: bool = False) -> None:
		if self._sorted:
			raise NotImplementedError("can not sort more than once")
		if self._sqliteSortKey is None:
			raise RuntimeError("self._sqliteSortKey is None")

		self._reverse = reverse
		self._sorted = True
		sortColumnNames = self._columnNames
		self._orderBy = sortColumnNames
		if reverse:
			self._orderBy = ",".join(
				f"{col[0]} DESC" for col in self._sqliteSortKey
			)
		self._con.commit()
		self._con.execute(
			f"CREATE INDEX sortkey ON data({sortColumnNames});",
		)
		self._con.commit()

	def _parseExistingIndex(self) -> bool:
		if self._cur is None:
			return False
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

	def deleteAll(self) -> None:
		if self._con is None:
			return
		self._con.execute("DELETE FROM data;")
		self._con.commit()
		self._len = 0

	def clear(self) -> None:
		self.close()

	def close(self) -> None:
		if self._con is None or self._cur is None:
			return
		self._con.commit()
		self._cur.close()
		self._con.close()
		self._con = None
		self._cur = None

	def __del__(self) -> None:
		try:
			self.close()
			if not self._persist and isfile(self._filename):
				os.remove(self._filename)
		except AttributeError as e:
			log.error(str(e))

	def __iter__(self) -> "Iterator[EntryType]":
		if self._cur is None:
			return
		query = f"SELECT pickle FROM data ORDER BY {self._orderBy}"
		self._cur.execute(query)
		entryFromRaw = self._entryFromRaw
		for row in self._cur:
			yield entryFromRaw(loads(row[0]))
