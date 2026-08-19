"""
PyGlossary TMX format plugin.

Translation Memory eXchange files (``.tmx``) with bilingual translation units.
Read-only ``Reader`` maps TMX ``<tu>`` segments to glossary headwords and
definitions.
"""

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
