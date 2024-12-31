# -*- coding: utf-8 -*-
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
lname = "wordnet"
name = "Wordnet"
description = "WordNet"
extensions = ()
extensionCreate = ""
singleFile = False
kind = "directory"
wiki = "https://en.wikipedia.org/wiki/WordNet"
website = (
	"https://wordnet.princeton.edu/",
	"WordNet - A Lexical Database for English",
)

# key is option/argument name, value is instance of Option
optionsProp: dict[str, Option] = {}
