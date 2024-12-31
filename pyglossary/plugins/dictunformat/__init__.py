from __future__ import annotations

from pyglossary.option import EncodingOption, Option, StrOption

from .reader import Reader

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
lname = "dictunformat"
name = "Dictunformat"
description = "dictunformat output file"
extensions = (".dictunformat",)
extensionCreate = ".dictunformat"
singleFile = True
kind = "text"
wiki = "https://directory.fsf.org/wiki/Dictd"
website = (
	"https://github.com/cheusov/dictd/blob/master/dictunformat.1.in",
	"dictd/dictunformat.1.in - @cheusov/dictd",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"headword_separator": StrOption(
		comment="separator for headword and alternates",
	),
}
