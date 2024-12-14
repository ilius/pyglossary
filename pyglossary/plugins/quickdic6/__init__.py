# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.flags import NEVER
from pyglossary.option import (
	Option,
	StrOption,
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
lname = "quickdic6"
name = "QuickDic6"
description = "QuickDic version 6 (.quickdic)"
extensions = (".quickdic", ".quickdic.v006.zip")
extensionCreate = ".quickdic"
singleFile = True
sortOnWrite = NEVER

kind = "binary"
wiki = ""
website = (
	"https://github.com/rdoeffinger/Dictionary",
	"github.com/rdoeffinger/Dictionary",
)
# https://github.com/rdoeffinger/Dictionary/blob/master/dictionary-format-v6.txt
optionsProp: dict[str, Option] = {
	"normalizer_rules": StrOption(
		comment="ICU normalizer rules to use for index sorting",
	),
}
