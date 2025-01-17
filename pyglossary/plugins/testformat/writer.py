

from __future__ import annotations

# -*- coding: utf-8 -*-
from collections.abc import Generator

from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]

class Writer:
	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename

	def write(self) -> Generator[None, EntryType, None]:
		glos = self._glos
		filename = self._filename  # noqa
		# log.info(f"some useful message")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# can save it with entry.save(directory)
				continue
			word = entry.s_word  # noqa
			defi = entry.defi  # noqa
			# here write word and defi to the output file (depending on
			# your format)
		# here read info from Glossaey object
		name = glos.getInfo("name")  # noqa
		desc = glos.getInfo("description")  # noqa
		author = glos.author  # noqa
		copyright = glos.getInfo("copyright")  # noqa
		# if an info key doesn't exist, getInfo returns empty string
		# now write info to the output file (depending on your output format)

	def finish(self) -> None:
		self._filename = ""
