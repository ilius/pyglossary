# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	FileSizeOption,
	IntOption,
	Option,
	StrOption,
)

from .reader import Reader
from .writer import Writer

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
lname = "aard2_slob"
name = "Aard2Slob"
description = "Aard 2 (.slob)"
extensions = (".slob",)
extensionCreate = ".slob"
singleFile = True
kind = "binary"
wiki = "https://github.com/itkach/slob/wiki"
website = (
	"http://aarddict.org/",
	"aarddict.org",
)
optionsProp: dict[str, Option] = {
	"compression": StrOption(
		values=["", "bz2", "zlib", "lzma2"],
		comment="Compression Algorithm",
	),
	"content_type": StrOption(
		customValue=True,
		values=[
			"text/plain; charset=utf-8",
			"text/html; charset=utf-8",
		],
		comment="Content Type",
	),
	# "encoding": EncodingOption(),
	"file_size_approx": FileSizeOption(
		comment="split up by given approximate file size\nexamples: 100m, 1g",
	),
	"file_size_approx_check_num_entries": IntOption(
		comment="for file_size_approx, check every `[?]` entries",
	),
	"separate_alternates": BoolOption(
		comment="add alternate headwords as separate entries to slob",
	),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
	"version_info": BoolOption(
		comment="add version info tags to slob file",
	),
	"audio_goldendict": BoolOption(
		comment="Convert audio links for GoldenDict (desktop)",
	),
}

extraDocs = [
	(
		"PyICU",
		"See [doc/pyicu.md](./doc/pyicu.md) file for more detailed"
		" instructions on how to install PyICU.",
	),
]
