# -*- coding: utf-8 -*-
# mypy: ignore-errors
from __future__ import annotations

from typing import TYPE_CHECKING

from .reader import Reader

if TYPE_CHECKING:
	from pyglossary.option import Option


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
lname = "cc_kedict"
name = "cc-kedict"
description = "cc-kedict"
extensions = ()
extensionCreate = ""
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/mhagiwara/cc-kedict",
	"@mhagiwara/cc-kedict",
)
optionsProp: dict[str, Option] = {}
