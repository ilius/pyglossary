# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
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
lname = "babylon_bdc"
name = "BabylonBdc"
description = "Babylon (bdc)"
extensions = (".bdc",)
extensionCreate = ""
singleFile = True
kind = "binary"
wiki = ""
website = None
optionsProp: dict[str, Option] = {}
