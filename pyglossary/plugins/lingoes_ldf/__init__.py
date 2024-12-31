# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	NewlineOption,
	Option,
)

from .reader import Reader
from .writer import Writer

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
lname = "lingoes_ldf"
name = "LingoesLDF"
description = "Lingoes Source (.ldf)"
extensions = (".ldf",)
extensionCreate = ".ldf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Lingoes"
website = (
	"http://www.lingoes.net/en/dictionary/dict_format.php",
	"Lingoes.net",
)
optionsProp: dict[str, Option] = {
	"newline": NewlineOption(),
	"resources": BoolOption(comment="Enable resources / data files"),
	"encoding": EncodingOption(),
}
