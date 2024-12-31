# -*- coding: utf-8 -*-

from __future__ import annotations

from pyglossary.flags import DEFAULT_YES
from pyglossary.option import (
	BoolOption,
	FileSizeOption,
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
lname = "mobi"
name = "Mobi"
description = "Mobipocket (.mobi) E-Book"
extensions = (".mobi",)
extensionCreate = ".mobi"
singleFile = False
sortOnWrite = DEFAULT_YES
sortKeyName = "ebook"
kind = "package"
wiki = "https://en.wikipedia.org/wiki/Mobipocket"
website = None

optionsProp: dict[str, Option] = {
	"group_by_prefix_length": IntOption(
		comment="Prefix length for grouping",
	),
	# "group_by_prefix_merge_min_size": IntOption(),
	# "group_by_prefix_merge_across_first": BoolOption(),
	# specific to mobi
	"kindlegen_path": StrOption(
		comment="Path to kindlegen executable",
	),
	"compress": BoolOption(
		disabled=True,
		comment="Enable compression",
	),
	"keep": BoolOption(
		comment="Keep temp files",
	),
	"include_index_page": BoolOption(
		disabled=True,
		comment="Include index page",
	),
	"css": StrOption(
		# disabled=True,
		comment="Path to css file",
	),
	"cover_path": StrOption(
		# disabled=True,
		comment="Path to cover file",
	),
	"file_size_approx": FileSizeOption(
		comment="Approximate size of each xhtml file (example: 200kb)",
	),
	"hide_word_index": BoolOption(
		comment="Hide headword in tap-to-check interface",
	),
	"spellcheck": BoolOption(
		comment="Enable wildcard search and spell correction during word lookup",
		# "Maybe it just enables the kindlegen's spellcheck."
	),
	"exact": BoolOption(
		comment="Exact-match Parameter",
		# "I guess it only works for inflections"
	),
}

extraDocs = [
	(
		"Other Requirements",
		"Install [KindleGen](https://wiki.mobileread.com/wiki/KindleGen)"
		" for creating Mobipocket e-books.",
	),
]
