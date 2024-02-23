# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
	"enable",
	"lname",
	"format",
	"description",
	"extensions",
	"extensionCreate",
	"singleFile",
	"kind",
	"wiki",
	"website",
	"optionsProp",
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
