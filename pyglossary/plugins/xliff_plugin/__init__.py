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
	"singleFile",
	"wiki",
]

enable = True
lname = "xliff"
name = "XLIFF"
description = "XLIFF (.xlf, .xliff)"
extensions = (".xlf", ".xliff")
extensionCreate = ".xlf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/XLIFF"
website = (
	"https://docs.oasis-open.org/xliff/v1.2/os/xliff-core.html",
	"XLIFF Version 1.2",
)
optionsProp: dict[str, Option] = {}

# XLIFF Version 2.2: https://docs.oasis-open.org/xliff/xliff-core/v2.2/
