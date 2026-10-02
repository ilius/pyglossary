# Copyright (C) 2026 glowinthedark
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import html
import os
from typing import TYPE_CHECKING

from pyglossary.core import log

from . import wumd

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]

# Info keys the header has its own place for, or that describe the conversion
# rather than the dictionary.
_OWN_KEYS = frozenset((
	"name", "title", "sourcelang", "targetlang", "description", "input_file_size",
	"sourcelangcode", "targetlangcode",
))  # fmt: skip


def _text_html(s: str) -> str:
	"""A plain-text definition as HTML."""
	return "<p>" + html.escape(s, quote=False).replace("\n", "<br/>") + "</p>"


class Writer:
	depends = {"markdown_it": "markdown-it-py"}

	_mode: str = "html"
	_resources: bool = True

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._file: io.TextIOWrapper | None = None
		self._filename = ""
		self._resDir = ""
		self._done = False  # every entry written: the file can take its name
		self.empty = self.nameless = self.repaired = 0

	def _body(self, src: str) -> str:
		return wumd.html_body(src) if self._mode == "html" else wumd.clean_body(src)

	def _repair(self, s: str) -> str:
		"""R6.2, counting what it has to change."""
		r = wumd.repair_name(s)
		self.repaired += r != s.strip(" ")
		return r

	def _header(self, stem: str) -> str:
		"""R6.1: the title, the header fields and the description."""
		glos = self._glos
		name = (
			self._repair(glos.getInfo("name") or "") or self._repair(stem) or "dictionary"
		)
		out = ["# " + wumd.heading_esc(name), "wudict: 1"]
		for key, lang in (("from", glos.sourceLang), ("to", glos.targetLang)):
			if lang and (code := self._repair(lang.code)):
				out.append(f"{key}: {code}")
		for key, value in glos.iterInfo():
			if key.lower() in _OWN_KEYS or not (v := self._repair(value)):
				continue
			if key == "meta":  # this format's own escape, read back as is
				out.append("meta: " + v)
			elif k := wumd.field_key(key):
				out.append(f"{k}: {v}")
			elif k := self._repair(key):
				out.append(f"meta: {k}: {v}")
		text = "\n".join(out)
		if desc := glos.getInfo("description"):
			try:
				md = self._body(desc if "<" in desc and ">" in desc else _text_html(desc))
			except wumd.CleanError as e:
				raise ValueError(f"the description: {e}") from e
			if md:
				text += "\n\n" + md
		return text

	def open(self, filename: str) -> None:
		if self._mode not in ("clean", "html"):
			raise ValueError(f"mode {self._mode!r}: want clean or html")
		base = filename[:-3] if filename.lower().endswith(".md") else filename
		header = self._header(os.path.basename(base))
		self._filename = filename
		self._resDir = base + ".files"  # R2.3
		self._file = open(filename + ".tmp", "w", encoding="utf-8", newline="\n")
		self._file.write(header)

	def write(self) -> Generator[None, EntryType, None]:
		index = 0
		while (entry := (yield)) is not None:
			if entry.isData():
				if self._resources:
					os.makedirs(self._resDir, exist_ok=True)
					entry.save(self._resDir)
				continue
			index += 1
			names: list[str] = []
			for n in entry.l_term:
				if (n := self._repair(n)) and n not in names:
					names.append(n)
			if not names:
				self.nameless += 1
				continue
			# A reader may leave the format "m" and the writer detect HTML.
			src = (
				entry.defi
				if entry.detectDefiFormat("m") == "h"
				else _text_html(entry.defi)
			)
			try:
				md = self._body(src)
			except wumd.CleanError as e:
				# R6.8: the raw entry on stdout, and how to keep its HTML.
				print("\n".join("## " + n for n in names) + "\n\n" + src)  # noqa: T201
				raise ValueError(
					f"entry {names[0]!r} (#{index}): {e}\n"
					"hint: keep the dictionary's HTML instead: --write-options=mode=html",
				) from e
			if not md:
				self.empty += 1
				continue
			heads = "\n".join("## " + wumd.heading_esc(n) for n in names)
			self._file.write(f"\n\n{heads}\n\n{md}")
		self._done = True

	def finish(self) -> None:
		f, self._file = self._file, None
		if f is None:
			return
		tmp = self._filename + ".tmp"
		if not self._done:  # failed: no partial output (R6.8)
			f.close()
			os.remove(tmp)
			return
		f.write("\n")
		f.close()
		os.replace(tmp, self._filename)
		for n, what in (
			(self.empty, "article(s) with an empty body left out"),
			(self.nameless, "entry(ies) without a headword left out"),
			(self.repaired, "name(s) or value(s) repaired"),
		):
			if n:
				log.info(f"{n} {what}")
		if os.path.isdir(self._resDir) and not os.listdir(self._resDir):
			os.rmdir(self._resDir)
