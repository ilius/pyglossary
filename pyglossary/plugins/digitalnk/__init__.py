# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.option import Option

from .reader import Reader

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
lname = "digitalnk"
name = "DigitalNK"
description = "DigitalNK (SQLite3, N-Korean)"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://github.com/digitalprk/dicrs",
	"@digitalprk/dicrs",
)
optionsProp: dict[str, Option] = {}
