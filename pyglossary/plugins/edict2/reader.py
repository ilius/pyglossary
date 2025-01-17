from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.io_utils import nullTextIO

from .conv import (
	Article,
	parse_line_simp,
	parse_line_trad,
	render_article,
	render_syllables_color,
	render_syllables_no_color,
)

if TYPE_CHECKING:
	import io
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = True
	depends = {
		"lxml": "lxml",
	}

	_encoding: str = "utf-8"
	_traditional_title: bool = False
	_colorize_tones: bool = True

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self.file: io.TextIOBase = nullTextIO
		self._fileSize = 0

	def open(self, filename: str) -> None:
		# self._glos.sourceLangName = "Chinese"
		# self._glos.targetLangName = "English"

		cfile = self.file = open(filename, encoding=self._encoding)

		if cfile.seekable():
			cfile.seek(0, 2)
			self._fileSize = cfile.tell()
			cfile.seek(0)
			# self._glos.setInfo("input_file_size", f"{self._fileSize}")
		else:
			log.warning("EDICT2 Reader: file is not seekable")

	def close(self) -> None:
		self.file.close()
		self.file = nullTextIO

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType]:
		file = self.file
		fileSize = self._fileSize
		glos = self._glos

		render_syllables = (
			render_syllables_color
			if self._colorize_tones
			else render_syllables_no_color
		)
		parse_line = parse_line_trad if self._traditional_title else parse_line_simp

		while True:
			line = file.readline()
			if not line:
				break
			line = line.rstrip("\n")
			if not line:
				continue
			if line.startswith("#"):
				continue
			parts = parse_line(line)
			if parts is None:
				log.warning(f"bad line: {line!r}")
				continue
			names, article_text = render_article(
				render_syllables,
				Article(*parts),
			)
			entry = glos.newEntry(
				names,
				article_text,
				defiFormat="h",
				byteProgress=(file.tell(), fileSize) if fileSize else None,
			)
			yield entry
