from pickle import dumps, loads
import os
from os.path import isfile

import logging
log = logging.getLogger("pyglossary")

PICKLE_PROTOCOL = 4

# Pickle protocol 4 performed better than protocol 5 on Python 3.9.2
# Slightly lower running time, lower memory usage, and same .db file size

# Pickle protocol 5		added in Python 3.8		PEP 574
# Pickle protocol 4		added in Python 3.4		PEP 3154
# Pickle Protocol 3		added in Python 3.0

# https://docs.python.org/3/library/pickle.html


class SqList(object):
	def __init__(
		self,
		filename: str,
		sortColumns: "List[Tuple[str, str, str]]",
		create: bool = True,
		persist: bool = False,
	):
		"""
			sortColumns[i] == (name, type, valueFunc)

			persist: do not delete the file when variable is deleted
		"""
		from sqlite3 import connect
		if not filename:
			raise ValueError(f"invalid filename={filename!r}")
		self._filename = filename
		self._persist = persist
		self._con = connect(filename)
		self._cur = self._con.cursor()
		self._sortColumns = sortColumns
		self._columnNames = ",".join([
			col[0] for col in sortColumns
		])
		self._orderBy = "rowid"
		self._sorted = False
		self._reverse = False
		self._len = 0
		if create:
			colDefs = ",".join([
				f"{col[0]} {col[1]}"
				for col in sortColumns
			] + ["pickle BLOB"])
			self._con.execute(
				f"CREATE TABLE data ({colDefs})"
			)
		else:
			self._parseExistingIndex()

	def __len__(self):
		return self._len

	def append(self, item):
		self._len += 1
		colCount = len(self._sortColumns)
		try:
			values = [
				col[2](item) for col in self._sortColumns
			]
		except Exception as e:
			log.error(f"error in _sortColumns funcs for item = {item!r}")
			raise e
		try:
			item_pickle = dumps(item, protocol=PICKLE_PROTOCOL)
		except Exception as e:
			log.error(f"error in pickle.dumps for item = {item!r}")
			raise e
		self._cur.execute(
			f"insert into data({self._columnNames}, pickle)"
			f" values (?{', ?' * colCount})",
			values + [item_pickle],
		)
		if self._len % 1000 == 0:
			self._con.commit()

	def __iadd__(self, other):
		for item in other:
			self.append(item)
		return self

	def setSortKey(self, sortKey, sampleItem):
		log.warning(f"SqList: ignoring sortKey {sortKey}")
		# FIXME
		# sample = sortKey(sampleItem)

	def sort(self, key=None, reverse=False):
		if key is not None:
			raise NotImplementedError(
				"key= is not available,"
				"use sortColumns= argument when instantiating"
			)
		if self._sorted:
			raise NotImplementedError("can not sort more than once")

		self._reverse = reverse
		self._sorted = True
		sortColumnNames = self._columnNames
		self._orderBy = sortColumnNames
		if reverse:
			self._orderBy = ",".join([
				f"{col[0]} DESC" for col in self._sortColumns
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
			log.error(f"error parsing index sql={sql!r}")
			return False
		j = sql.find(")", i)
		if j < 0:
			log.error(f"error parsing index sql={sql!r}")
			return False
		columnNames = sql[i + 1:j]
		self._sorted = True
		self._orderBy = columnNames
		return True

	def clear(self):
		self._con.execute(
			f"DELETE FROM data;"
		)
		self._con.commit()
		self._len = 0

	def close(self):
		if self._con is None:
			return
		self._con.commit()
		self._cur.close()
		self._con.close()
		self._con = None
		self._cur = None

	def __del__(self):
		self.close()
		if not self._persist and isfile(self._filename):
			os.remove(self._filename)

	def __iter__(self):
		query = f"SELECT pickle FROM data ORDER BY {self._orderBy}"
		self._cur.execute(query)
		for row in self._cur:
			yield loads(row[0])
