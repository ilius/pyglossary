# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import Option

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

enable = False
lname = "testformat"
name = "Test"
description = "Test Format File(.test)"
extensions = (".test", ".tst")
extensionCreate = ".test"
singleFile = True
kind = "text"
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp: dict[str, Option] = {}
