# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import BoolOption

from .reader import Reader
from .writer import Writer

if TYPE_CHECKING:
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
lname = "ayandict_sqlite"
name = "AyanDictSQLite"
description = "AyanDict SQLite"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://github.com/ilius/ayandict",
	"ilius/ayandict",
)
optionsProp: dict[str, Option] = {
	"fuzzy": BoolOption(
		comment="Create fuzzy search data",
	),
}
