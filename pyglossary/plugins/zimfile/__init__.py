# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterator

	from libzim.reader import Archive  # type: ignore

	from pyglossary.glossary_types import EntryType, GlossaryType
	from pyglossary.option import Option

from pyglossary.core import cacheDir, exc_note, log, pip
from pyglossary.option import UnicodeErrorsOption

__all__ = [
	"Reader",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "zim"
name = "Zim"
description = "Zim (.zim, for Kiwix)"
extensions = (".zim",)
extensionCreate = ".zim"
singleFile = True
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/ZIM_(file_format)"
website = (
	"https://wiki.openzim.org/wiki/OpenZIM",
	"OpenZIM",
)
optionsProp: dict[str, Option] = {
	"text_unicode_errors": UnicodeErrorsOption(
		comment="Unicode Errors for plaintext, values: `strict`, `ignore`, `replace`",
	),
	"html_unicode_errors": UnicodeErrorsOption(
		comment="Unicode Errors for HTML, values: `strict`, `ignore`, `replace`",
	),
}

# https://wiki.kiwix.org/wiki/Software

# to download zim files:
# https://archive.org/details/zimarchive
# https://dumps.wikimedia.org/other/kiwix/zim/

# I can't find any way to download zim files from https://library.kiwix.org/
# which wiki.openzim.org points at for downloaing zim files


class Reader:
	_text_unicode_errors = "replace"
	_html_unicode_errors = "replace"
	depends = {
		"libzim": "libzim>=1.0",
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

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._zimfile: Archive | None = None

	def open(self, filename: str) -> None:
		try:
			from libzim.reader import Archive
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install libzim` to install")
			raise

		self._filename = filename
		self._zimfile = Archive(filename)

	def close(self) -> None:
		self._filename = ""
		self._zimfile = None

	def __len__(self) -> int:
		if self._zimfile is None:
			log.error("len(reader) called before reader.open()")
			return 0
		return self._zimfile.entry_count

	def __iter__(self) -> Iterator[EntryType | None]:  # noqa: PLR0912
		glos = self._glos
		zimfile = self._zimfile
		if zimfile is None:
			return
		emptyContentCount = 0
		invalidMimeTypeCount = 0
		undefinedMimeTypeCount = 0
		entryCount = zimfile.entry_count

		redirectCount = 0

		windows = os.sep == "\\"

		try:
			f_namemax = os.statvfs(cacheDir).f_namemax  # type: ignore
		except AttributeError:
			log.warning("Unsupported operating system (no os.statvfs)")
			# Windows: CreateFileA has a limit of 260 characters.
			# CreateFileW supports names up to about 32760 characters (64kB).
			f_namemax = 200

		fileNameTooLong: list[str] = []

		text_unicode_errors = self._text_unicode_errors
		html_unicode_errors = self._html_unicode_errors

		for entryIndex in range(entryCount):
			zEntry = zimfile._get_entry_by_id(entryIndex)
			word = zEntry.title

			if zEntry.is_redirect:
				redirectCount += 1
				targetWord = zEntry.get_redirect_entry().title
				yield glos.newEntry(
					word,
					f'Redirect: <a href="bword://{targetWord}">{targetWord}</a>',
					defiFormat="h",
				)
				continue

			zItem = zEntry.get_item()
			b_content = zItem.content.tobytes()

			if not b_content:
				emptyContentCount += 1
				yield None
				# TODO: test with more zim files
				# Looks like: zItem.path == zEntry.path == "-" + word
				# print(f"b_content empty, {word=}, {zEntry.path=}, {zItem.path=}")
				# if zEntry.path == "-" + word:
				# 	yield None
				# else:
				# 	defi = f"Path: {zEntry.path}"
				# 	yield glos.newEntry(word, defi, defiFormat="m")
				continue

			try:
				mimetype = zItem.mimetype
			except RuntimeError:
				invalidMimeTypeCount += 1
				mimetype = ""
				yield glos.newDataEntry(word, b_content)

			if mimetype == "undefined":
				undefinedMimeTypeCount += 1
				continue

			mimetype = mimetype.split(";")[0]

			if mimetype.startswith("text/html"):
				# can be "text/html;raw=true"
				defi = b_content.decode("utf-8", errors=html_unicode_errors)
				defi = defi.replace(' src="../I/', ' src="./')
				yield glos.newEntry(word, defi, defiFormat="h")
				continue

			if mimetype == "text/plain":
				yield glos.newEntry(
					word,
					b_content.decode("utf-8", errors=text_unicode_errors),
					defiFormat="m",
				)
				continue

			if mimetype not in self.resourceMimeTypes:
				log.warning(f"Unrecognized {mimetype=}")

			if len(word) > f_namemax:
				fileNameTooLong.append(word)
				continue

			if "|" in word:
				log.warning(f"resource title: {word}")
				if windows:
					continue

			try:
				entry = glos.newDataEntry(word, b_content)
			except Exception as e:
				log.error(f"error creating file: {e}")
				continue
			yield entry

		log.info(f"ZIM Entry Count: {entryCount}")

		if fileNameTooLong:
			log.warning(f"Files with name too long: {len(fileNameTooLong)}")

		if emptyContentCount > 0:
			log.info(f"Empty Content Count: {emptyContentCount}")
		if invalidMimeTypeCount > 0:
			log.info(f"Invalid MIME-Type Count: {invalidMimeTypeCount}")
		if undefinedMimeTypeCount > 0:
			log.info(f"MIME-Type 'undefined' Count: {invalidMimeTypeCount}")
		if redirectCount > 0:
			log.info(f"Redirect Count: {redirectCount}")
