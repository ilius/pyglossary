# Copyright (C) 2026 glowinthedark
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import posixpath
import zipfile
from typing import TYPE_CHECKING

from pyglossary.core import log

from . import wumd

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]

_MAX_WARNINGS = 100  # logged one by one; the rest are counted


def _container_base(filename: str) -> str:
	"""
	The name the resource container is named after (R2.3): the file's
	name without its compression suffix and its final `.md`.
	"""
	base = filename[:-3] if filename.lower().endswith((".gz", ".dz")) else filename
	return base[:-3] if base.lower().endswith(".md") else base


class Reader:
	depends = {"markdown_it": "markdown-it-py"}
	compressions = ("gz", "dz")  # read here, with decompression bounded (R2.4)

	_resources: bool = True

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._doc: wumd.Document | None = None
		self._resDir = ""
		self._resZip = ""

	def open(self, filename: str) -> None:
		try:
			doc = wumd.read_text(wumd.load(filename))
		except wumd.FormatError as e:
			raise ValueError(f"{filename}: {e}") from e
		name = os.path.basename(filename)
		for w in doc.warnings[:_MAX_WARNINGS]:
			log.warning(f"{name}: {w}")
		if len(doc.warnings) > _MAX_WARNINGS:
			log.warning(
				f"{name}: {len(doc.warnings) - _MAX_WARNINGS} more entry warnings"
			)
		self._doc = doc
		glos, meta = self._glos, doc.meta
		glos.setInfo("name", meta["name"])
		# BCP 47 tags, as their primary language: pyglossary knows no regions
		if meta["from"]:
			glos.setInfo("sourceLang", meta["from"].partition("-")[0])
		if meta["to"]:
			glos.setInfo("targetLang", meta["to"].partition("-")[0])
		for key, value in meta["fields"]:
			glos.setInfo(key, value)
		if meta["description"]:
			glos.setInfo("description", meta["description"])
		if self._resources:
			base = _container_base(filename)
			if os.path.isdir(base + ".files"):
				self._resDir = base + ".files"
			elif os.path.isfile(base + ".files.zip"):
				self._resZip = base + ".files.zip"

	def close(self) -> None:
		self._doc = None

	def __len__(self) -> int:
		return len(self._doc) if self._doc is not None else 0

	def __iter__(self) -> Iterator[EntryType | None]:
		if self._doc is None:
			raise RuntimeError("iterating over a reader while it's not open")
		glos = self._glos
		for names, body in self._doc:
			yield glos.newEntry(names, body, defiFormat="h")
		if self._resDir:
			yield from self._dirResources()
		elif self._resZip:
			yield from self._zipResources()

	def _dirResources(self) -> Iterator[EntryType]:
		# Nothing outside the container is read, symlinks included (R2.3).
		root = os.path.realpath(self._resDir)
		for parent, dirs, files in os.walk(root):
			dirs.sort()
			for f in sorted(files):
				path = os.path.join(parent, f)
				if not os.path.realpath(path).startswith(root + os.sep):
					log.warning(f"skipping {path}: it leads out of {self._resDir}")
					continue
				with open(path, "rb") as fh:
					data = fh.read()
				yield self._glos.newDataEntry(
					os.path.relpath(path, root).replace(os.sep, "/"), data
				)

	def _zipResources(self) -> Iterator[EntryType]:
		with zipfile.ZipFile(self._resZip) as z:
			for info in z.infolist():
				if info.is_dir():
					continue
				if info.file_size > wumd.MAX_MARKDOWN:
					log.warning(f"{self._resZip}: skipping {info.filename!r}: too large")
					continue
				# `.` and `..` resolve at the container's root (R2.3)
				name = posixpath.normpath("/" + info.filename)[1:]
				yield self._glos.newDataEntry(name, z.read(info))
