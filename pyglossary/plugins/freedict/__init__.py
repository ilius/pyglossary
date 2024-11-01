# -*- coding: utf-8 -*-

from .options import optionsProp
from .reader import Reader

__all__ = [
	"Reader",
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

enable = True
lname = "freedict"
format = "FreeDict"
description = "FreeDict (.tei)"
extensions = (".tei",)
extensionCreate = ".tei"
singleFile = True
kind = "text"
wiki = "https://github.com/freedict/fd-dictionaries/wiki"
website = (
	"https://freedict.org/",
	"FreeDict.org",
)
