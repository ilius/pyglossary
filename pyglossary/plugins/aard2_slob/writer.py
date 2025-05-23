# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
import shutil
from os.path import isfile, splitext
from typing import TYPE_CHECKING

from pyglossary.core import cacheDir, exc_note, log, pip
from pyglossary.glossary_utils import WriteError
from pyglossary.plugins.aard2_slob.tags import (
	t_created_at,
	t_created_by,
	t_label,
	t_uri,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary import slob
	from pyglossary.glossary_types import EntryType, WriterGlossaryType


__all__ = ["Writer"]


class Writer:
	depends = {
		"icu": "PyICU",
	}

	_compression: str = "zlib"
	_content_type: str = ""
	_file_size_approx: int = 0
	_file_size_approx_check_num_entries = 100
	_separate_alternates: bool = False
	_word_title: bool = False
	_version_info: bool = False

	_audio_goldendict: bool = False

	resourceMimeTypes = {
		"png": "image/png",
		"jpeg": "image/jpeg",
		"jpg": "image/jpeg",
		"gif": "image/gif",
		"svg": "image/svg+xml",
		"webp": "image/webp",
		"tiff": "image/tiff",
		"tif": "image/tiff",
		"bmp": "image/bmp",
		"css": "text/css",
		"js": "application/javascript",
		"json": "application/json",
		"woff": "application/font-woff",
		"woff2": "application/font-woff2",
		"ttf": "application/x-font-ttf",
		"otf": "application/x-font-opentype",
		"mp3": "audio/mpeg",
		"ogg": "audio/ogg",
		"opus": "audio/ogg",
		"oga": "audio/ogg",
		"spx": "audio/x-speex",
		"wav": "audio/wav",
		"ini": "text/plain",
		# "application/octet-stream+xapian",
		"eot": "application/vnd.ms-fontobject",
		"pdf": "application/pdf",
		"mp4": "video/mp4",
	}

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resPrefix = ""
		self._slobWriter: slob.Writer | None = None

	@staticmethod
	def _slobObserver(
		event: slob.WriterEvent,  # noqa: F401, F821
	) -> None:
		log.debug(f"slob: {event.name}{': ' + str(event.data) if event.data else ''}")

	def _open(self, filepath: str, namePostfix: str) -> slob.Writer:
		from pyglossary import slob

		if isfile(filepath):
			shutil.move(filepath, f"{filepath}.bak")
			log.warning(f"renamed existing {filepath!r} to {filepath + '.bak'!r}")
		self._slobWriter = slobWriter = slob.Writer(
			filepath,
			observer=self._slobObserver,
			workdir=cacheDir,
			compression=self._compression,
			version_info=self._version_info,
		)

		# "label" tag is a dictionary name shown in UI
		slobWriter.tag(t_label, self._glos.getInfo("name") + namePostfix)

		createdAt = self._glos.getInfo("creationTime")
		if createdAt is not None:
			slobWriter.tag(t_created_at, createdAt)
		createdBy = self._glos.getInfo("author")
		if createdBy is not None:
			slobWriter.tag(t_created_by, createdBy)

		filename = os.path.basename(filepath)
		dic_uri = re.sub(r"[^A-Za-z0-9_-]+", "_", filename)
		# "uri" tag is not web url, it's a part of gloss addressing ID: uri + article ID
		# setting the tag allows bookmark & history migration, if dict file is updated
		# we use source filename as "uri", since it is stable (most likely)
		slobWriter.tag(t_uri, dic_uri)

		return slobWriter

	def open(self, filename: str) -> None:
		try:
			import icu  # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install PyICU` to install")
			raise
		if isfile(filename):
			raise WriteError(f"File '{filename}' already exists")
		namePostfix = ""
		if self._file_size_approx > 0:
			namePostfix = " (part 1)"
		self._open(filename, namePostfix)
		self._filename = filename

	def finish(self) -> None:
		from time import perf_counter

		self._filename = ""
		if self._slobWriter is None:
			return
		log.info("Finalizing slob file...")
		t0 = perf_counter()
		self._slobWriter.finalize()
		log.info(f"Finalizing slob file took {perf_counter() - t0:.1f} seconds")
		self._slobWriter = None

	def addDataEntry(self, entry: EntryType) -> None:
		slobWriter = self._slobWriter
		if slobWriter is None:
			raise ValueError("slobWriter is None")
		rel_path = entry.s_word
		_, ext = splitext(rel_path)
		ext = ext.lstrip(os.path.extsep).lower()
		content_type = self.resourceMimeTypes.get(ext)
		if not content_type:
			log.error(f"Aard2 slob: unknown content type for {rel_path!r}")
			return
		content = entry.data
		key = self._resPrefix + rel_path
		try:
			key.encode(slobWriter.encoding)
		except UnicodeEncodeError:
			log.error(f"Failed to add, broken unicode in key: {key!a}")
			return
		slobWriter.add(content, key, content_type=content_type)

	def addEntry(self, entry: EntryType) -> None:
		words = entry.l_word
		b_defi = entry.defi.encode("utf-8")
		ctype = self._content_type
		writer = self._slobWriter
		if writer is None:
			raise ValueError("slobWriter is None")

		entry.detectDefiFormat()
		defiFormat = entry.defiFormat

		if self._word_title and defiFormat in {"h", "m"}:
			if defiFormat == "m":
				defiFormat = "h"
			title = self._glos.wordTitleStr(
				words[0],
			)
			b_defi = title.encode("utf-8") + b_defi

		if defiFormat == "h":
			b_defi = b_defi.replace(b'"bword://', b'"')
			b_defi = b_defi.replace(b"'bword://", b"'")

			if not self._audio_goldendict:
				b_defi = b_defi.replace(
					b"""href="sound://""",
					b'''onclick="new Audio(this.href).play(); return false;" href="''',
				)
				b_defi = b_defi.replace(
					b"""href='sound://""",
					b"""onclick="new Audio(this.href).play(); return false;" href='""",
				)
				b_defi = b_defi.replace(b"""<img src="/""", b'''<img src="''')
				b_defi = b_defi.replace(b"""<img src='""", b"""<img src='""")
				b_defi = b_defi.replace(b"""<img src="file:///""", b'''<img src="''')
				b_defi = b_defi.replace(b"""<img src='file:///""", b"""<img src='""")

		if not ctype:
			if defiFormat == "h":
				ctype = "text/html; charset=utf-8"
			elif defiFormat == "m":
				ctype = "text/plain; charset=utf-8"
			else:
				ctype = "text/plain; charset=utf-8"

		if not self._separate_alternates:
			writer.add(
				b_defi,
				*tuple(words),
				content_type=ctype,
			)
			return

		headword, *alts = words
		writer.add(
			b_defi,
			headword,
			content_type=ctype,
		)
		for alt in alts:
			writer.add(
				b_defi,
				f"{alt}, {headword}",
				content_type=ctype,
			)

	def write(self) -> Generator[None, EntryType, None]:
		slobWriter = self._slobWriter
		if slobWriter is None:
			raise ValueError("slobWriter is None")
		file_size_approx = int(self._file_size_approx * 0.95)
		entryCount = 0
		sumBlobSize = 0
		fileIndex = 0
		filenameNoExt, _ = splitext(self._filename)
		while True:
			entry = yield
			if entry is None:
				break

			if entry.isData():
				self.addDataEntry(entry)
			else:
				self.addEntry(entry)

			if file_size_approx <= 0:
				continue

			# handle file_size_approx
			check_every = self._file_size_approx_check_num_entries
			entryCount += 1
			if entryCount % check_every == 0:
				sumBlobSize = slobWriter.size_data()
				if sumBlobSize >= file_size_approx:
					slobWriter.finalize()
					fileIndex += 1
					slobWriter = self._open(
						f"{filenameNoExt}.{fileIndex}.slob",
						f" (part {fileIndex + 1})",
					)
					sumBlobSize = 0
					entryCount = 0
