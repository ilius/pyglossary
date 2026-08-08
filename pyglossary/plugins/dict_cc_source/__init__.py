# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import StrOption

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
	"relatedFormats",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "dict_cc_source"
name = "Dictcc_source"
description = "Dict.cc translation export (tab-separated source file)"
extensions = (".txt",)
extensionCreate = ".txt"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Dict.cc"
website = (
	"https://www1.dict.cc/translation_file_request.php",
	"dict.cc translation file",
)
relatedFormats: list[str] = ["Dictcc", "Dictcc_split"]
optionsProp: dict[str, Option] = {
	"source_lang": StrOption(
		customValue=True,
		comment=(
			"Source column language code (must match the export header), e.g. en or de"
		),
	),
}
