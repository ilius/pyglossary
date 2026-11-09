"""
Write OpenZIM archives for Kiwix offline dictionaries.

Builds a ``.zim`` file from glossary entries using ``libzim``. Articles are
stored as HTML items under the ``A/`` namespace, alternate headwords become
aliases, and resources are stored under ``I/``. Glossary metadata is mapped to
the standard ZIM metadata fields.
"""

from __future__ import annotations

import os
import re
from contextlib import ExitStack
from datetime import UTC, datetime
from html import unescape
from os.path import splitext
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote
from xml.sax.saxutils import escape

from pyglossary.core import exc_note, log, pip
from pyglossary.glossary_utils import WriteError
from pyglossary.xdxf.py_transform import XdxfTransformer

if TYPE_CHECKING:
	from collections.abc import Generator

	from libzim.writer import ContentProvider, Creator

	from pyglossary.stubs.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]

_XDXF_TRANSFORMER: XdxfTransformer | None = None

_DEFAULT_LANGUAGE = "und"


def _today() -> str:
	return datetime.now(tz=UTC).date().isoformat()


def _xdxfToHtml(text: str) -> str:
	global _XDXF_TRANSFORMER
	if _XDXF_TRANSFORMER is None:
		_XDXF_TRANSFORMER = XdxfTransformer(encoding="utf-8")
	return _XDXF_TRANSFORMER.transformByInnerString(text)


class _ZimItem:
	"""An item added to a ZIM archive."""

	def __init__(  # noqa: PLR0913
		self,
		path: str,
		title: str,
		mimetype: str,
		content: bytes | None = None,
		filepath: str | None = None,
		frontArticle: bool = False,
		compress: bool = True,
	) -> None:
		self._path = path
		self._title = title
		self._mimetype = mimetype
		self._content = content
		self._filepath = filepath
		self._frontArticle = frontArticle
		self._compress = compress

	def get_path(self) -> str:
		return self._path

	def get_title(self) -> str:
		return self._title

	def get_mimetype(self) -> str:
		return self._mimetype

	def get_contentprovider(self) -> ContentProvider:
		from libzim.writer import FileProvider, StringProvider

		if self._filepath:
			return FileProvider(self._filepath)
		return StringProvider(self._content or b"")

	def get_hints(self) -> dict:
		from libzim.writer import Hint

		hints = {Hint.COMPRESS: self._compress}
		if self._frontArticle:
			hints[Hint.FRONT_ARTICLE] = True
		return hints


class Writer:
	"""Write glossary files in Zim format."""

	depends = {
		"libzim": "libzim>=4.0",
	}

	_compress: bool = True
	_indexing: bool = True
	_language: str = ""
	_word_title: bool = False
	_front_article: bool = True
	_verbose: bool = False

	resourceMimeTypes = {
		"bmp": "image/bmp",
		"gif": "image/gif",
		"ico": "image/x-icon",
		"jpeg": "image/jpeg",
		"jpg": "image/jpeg",
		"png": "image/png",
		"svg": "image/svg+xml",
		"tif": "image/tiff",
		"tiff": "image/tiff",
		"webp": "image/webp",
		"css": "text/css",
		"js": "application/javascript",
		"json": "application/json",
		"woff": "application/font-woff",
		"woff2": "application/font-woff2",
		"ttf": "application/x-font-ttf",
		"otf": "application/x-font-opentype",
		"eot": "application/vnd.ms-fontobject",
		"pdf": "application/pdf",
		"mp3": "audio/mpeg",
		"ogg": "audio/ogg",
		"opus": "audio/ogg",
		"oga": "audio/ogg",
		"spx": "audio/x-speex",
		"wav": "audio/wav",
		"mp4": "video/mp4",
		"m4a": "audio/mp4",
		"m4b": "audio/mp4",
		"aac": "audio/aac",
		"webm": "audio/webm",
		"weba": "audio/webm",
	}

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._stack: ExitStack | None = None
		self._creator: Creator | None = None
		self._usedPaths: set[str] = set()
		self._mainPathSet = False

	def _getInfo(self, key: str) -> str:
		return self._glos.getInfo(key).strip()

	def _getLanguage(self) -> str:
		if self._language:
			return self._language
		lang = self._glos.sourceLang
		if lang is not None:
			for code in lang.codes:
				if len(code) == 3:
					return code
			if lang.code:
				return lang.code
		return _DEFAULT_LANGUAGE

	def _uniquePath(self, term: str, prefix: str = "A/") -> str:
		base = prefix + quote(term, safe="")
		path = base
		index = 2
		while path in self._usedPaths:
			path = f"{base}_{index}"
			index += 1
		self._usedPaths.add(path)
		return path

	@staticmethod
	def _pathForTerm(term: str) -> str:
		return "A/" + quote(term, safe="")

	@staticmethod
	def _bwordTargetToPath(target: str) -> str:
		# bword targets are HTML-attribute escaped and URL-encoded
		# (see xdxf/py_transform.py), so decode both before re-encoding
		target = unquote(unescape(target))
		term, sep, fragment = target.partition("#")
		path = Writer._pathForTerm(term)
		if sep:
			path += "#" + quote(fragment, safe="")
		return path

	@staticmethod
	def _replaceBwordLinks(text: str) -> str:
		def repl(match: re.Match[str]) -> str:
			quoteChar = match.group("quote")
			path = Writer._bwordTargetToPath(match.group("target"))
			return f"{quoteChar}{path}{quoteChar}"

		return re.sub(
			r"(?P<quote>[\"'])bword://(?P<target>[^\"']*)(?P=quote)",
			repl,
			text,
		)

	def _defiToHtml(self, entry: EntryType) -> str:
		entry.detectDefiFormat()
		defiFormat = entry.defiFormat
		if defiFormat == "h":
			defi = entry.defi
		elif defiFormat == "x":
			defi = _xdxfToHtml(entry.defi)
		else:
			defi = f"<pre>{escape(entry.defi)}</pre>"

		defi = self._replaceBwordLinks(defi)

		if self._word_title:
			title = escape(entry.l_term[0])
			defi = f"<b>{title}</b><br>\n{defi}"

		return defi

	def _addMetadata(self, creator: Creator) -> None:
		name = self._getInfo("name")
		if not name:
			name = os.path.basename(self._filename)
			name = splitext(name)[0]
		if not name:
			name = "Glossary"

		title = self._getInfo("title") or name
		description = self._getInfo("description") or name
		author = self._getInfo("author") or "PyGlossary"
		publisher = self._getInfo("publisher") or author

		metadata = {
			"Name": name,
			"Title": title,
			"Language": self._getLanguage(),
			"Creator": author,
			"Publisher": publisher,
			"Description": description,
			"Date": self._getInfo("creationTime")[:10] or _today(),
		}
		license_ = self._getInfo("license")
		if license_:
			metadata["License"] = license_

		for key, value in metadata.items():
			creator.add_metadata(key, value)

	def open(self, filename: str) -> None:
		try:
			from libzim.writer import Compression, Creator
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install libzim` to install")
			raise

		if os.path.isfile(filename):
			raise WriteError(f"File '{filename}' already exists")

		self._filename = filename
		creator = Creator(filename)
		creator.config_verbose(self._verbose)
		creator.config_compression(
			Compression.zstd if self._compress else Compression.none,
		)
		if self._indexing:
			creator.config_indexing(True, self._getLanguage())
		self._stack = ExitStack()
		self._creator = self._stack.enter_context(creator)
		self._addMetadata(creator)

	def finish(self) -> None:
		stack = self._stack
		self._stack = None
		self._creator = None
		self._filename = ""
		if stack is None:
			return
		stack.close()

	def _addItem(self, item: _ZimItem) -> None:
		creator = self._creator
		if creator is None:
			raise ValueError("creator is None")
		creator.add_item(item)

	def _addDataEntry(self, entry: EntryType) -> None:
		relPath = entry.s_term.lstrip("/")
		_, ext = splitext(relPath)
		ext = ext.lstrip(os.extsep).lower()
		mimetype = self.resourceMimeTypes.get(ext, "application/octet-stream")
		path = self._uniquePath(relPath, prefix="I/")
		tmpPath = entry.tmpPath
		self._addItem(
			_ZimItem(
				path=path,
				title=entry.s_term,
				mimetype=mimetype,
				content=None if tmpPath else entry.data,
				filepath=tmpPath,
				frontArticle=False,
				compress=self._compress,
			),
		)

	def _addEntry(self, entry: EntryType) -> None:
		creator = self._creator
		if creator is None:
			raise ValueError("creator is None")

		terms = entry.l_term
		if not terms:
			log.warning("Zim writer: skipping entry with no headword")
			return

		headword = terms[0]
		defi = self._defiToHtml(entry)
		path = self._uniquePath(headword)
		if path != self._pathForTerm(headword):
			log.warning(
				f"Zim writer: duplicate headword {headword!r} stored as {path!r};"
				" links to it resolve to the first entry",
			)
		if not self._mainPathSet:
			creator.set_mainpath(path)
			self._mainPathSet = True
		self._addItem(
			_ZimItem(
				path=path,
				title=headword,
				mimetype="text/html; charset=utf-8",
				content=defi.encode("utf-8"),
				frontArticle=self._front_article,
				compress=self._compress,
			),
		)

		from libzim.writer import Hint

		hints = {Hint.FRONT_ARTICLE: True} if self._front_article else {}
		for term in terms[1:]:
			if not term or term == headword:
				continue
			aliasPath = self._uniquePath(term)
			creator.add_alias(aliasPath, term, path, hints)

	def write(self) -> Generator[None, EntryType, None]:
		while True:
			entry = yield
			if entry is None:
				return

			if entry.isData():
				self._addDataEntry(entry)
			else:
				self._addEntry(entry)
