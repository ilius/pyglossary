# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"format",
	"kind",
	"lname",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = False
lname = "babylon_bdc"
format = "BabylonBdc"
description = "Babylon (bdc)"
extensions = (".bdc",)
extensionCreate = ""
singleFile = True
kind = "binary"
wiki = ""
website = None
optionsProp: "dict[str, Option]" = {}
