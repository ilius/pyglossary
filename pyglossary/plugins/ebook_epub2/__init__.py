# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.flags import ALWAYS
from pyglossary.option import (
	BoolOption,
	IntOption,
	Option,
	StrOption,
)

from .writer import Writer

__all__ = [
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
lname = "epub2"
name = "Epub2"
description = "EPUB-2 E-Book"
extensions = (".epub",)
extensionCreate = ".epub"
singleFile = True
sortOnWrite = ALWAYS
sortKeyName = "ebook"
kind = "package"
wiki = "https://en.wikipedia.org/wiki/EPUB"
website = None

# EPUB-3: https://www.w3.org/community/epub3/

optionsProp: dict[str, Option] = {
	"group_by_prefix_length": IntOption(
		comment="Prefix length for grouping",
	),
	# "group_by_prefix_merge_min_size": IntOption(),
	# "group_by_prefix_merge_across_first": BoolOption(),
	"compress": BoolOption(
		comment="Enable compression",
	),
	"keep": BoolOption(
		comment="Keep temp files",
	),
	"include_index_page": BoolOption(
		comment="Include index page",
	),
	"css": StrOption(
		comment="Path to css file",
	),
	"cover_path": StrOption(
		comment="Path to cover file",
	),
}
