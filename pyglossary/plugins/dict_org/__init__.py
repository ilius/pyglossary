# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.flags import DEFAULT_NO
from pyglossary.option import BoolOption, Option

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
lname = "dict_org"
name = "DictOrg"
description = "DICT.org file format (.index)"
extensions = (".index",)
extensionCreate = ""
singleFile = False
optionsProp: dict[str, Option] = {
	"dictzip": BoolOption(comment="Compress .dict file to .dict.dz"),
	"install": BoolOption(comment="Install dictionary to /usr/share/dictd/"),
}
sortOnWrite = DEFAULT_NO
kind = "directory"
wiki = "https://en.wikipedia.org/wiki/DICT#DICT_file_format"
website = (
	"http://dict.org/bin/Dict",
	"The DICT Development Group",
)
