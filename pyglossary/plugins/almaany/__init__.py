# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.option import Option

from .reader import Reader

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
lname = "almaany"
name = "Almaany"
description = "Almaany.com (SQLite3)"
extensions = ()
extensionCreate = ".db"
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://play.google.com/store/apps/details?id=com.almaany.arar",
	"Almaany.com Arabic Dictionary - Google Play",
)
optionsProp: dict[str, Option] = {}
