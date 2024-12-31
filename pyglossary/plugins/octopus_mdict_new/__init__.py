# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
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
lname = "octopus_mdict"
name = "OctopusMdict"
description = "Octopus MDict (.mdx)"
extensions = (".mdx",)
extensionCreate = ""
singleFile = False
kind = "binary"
wiki = ""
website = (
	"https://www.mdict.cn/wp/?page_id=5325&lang=en",
	"Download | MDict.cn",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"substyle": BoolOption(
		comment="Enable substyle",
	),
	"same_dir_data_files": BoolOption(
		comment="Read data files from same directory",
	),
	"audio": BoolOption(
		comment="Enable audio objects",
	),
}

extraDocs = [
	(
		"`python-lzo` is required for **some** MDX glossaries.",
		"""First try converting your MDX file, if failed (`AssertionError` probably),
then try to install [LZO library and Python binding](./doc/lzo.md).""",
	),
]
