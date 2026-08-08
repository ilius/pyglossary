# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	IntOption,
)

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

optionsProp: dict[str, Option] = {
	"word_field": IntOption(
		customValue=True,
		minim=0,
		comment="0-based index of the note field to use as headword",
	),
	"include_tags": BoolOption(
		comment="Prepend Anki tags to the definition (HTML)",
	),
}
