"""
PyGlossary dict.cc split format plugin.

Split SQLite3 dict.cc databases spread across multiple ``.db`` files. Read-only
``Reader`` aggregates shards into a single glossary view for large dict.cc
exports.
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
lname = "dict_cc_split"
name = "Dictcc_split"
description = "Dict.cc (SQLite3) - Split"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/Dict.cc"
website = (
	"https://play.google.com/store/apps/details?id=cc.dict.dictcc",
	"dict.cc dictionary - Google Play",
)
relatedFormats: list[str] = ["Dictcc"]
optionsProp: dict[str, Option] = {}
