# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	ListOption,
	Option,
	StrOption,
)

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
lname = "wiktextract"
name = "Wiktextract"
description = "Wiktextract (.jsonl)"
extensions = (".jsonl",)
extensionCreate = ".jsonl"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/tatuylonen/wiktextract",
	"@tatuylonen/wiktextract",
)
optionsProp: dict[str, Option] = {
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
	"pron_color": StrOption(
		comment="Pronunciation color",
	),
	"gram_color": StrOption(
		comment="Grammar color",
	),
	"example_padding": StrOption(
		comment="Padding for examples (css value)",
	),
	"audio": BoolOption(
		comment="Enable audio",
	),
	"audio_formats": ListOption(
		comment="List of audio formats to use",
	),
	"categories": BoolOption(
		comment="Enable categories",
	),
}
