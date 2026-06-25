from __future__ import annotations

from typing import TYPE_CHECKING

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
	"singleFile",
	"wiki",
]

enable = True
lname = "tmx"
name = "TMX"
description = "TMX (.tmx)"
extensions = (".tmx",)
extensionCreate = ".tmx"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Translation_Memory_eXchange"
website = (
	"https://resources.gala-global.org/tbx14b/",
	"TMX 1.4b Specification",
)
optionsProp: dict[str, Option] = {}
relatedFormats: list[str] = ["XLIFF"]
