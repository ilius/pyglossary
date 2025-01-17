# -*- coding: utf-8 -*-

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
	useByteProgress = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos

	def close(self) -> None:
		pass

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToData

		with open(filename, encoding="utf-8") as infoFp:
			info = jsonToData(infoFp.read())
		assert isinstance(info, dict)
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType | None]:
		yield None
