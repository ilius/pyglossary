# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.core import log

if TYPE_CHECKING:
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
		# filename = self._filename
		# log.info(f"some useful message")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				# can save it with entry.save(directory)
				continue
			# term = entry.s_term
			# defi = entry.defi
			# here write word and defi to the output file (depending on
			# your format)
		# here read info from Glossaey object
		name = glos.getInfo("name")
		desc = glos.getInfo("description")
		author = glos.author
		copyright_ = glos.getInfo("copyright")
		# if an info key doesn't exist, getInfo returns empty string
		# now write info to the output file (depending on your output format)
		log.info(f"{name=}")
		log.info(f"{desc=}")
		log.info(f"{author=}")
		log.info(f"{copyright_=}")

	def finish(self) -> None:
		self._filename = ""
