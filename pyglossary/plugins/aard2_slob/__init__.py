# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
import shutil
from os.path import isfile, splitext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Generator, Iterator

	from pyglossary import slob
	from pyglossary.glossary_types import EntryType, GlossaryType

from pyglossary.core import cacheDir, exc_note, log, pip
from pyglossary.option import (
	BoolOption,
	FileSizeOption,
	IntOption,
	Option,
	StrOption,
)

__all__ = [
	"Reader",
	"Writer",
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
lname = "aard2_slob"
name = "Aard2Slob"
description = "Aard 2 (.slob)"
extensions = (".slob",)
extensionCreate = ".slob"
singleFile = True
kind = "binary"
wiki = "https://github.com/itkach/slob/wiki"
website = (
	"http://aarddict.org/",
	"aarddict.org",
)
optionsProp: dict[str, Option] = {
	"compression": StrOption(
		values=["", "bz2", "zlib", "lzma2"],
		comment="Compression Algorithm",
	),
	"content_type": StrOption(
		customValue=True,
		values=[
			"text/plain; charset=utf-8",
			"text/html; charset=utf-8",
		],
		comment="Content Type",
	),
	# "encoding": EncodingOption(),
	"file_size_approx": FileSizeOption(
		comment="split up by given approximate file size\nexamples: 100m, 1g",
	),
	"file_size_approx_check_num_entries": IntOption(
		comment="for file_size_approx, check every `[?]` entries",
	),
	"separate_alternates": BoolOption(
		comment="add alternate headwords as separate entries to slob",
	),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
	"version_info": BoolOption(
		comment="add version info tags to slob file",
	),
	"audio_goldendict": BoolOption(
		comment="Convert audio links for GoldenDict (desktop)",
	),
}

extraDocs = [
	(
		"PyICU",
		"See [doc/pyicu.md](./doc/pyicu.md) file for more detailed"
		" instructions on how to install PyICU.",
	),
]

t_created_at = "created.at"
t_label = "label"
t_created_by = "created.by"
t_copyright = "copyright"
t_license_name = "license.name"
t_license_url = "license.url"
t_uri = "uri"
t_edition = "edition"

supported_tags = {
	t_label,
	t_created_at,
	t_created_by,
	t_copyright,
	t_uri,
	t_edition,
}


class Reader:
	depends = {
		"icu": "PyICU",  # >=1.5
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._clear()
		self._re_bword = re.compile(
			"(<a href=[^<>]+?>)",
			re.IGNORECASE,
		)

	def close(self) -> None:
		if self._slobObj is not None:
			self._slobObj.close()
		self._clear()

	def _clear(self) -> None:
		self._filename = ""
		self._slobObj: slob.Slob | None = None

	# TODO: PLR0912 Too many branches (13 > 12)
	def open(self, filename: str) -> None:  # noqa: PLR0912
		try:
			import icu  # type: ignore # noqa: F401
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install PyICU` to install")
			raise
		from pyglossary import slob

		self._filename = filename
		self._slobObj = slob.open(filename)
		tags = dict(self._slobObj.tags.items())

		if t_label in tags:
			self._glos.setInfo("name", tags[t_label])

		if t_created_at in tags:
			self._glos.setInfo("creationTime", tags[t_created_at])

		if t_created_by in tags:
			self._glos.setInfo("author", tags[t_created_by])

		copyrightLines: list[str] = []
		for key in (t_copyright, t_license_name, t_license_url):
			try:
				value = tags.pop(key)
			except KeyError:
				continue
			copyrightLines.append(value)
		if copyrightLines:
			self._glos.setInfo("copyright", "\n".join(copyrightLines))

		if t_uri in tags:
			self._glos.setInfo("website", tags[t_uri])

		if t_edition in tags:
			self._glos.setInfo("edition", tags[t_edition])

		for key, value in tags.items():
			if key in supported_tags:
				continue
			self._glos.setInfo(f"slob.{key}", value)

	def __len__(self) -> int:
		if self._slobObj is None:
			log.error("called len() on a reader which is not open")
			return 0
		return len(self._slobObj)

	@staticmethod
	def _href_sub(m: re.Match) -> str:
		st = m.group(0)
		if "//" in st:
			return st
		return st.replace('href="', 'href="bword://').replace(
			"href='",
			"href='bword://",
		)

	def __iter__(self) -> Iterator[EntryType | None]:
		from pyglossary.slob import MIME_HTML, MIME_TEXT

		if self._slobObj is None:
			raise RuntimeError("iterating over a reader while it's not open")

		slobObj = self._slobObj
		blobSet = set()

		# slob library gives duplicate blobs when iterating over slobObj
		# even keeping the last id is not enough, since duplicate blobs
		# are not all consecutive. so we have to keep a set of blob IDs

		for blob in slobObj:
			id_ = blob.identity
			if id_ in blobSet:
				yield None  # update progressbar
				continue
			blobSet.add(id_)

			# blob.key is str, blob.content is bytes
			word = blob.key

			ctype = blob.content_type.split(";")[0]
			if ctype not in {MIME_HTML, MIME_TEXT}:
				log.debug(f"unknown {blob.content_type=} in {word=}")
				word = word.removeprefix("~/")
				yield self._glos.newDataEntry(word, blob.content)
				continue
			defiFormat = ""
			if ctype == MIME_HTML:
				defiFormat = "h"
			elif ctype == MIME_TEXT:
				defiFormat = "m"

			defi = blob.content.decode("utf-8")
			defi = self._re_bword.sub(self._href_sub, defi)
			yield self._glos.newEntry(word, defi, defiFormat=defiFormat)


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
		"spx": "audio/x-speex",
		"wav": "audio/wav",
		"ini": "text/plain",
		# "application/octet-stream+xapian",
		"eot": "application/vnd.ms-fontobject",
		"pdf": "application/pdf",
		"mp4": "video/mp4",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._resPrefix = ""
		self._slobWriter: slob.Writer | None = None

	@staticmethod
	def _slobObserver(
		event: slob.WriterEvent,  # noqa: F401, F821
	) -> None:
		log.debug(f"slob: {event.name}{': ' + event.data if event.data else ''}")

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
			raise OSError(f"File '{filename}' already exists")
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
