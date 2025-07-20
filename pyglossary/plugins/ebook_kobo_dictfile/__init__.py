# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	EncodingOption,
)

from .reader import Reader
from .writer import Writer

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
lname = "kobo_dictfile"
name = "Dictfile"
description = "Kobo E-Reader Dictfile (.df)"
extensions = (".df",)
extensionCreate = ".df"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://pgaskin.net/dictutil/dictgen/#dictfile-format",
	"dictgen - dictutil",
)
# https://github.com/pgaskin/dictutil

relatedFormats: list[str] = ["Kobo"]

optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"extract_inline_images": BoolOption(comment="Extract inline images"),
}
