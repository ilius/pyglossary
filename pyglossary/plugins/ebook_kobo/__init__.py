# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.flags import NEVER

from .writer import Writer

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
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
lname = "kobo"
name = "Kobo"
description = "Kobo E-Reader Dictionary"
extensions = (".kobo",)
extensionCreate = ".kobo.zip"
singleFile = False
kind = "package"
sortOnWrite = NEVER
wiki = "https://en.wikipedia.org/wiki/Kobo_eReader"
website = (
	"https://www.kobo.com",
	"www.kobo.com",
)

# https://help.kobo.com/hc/en-us/articles/360017640093-Add-new-dictionaries-to-your-Kobo-eReader


optionsProp: dict[str, Option] = {}


# Penelope option: marisa_index_size=1000000
