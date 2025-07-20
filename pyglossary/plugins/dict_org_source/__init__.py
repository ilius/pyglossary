# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import BoolOption

from .writer import Writer

if TYPE_CHECKING:
	from pyglossary.option import Option

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
lname = "dict_org_source"
name = "DictOrgSource"
description = "DICT.org dictfmt source file"
extensions = (".dtxt",)
extensionCreate = ".dtxt"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/DICT"
website = (
	"https://github.com/cheusov/dictd",
	"@cheusov/dictd",
)
relatedFormats: list[str] = ["DictOrg", "Dictunformat"]
optionsProp: dict[str, Option] = {
	"remove_html_all": BoolOption(comment="Remove all HTML tags"),
}
