# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.info_writer import InfoWriter as Writer

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import (
		EntryType,
		GlossaryType,
	)
	from pyglossary.option import Option

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
lname = "info"
name = "Info"
description = "Glossary Info (.info)"
extensions = (".info",)
extensionCreate = ".info"
singleFile = True
kind = "text"
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp: dict[str, Option] = {}


class Reader:
	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def close(self) -> None:
		pass

	def open(self, filename: str) -> None:
		from pyglossary.json_utils import jsonToData

		with open(filename, encoding="utf-8") as infoFp:
			info = jsonToData(infoFp.read())
		for key, value in info.items():
			self._glos.setInfo(key, value)

	def __len__(self) -> int:
		return 0

	def __iter__(self) -> Iterator[EntryType | None]:
		yield None
