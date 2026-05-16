# -*- coding: utf-8 -*-
from __future__ import annotations

from html import escape as html_escape
from typing import TYPE_CHECKING

from pyglossary.core import log

if TYPE_CHECKING:
	import sqlite3
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]

_SQLITE_MAGIC = b"SQLite format 3\x00"
_COLLECTION_NAMES = (
	"collection.anki21",
	"collection.anki2",
	"collection.anki21b",
)


class Reader:
	r"""
	Read notes from Anki deck/collection packages (.apkg / .colpkg).

	Archives are zips containing a SQLite ``collection.anki*`` database; note
	fields are stored in ``notes.flds`` separated by ``\\x1f`` (same layout
	consumed by community tools such as anki-export and AnkiTools).
	"""

	useByteProgress = False

	_word_field: int = 0
	_include_tags: bool = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._tmp_path = ""
		self._con: sqlite3.Connection | None = None
		self._cur: sqlite3.Cursor | None = None

	def open(self, filename: str) -> None:
		import os
		import tempfile
		from sqlite3 import connect
		from zipfile import BadZipFile, ZipFile

		self._clear()
		self._filename = filename

		try:
			zf = ZipFile(filename)
		except BadZipFile as e:
			raise LookupError(
				f"Not a zip archive (expected Anki .apkg / .colpkg): {filename!r}",
			) from e

		with zf:
			col_sqlite: bytes | None = None
			col_member = ""
			for cand in _COLLECTION_NAMES:
				if cand not in zf.namelist():
					continue
				raw = zf.read(cand)
				if len(raw) >= 16 and raw[:16] == _SQLITE_MAGIC:
					col_sqlite = raw
					col_member = cand
					break
				log.warning("%s is not SQLite, skipping", cand)

		if col_sqlite is None:
			raise LookupError(
				"No SQLite collection database found (expected one of "
				f"{', '.join(_COLLECTION_NAMES)}). "
				"If this package uses a newer Anki storage layout, try exporting "
				"with an older Anki version or use a dedicated exporter "
				"(for example https://github.com/patarapolw/anki-export ).",
			)

		fd, self._tmp_path = tempfile.mkstemp(prefix="pyglossary-anki-", suffix=".sqlite")
		try:
			os.close(fd)
			with open(self._tmp_path, "wb") as fp:
				fp.write(col_sqlite)
			self._con = connect(self._tmp_path)
			self._cur = self._con.cursor()
			self._cur.execute(
				"SELECT name FROM sqlite_master WHERE type='table' AND name='notes'",
			)
			if self._cur.fetchone() is None:
				raise LookupError("SQLite database has no 'notes' table")
			self._glos.setDefaultDefiFormat("h")
			self._glos.setInfo("anki_collection_db", col_member)
		except Exception:
			self.close()
			raise

	def __len__(self) -> int:
		if self._cur is None:
			raise RuntimeError("len(reader) called while reader is not open")
		self._cur.execute("SELECT count(*) FROM notes")
		row = self._cur.fetchone()
		return int(row[0]) if row else 0

	def __iter__(self) -> Iterator[EntryType]:
		if self._cur is None:
			raise RuntimeError("iter(reader) called while reader is not open")

		self._cur.execute("SELECT flds, tags FROM notes")
		idx = self._word_field
		for flds, tags in self._cur.fetchall():
			if not isinstance(flds, str):
				flds = str(flds)
			fields = flds.split("\x1f")
			if not fields or all(not p.strip() for p in fields):
				continue
			if idx < 0 or idx >= len(fields):
				log.warning(
					f"Skipping note: word_field={idx} but note has {len(fields)} field(s)",
				)
				continue
			term = fields[idx].strip()
			if not term:
				continue
			other = fields[:idx] + fields[idx + 1 :]
			defi = "<br>\n".join(other)
			if self._include_tags and isinstance(tags, str) and tags.strip():
				defi = f'<div class="anki-tags">{html_escape(tags.strip())}</div>\n{defi}'
			yield self._glos.newEntry(term, defi, defiFormat="h")

	def close(self) -> None:
		import os

		if self._cur:
			self._cur.close()
			self._cur = None
		if self._con:
			self._con.close()
			self._con = None
		if self._tmp_path:
			try:
				os.remove(self._tmp_path)
			except OSError:
				log.exception("Could not remove temporary file %s", self._tmp_path)
			self._tmp_path = ""
