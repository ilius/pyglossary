# -*- coding: utf-8 -*-
# mypy: ignore-errors
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.flags import ALWAYS

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

lname = "dicformids"
enable = True
name = "Dicformids"
description = "DictionaryForMIDs"
extensions = (".mids",)
extensionCreate = ".mids/"
singleFile = False
sortOnWrite = ALWAYS
sortKeyName = "dicformids"
sortEncoding = "utf-8"
kind = "directory"
wiki = ""
website = (
	"http://dictionarymid.sourceforge.net/",
	"DictionaryForMIDs - SourceForge",
)

optionsProp: dict[str, Option] = {}
