"""
PyGlossary dict.cc format plugin.

SQLite3 databases exported from dict.cc vocabulary lists. Read-only ``Reader``
queries bilingual term pairs and example sentences from dict.cc ``.db`` archives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .reader import Reader

if TYPE_CHECKING:
	from pyglossary.option import Option


__all__ = [
	"Reader",
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
lname = "dict_cc"
name = "Dictcc"
description = "Dict.cc (SQLite3)"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/Dict.cc"
website = (
	"https://play.google.com/store/apps/details?id=cc.dict.dictcc",
	"dict.cc dictionary - Google Play",
)
relatedFormats: list[str] = ["Dictcc_split"]
optionsProp: dict[str, Option] = {}
