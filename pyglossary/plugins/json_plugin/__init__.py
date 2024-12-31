# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)

from .writer import Writer

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
lname = "json"
name = "Json"
description = "JSON (.json)"
extensions = (".json",)
extensionCreate = ".json"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JSON"
website = (
	"https://www.json.org/json-en.html",
	"www.json.org",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"enable_info": BoolOption(comment="Enable glossary info / metedata"),
	"resources": BoolOption(comment="Enable resources / data files"),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
}
