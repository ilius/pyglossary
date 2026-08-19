"""
PyGlossary Wordset format plugin.

JSON directory dumps from Wordset.org open lexical data. Read-only ``Reader``
walks per-lemma JSON files under a ``-wordset/`` directory layout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import EncodingOption

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
lname = "wordset"
name = "Wordset"
description = "Wordset.org JSON directory"
extensions = ()
extensionCreate = "-wordset/"
singleFile = False
kind = "directory"
wiki = ""
website = (
	"https://github.com/wordset/wordset-dictionary",
	"@wordset/wordset-dictionary",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
}
