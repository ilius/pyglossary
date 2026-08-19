"""
Read PyGlossary ``.info`` glossary metadata files.

Parses glossary info sidecar files that describe source format, languages, and
conversion options. Yields a single informational entry or merges metadata into
the active glossary context during import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import (
		EntryType,
		ReaderGlossaryType,
	)

__all__ = ["Reader"]


class Reader:
	"""Read glossary info glossary files."""

	useByteProgress = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos

	def close(self) -> None:
		pass

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToData

		with open(filename, encoding="utf-8") as infoFp:
			info = jsonToData(infoFp.read())
		assert isinstance(info, dict), f"{info=}"
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType | None]:
		yield None
