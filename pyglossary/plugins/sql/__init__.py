# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	ListOption,
	NewlineOption,
)

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
lname = "sql"
name = "Sql"
description = "SQL (.sql)"
extensions = (".sql",)
extensionCreate = ".sql"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/SQL"
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"info_keys": ListOption(comment="List of dbinfo table columns"),
	"add_extra_info": BoolOption(comment="Create dbinfo_extra table"),
	"newline": NewlineOption(),
	"transaction": BoolOption(comment="Use TRANSACTION"),
}
