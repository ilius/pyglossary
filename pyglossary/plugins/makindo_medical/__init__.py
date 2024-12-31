# -*- coding: utf-8 -*-
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
lname = "makindo_medical"
name = "MakindoMedical"
description = "Makindo Medical Reference (SQLite3)"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://www.makindo.co.uk/topics/_index.php",
	"Makindo.co.uk Comprehensive Medical Encyclopedia",
)
optionsProp: dict[str, Option] = {}
