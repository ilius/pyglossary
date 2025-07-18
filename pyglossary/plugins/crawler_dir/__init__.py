# mypy: ignore-errors
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import StrOption

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
lname = "crawler_dir"
name = "CrawlerDir"
description = "Crawler Directory"
extensions = (".crawler",)
extensionCreate = ".crawler/"
singleFile = True
kind = "directory"
wiki = ""
website = None
optionsProp: dict[str, Option] = {
	"compression": StrOption(
		values=["", "gz", "bz2", "lzma"],
		comment="Compression Algorithm",
	),
}
