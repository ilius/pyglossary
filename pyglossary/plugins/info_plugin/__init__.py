# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.info_writer import InfoWriter as Writer

from .reader import Reader

if TYPE_CHECKING:
	from pyglossary.option import Option

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
lname = "info"
name = "Info"
description = "Glossary Info (.info)"
extensions = (".info",)
extensionCreate = ".info"
singleFile = True
kind = "text"
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp: dict[str, Option] = {}
