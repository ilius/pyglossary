
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from os.path import isfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import sqlite3
	from collections.abc import Iterator, Sequence

	from pyglossary.glossary_types import EntryType


from pyglossary.core import log


class BaseSqList:
	def __init__(
		self,
		filename: str,
	) -> None:
		from sqlite3 import connect

		if isfile(filename):
			log.warning(f"Renaming {filename} to {filename}.bak")
			os.rename(filename, filename + "bak")

		self._filename = filename

		self._con: sqlite3.Connection | None = connect(filename)
		self._cur: sqlite3.Cursor | None = self._con.cursor()

		if not filename:
			raise ValueError(f"invalid {filename=}")

		self._orderBy = "word_lower, word"
		self._sorted = False
		self._len = 0

		columns = self._columns = [
			("word_lower", "TEXT"),
			("word", "TEXT"),
		] + self.getExtraColumns()

		self._columnNames = ",".join(col[0] for col in columns)

		colDefs = ",".join(f"{col[0]} {col[1]}" for col in columns)
		self._con.execute(
			f"CREATE TABLE data ({colDefs})",
		)
		self._con.execute(
			f"CREATE INDEX sortkey ON data({self._orderBy});",
		)
		self._con.commit()

	@classmethod
	def getExtraColumns(cls) -> list[tuple[str, str]]:
		# list[(columnName, dataType)]
		return []

	def __len__(self) -> int:
		return self._len

	def append(self, item: Sequence) -> None:
		if self._cur is None or self._con is None:
			raise RuntimeError("db is closed")
		self._len += 1
		extraN = len(self._columns) - 1
		self._cur.execute(
			f"insert into data({self._columnNames}) values (?{', ?' * extraN})",
			[item[0].lower()] + list(item),
		)
		if self._len % 1000 == 0:
			self._con.commit()

	def sort(self) -> None:
		pass

	def close(self) -> None:
		if self._cur is None or self._con is None:
			return
		self._con.commit()
		self._cur.close()
		self._con.close()
		self._con = None
		self._cur = None

	def __del__(self) -> None:
		try:
			self.close()
		except AttributeError as e:
			log.error(str(e))

	def __iter__(self) -> Iterator[EntryType]:
		if self._cur is None:
			raise RuntimeError("db is closed")
		query = f"SELECT * FROM data ORDER BY {self._orderBy}"
		self._cur.execute(query)
		for row in self._cur:
			yield row[1:]


class IdxSqList(BaseSqList):
	@classmethod
	def getExtraColumns(cls) -> list[tuple[str, str]]:
		# list[(columnName, dataType)]
		return [
			("idx_block", "BLOB"),
		]


class SynSqList(BaseSqList):
	@classmethod
	def getExtraColumns(cls) -> list[tuple[str, str]]:
		# list[(columnName, dataType)]
		return [
			("entry_index", "INTEGER"),
		]
