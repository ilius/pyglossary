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
wiki = ""
sortOnWrite = ALWAYS
sortKeyName = "headword"

optionsProp: dict[str, Option] = {}
