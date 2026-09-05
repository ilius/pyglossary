# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
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
lname = "anki_apkg"
name = "AnkiApkg"
description = "Anki deck package (.apkg, .colpkg)"
extensions = (".apkg", ".colpkg")
extensionCreate = ".apkg"
singleFile = True
kind = "binary"
wiki = "https://docs.ankiweb.net/exporting.html"
website = (
	"https://github.com/ankitects/anki",
	"ankitects/anki",
)

optionsProp: dict[str, Option] = {}
