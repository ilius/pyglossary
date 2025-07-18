# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	EncodingOption,
)

from .reader import Reader
from .writer import Writer

if TYPE_CHECKING:
	from pyglossary.option import Option

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
lname = "edlin"
name = "Edlin"
# Editable Linked List of Entries
description = "EDLIN"
extensions = (".edlin",)
extensionCreate = ".edlin/"
singleFile = False
kind = "directory"
wiki = ""
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"prev_link": BoolOption(comment="Enable link to previous entry"),
}
