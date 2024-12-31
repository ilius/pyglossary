# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	FileSizeOption,
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
lname = "tabfile"
name = "Tabfile"
description = "Tabfile (.txt, .dic)"
extensions = (".txt", ".tab", ".tsv")
extensionCreate = ".txt"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Tab-separated_values"
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"enable_info": BoolOption(
		comment="Enable glossary info / metedata",
	),
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"file_size_approx": FileSizeOption(
		comment="Split up by given approximate file size\nexamples: 100m, 1g",
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
}
