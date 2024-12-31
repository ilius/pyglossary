# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	Option,
)

from .reader import Reader
from .writer import Writer

__all__ = [
	"Reader",
	"Writer",
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
lname = "gettext_po"
name = "GettextPo"
description = "Gettext Source (.po)"
extensions = (".po",)
extensionCreate = ".po"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Gettext"
website = (
	"https://www.gnu.org/software/gettext",
	"gettext - GNU Project",
)
optionsProp: dict[str, Option] = {
	"resources": BoolOption(comment="Enable resources / data files"),
}
