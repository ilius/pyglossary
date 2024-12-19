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
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .glossary_utils import Error

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable, Iterator
	from typing import Any

	from .glossary_types import EntryType, RawEntryType
	from .sort_keys import NamedSortKey
	from .sort_keys_types import SQLiteSortKeyType


__all__ = ["SqEntryList"]

log = logging.getLogger("pyglossary")


class SqEntryList:
	def __init__(  # noqa: PLR0913
		self,
		entryToRaw: Callable[[EntryType], RawEntryType],
		entryFromRaw: Callable[[RawEntryType], EntryType],
		database: str,
		create: bool = True,
	) -> None:
		"""sqliteSortKey[i] == (name, type, valueFunc)."""
		import sqlite3

		self._entryToRaw = entryToRaw
		self._entryFromRaw = entryFromRaw
		self._database = database

		self._con: sqlite3.Connection | None = sqlite3.connect(database)
		self._cur: sqlite3.Cursor | None = self._con.cursor()

		if not database:
			raise ValueError(f"invalid {database=}")

		self._orderBy = "rowid"
		self._sorted = False
		self._reverse = False
		self._len = 0
		self._create = create
		self._sqliteSortKey: SQLiteSortKeyType = []
		self._columnNames = ""

	def hasSortKey(self) -> bool:
		return bool(self._sqliteSortKey)

	def setSortKey(
		self,
		namedSortKey: NamedSortKey,
		sortEncoding: str | None,
		writeOptions: dict[str, Any],
	) -> None:
		"""sqliteSortKey[i] == (name, type, valueFunc)."""
		if self._con is None:
			raise RuntimeError("self._con is None")

		if self._sqliteSortKey:
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
		self._columnNames = ",".join(col[0] for col in sqliteSortKey)

		if not self._create:
			self._parseExistingIndex()
			return

		colDefs = ",".join(
			[f"{col[0]} {col[1]}" for col in sqliteSortKey] + ["data BLOB"],
		)
		self._con.execute(
			f"CREATE TABLE data ({colDefs})",
		)

	def __len__(self) -> int:
		return self._len

	def _encode(self, entry: EntryType) -> bytes:
		return b"\x00".join(self._entryToRaw(entry))

	def _decode(self, data: bytes) -> EntryType:
		return self._entryFromRaw(data.split(b"\x00"))

	def append(self, entry: EntryType) -> None:
		self._cur.execute(  # type: ignore
			f"insert into data({self._columnNames}, data)"
			f" values (?{', ?' * len(self._sqliteSortKey)})",
			[col[2](entry.l_word) for col in self._sqliteSortKey]
			+ [self._encode(entry)],
		)
		self._len += 1

	def __iter__(self) -> Iterator[EntryType]:
		if self._cur is None:
			raise Error("SQLite cursor is closed")
		self._cur.execute(f"SELECT data FROM data ORDER BY {self._orderBy}")
		for row in self._cur:
			yield self._decode(row[0])

	def __iadd__(self, other: Iterable) -> SqEntryList:
		for item in other:
			self.append(item)
		return self

	def sort(self, reverse: bool = False) -> None:
		if self._sorted:
			raise NotImplementedError("can not sort more than once")
		if not self._sqliteSortKey:
			raise RuntimeError("self._sqliteSortKey is empty")

		self._reverse = reverse
		self._sorted = True
		sortColumnNames = self._columnNames
		self._orderBy = sortColumnNames
		if reverse:
			self._orderBy = ",".join(f"{col[0]} DESC" for col in self._sqliteSortKey)
		assert self._con
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
		columnNames = sql[i + 1 : j]
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
		self.close()
