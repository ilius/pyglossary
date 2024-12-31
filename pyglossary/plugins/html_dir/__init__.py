# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	IntOption,
	Option,
	StrOption,
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
lname = "html_dir"
name = "HtmlDir"
description = "HTML Directory"
extensions = (".hdir",)
extensionCreate = ".hdir/"
singleFile = False
kind = "directory"
wiki = ""
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"max_file_size": IntOption(
		comment="Maximum file size in bytes",
	),
	"filename_format": StrOption(
		comment="Filename format, default: {n:05d}.html",
	),
	"escape_defi": BoolOption(
		comment="Escape definitions",
	),
	"dark": BoolOption(
		comment="Use dark style",
	),
	"css": StrOption(
		comment="Path to css file",
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
}
