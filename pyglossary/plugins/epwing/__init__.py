# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING
from pyglossary.flags import ALWAYS

from .reader import Reader

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
	"Reader",
	"description",
	"enable",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
]

enable = True
lname = "epwing"
name = "EPWING"
description = "EPWING"
extensions = ()
singleFile = False
kind = "directory"
sortOnWrite = ALWAYS
sortKeyName = "headword"
wiki = "https://en.wikipedia.org/wiki/EPWING"
website = (
	"https://web.archive.org/web/20060430114516/http://www.epwing.or.jp/",
	"EPWING Consortium (2006)",
)
optionsProp: dict[str, Option] = {}
