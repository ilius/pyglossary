# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	IntOption,
	StrOption,
)

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
lname = "jmdict"
name = "JMDict"
description = "JMDict (xml)"
extensions = ()
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JMdict"
website = (
	"https://www.edrdg.org/jmdict/j_jmdict.html",
	"The JMDict Project",
)
relatedFormats: list[str] = ["EDICT2", "JMnedict"]
optionsProp: dict[str, Option] = {
	"example_color": StrOption(
		comment="Examples color",
	),
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
	),
	"translitation": BoolOption(
		comment="Add translitation (romaji) of keywords",
	),
}
