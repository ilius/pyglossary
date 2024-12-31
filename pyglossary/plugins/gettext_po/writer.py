# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.core import exc_note, pip
from pyglossary.io_utils import nullTextIO

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, GlossaryType


class Writer:
	depends = {
		"polib": "polib",
	}

	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		glos.preventDuplicateWords()

	def open(self, filename: str) -> None:
		try:
			from polib import escape as po_escape
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install polib` to install")
			raise

		self._filename = filename
		self._file = file = open(filename, mode="w", encoding="utf-8")
		file.write('#\nmsgid ""\nmsgstr ""\n')
		for key, value in self._glos.iterInfo():
			file.write(f'"{po_escape(key)}: {po_escape(value)}\\n"\n')

	def finish(self) -> None:
		self._filename = ""
		self._file.close()
		self._file = nullTextIO

	def write(self) -> Generator[None, EntryType, None]:
		from polib import escape as po_escape

		file = self._file

		resources = self._resources
		filename = self._filename
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(filename + "_res")
				continue
			file.write(
				f'msgid "{po_escape(entry.s_word)}"\n'
				f'msgstr "{po_escape(entry.defi)}"\n\n',
			)
