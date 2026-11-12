"""
Read OpenZIM archives used by Kiwix offline dictionaries.

Indexes ``.zim`` files and walks article entries to build glossary headwords from
titles. Extracts article HTML bodies as definitions and applies namespace and
redirect handling for offline Wikipedia-style content.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING
from xml.sax.saxutils import quoteattr

from pyglossary.core import cacheDir, exc_note, log, pip

if TYPE_CHECKING:
	from collections.abc import Iterator

	from libzim.reader import Archive, Entry

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType


__all__ = ["Reader"]


@dataclass
class _Stats:
	entryCount: int = 0
	emptyContentCount: int = 0
	invalidMimeTypeCount: int = 0
	undefinedMimeTypeCount: int = 0
	redirectCount: int = 0


class Reader:
	"""Read Zimfile glossary files."""

	_text_unicode_errors = "replace"
	_html_unicode_errors = "replace"
	useByteProgress = False
	depends = {
		"libzim": "libzim>=4.0",
	}

	resourceMimeTypes = {
		"image/png",
		"image/jpeg",
		"image/gif",
		"image/svg+xml",
		"image/webp",
		"image/x-icon",
		"text/css",
		"text/javascript",
		"application/javascript",
		"application/json",
		"application/octet-stream",
		"application/octet-stream+xapian",
		"application/x-chrome-extension",
		"application/warc-headers",
		"application/font-woff",
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		"""Store the target glossary and initialize an empty reader state."""
		self._glos = glos
		self._filename = ""
		self._zimfile: Archive | None = None

	def open(self, filename: str) -> None:
		"""Open the ZIM archive at ``filename`` for reading."""
		try:
			from libzim.reader import Archive
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install libzim` to install")
			raise

		self._filename = filename
		self._zimfile = Archive(filename)

	def close(self) -> None:
		"""Release the archive and reset the reader state."""
		self._filename = ""
		self._zimfile = None

	def countResourceFiles(self) -> int:
		"""Return the number of resource files; ZIM exposes them via entries."""
		return 0

	def __len__(self) -> int:
		"""Return the number of entries in the archive."""
		if self._zimfile is None:
			log.error("len(reader) called before reader.open()")
			return 0
		return self._zimfile.entry_count

	def __iter__(self) -> Iterator[EntryType | None]:
		"""Yield glossary entries for every entry in the archive."""
		zimfile = self._zimfile
		if zimfile is None:
			return

		stats = _Stats(entryCount=zimfile.entry_count)
		fNameMax = self._getFileNameMax()
		fileNameTooLong: list[str] = []

		for entryIndex in range(stats.entryCount):
			zEntry = zimfile.get_entry_by_id(entryIndex)
			yield from self._iterEntry(zEntry, stats, fileNameTooLong, fNameMax)

		self._logStats(stats, fileNameTooLong)

	@staticmethod
	def _getFileNameMax() -> int:
		"""Return the maximum file name length supported by the cache filesystem."""
		try:
			return os.statvfs(cacheDir).f_namemax
		except AttributeError:
			log.warning("Unsupported operating system (no os.statvfs)")
			# Windows: CreateFileA has a limit of 260 characters.
			# CreateFileW supports names up to about 32760 characters (64kB).
			return 200

	def _iterEntry(
		self,
		zEntry: Entry,
		stats: _Stats,
		fileNameTooLong: list[str],
		fNameMax: int,
	) -> Iterator[EntryType | None]:
		"""Yield entries derived from a single ZIM entry."""
		glos = self._glos
		term = zEntry.title

		if zEntry.is_redirect:
			stats.redirectCount += 1
			targetWord = zEntry.get_redirect_entry().title
			hrefQuoted = quoteattr("bword://" + targetWord)
			yield glos.newEntry(
				term,
				f"Redirect: <a href={hrefQuoted}>{targetWord}</a>",
				defiFormat="h",
			)
			return

		zItem = zEntry.get_item()
		b_content = zItem.content.tobytes()

		if not b_content:
			stats.emptyContentCount += 1
			yield None
			# TODO: test with more zim files
			# Looks like: zItem.path == zEntry.path == "-" + word
			# print(f"b_content empty, {word=}, {zEntry.path=}, {zItem.path=}")
			# if zEntry.path == "-" + word:
			# 	yield None
			# else:
			# 	defi = f"Path: {zEntry.path}"
			# 	yield glos.newEntry(word, defi, defiFormat="m")
			return

		try:
			mimetype = zItem.mimetype
		except RuntimeError:
			stats.invalidMimeTypeCount += 1
			mimetype = ""
			yield glos.newDataEntry(term, b_content)

		if mimetype == "undefined":
			stats.undefinedMimeTypeCount += 1
			return

		mimetype = mimetype.split(";")[0]

		if mimetype.startswith("text/html"):
			# can be "text/html;raw=true"
			defi = b_content.decode("utf-8", errors=self._html_unicode_errors)
			defi = defi.replace(' src="../I/', ' src="./')
			yield glos.newEntry(term, defi, defiFormat="h")
			return

		if mimetype == "text/plain":
			yield glos.newEntry(
				term,
				b_content.decode("utf-8", errors=self._text_unicode_errors),
				defiFormat="m",
			)
			return

		yield from self._iterResourceEntry(
			term,
			b_content,
			mimetype,
			fileNameTooLong,
			fNameMax,
		)

	def _iterResourceEntry(
		self,
		term: str,
		b_content: bytes,
		mimetype: str,
		fileNameTooLong: list[str],
		fNameMax: int,
	) -> Iterator[EntryType | None]:
		"""Yield a data entry for a non-text ZIM resource, if it is usable."""
		glos = self._glos

		if mimetype not in self.resourceMimeTypes:
			log.warning(f"Unrecognized {mimetype=}")

		if len(term) > fNameMax:
			fileNameTooLong.append(term)
			return

		if "|" in term:
			log.warning(f"resource title: {term}")
			if os.sep == "\\":
				return

		try:
			entry = glos.newDataEntry(term, b_content)
		except Exception as e:
			log.error(f"error creating file: {e}")
			return
		yield entry

	@staticmethod
	def _logStats(stats: _Stats, fileNameTooLong: list[str]) -> None:
		"""Log per-iteration counters and skipped-file information."""
		log.info(f"ZIM Entry Count: {stats.entryCount}")

		if fileNameTooLong:
			log.warning(f"Files with name too long: {len(fileNameTooLong)}")

		if stats.emptyContentCount > 0:
			log.info(f"Empty Content Count: {stats.emptyContentCount}")
		if stats.invalidMimeTypeCount > 0:
			log.info(f"Invalid MIME-Type Count: {stats.invalidMimeTypeCount}")
		if stats.undefinedMimeTypeCount > 0:
			log.info(
				f"MIME-Type 'undefined' Count: {stats.invalidMimeTypeCount}",
			)
		if stats.redirectCount > 0:
			log.info(f"Redirect Count: {stats.redirectCount}")
