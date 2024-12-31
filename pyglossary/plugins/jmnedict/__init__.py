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
lname = "jmnedict"
name = "JMnedict"
description = "JMnedict"
extensions = ()
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JMdict"
website = (
	"https://www.edrdg.org/wiki/index.php/Main_Page",
	"EDRDG Wiki",
)
optionsProp: dict[str, Option] = {}
