# -*- coding: utf-8 -*-
# mypy: ignore-errors
# from https://github.com/maxim-saplin/pyglossary

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
lname = "dikt_json"
name = "DiktJson"
description = "DIKT JSON (.json)"
extensions = ()
extensionCreate = ".json"
singleFile = True
kind = "text"
wiki = ""
website = "https://github.com/maxim-saplin/dikt"
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"enable_info": BoolOption(comment="Enable glossary info / metedata"),
	"resources": BoolOption(comment="Enable resources / data files"),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
}
