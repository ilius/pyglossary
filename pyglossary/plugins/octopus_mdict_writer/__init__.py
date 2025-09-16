# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.flags import NEVER
from pyglossary.option import (
	BoolOption,
	IntOption,
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
lname = "octopus_mdict_writer"
name = "Octopus MDict Writer"
description = "Octopus MDict (.mdx) - Mockup Writer"
extensions = (".mdx",)
extensionCreate = ".mdx"
singleFile = True
sortOnWrite = NEVER  # We'll handle sorting ourselves if needed

kind = "file"
wiki = "https://github.com/ilius/pyglossary"
website = "https://github.com/ilius/pyglossary"

optionsProp = {
	"encoding": StrOption(
		values=["utf-8", "utf-16", "gbk", "big5"],
		comment="Text encoding for the MDX file",
	),
	"key_block_size": IntOption(
		comment="Key block size in KB",
		values=[8, 16, 32, 64, 128, 256],
	),
	"record_block_size": IntOption(
		comment="Record block size in KB",
		values=[32, 64, 128, 256, 512, 1024],
	),
	"compression_type": IntOption(
		values=[0, 1, 2],  # 0=no compression, 1=lzo, 2=zlib
		comment="Compression type: 0=none, 1=lzo, 2=zlib",
	),
	"audio": BoolOption(
		comment="Convert HTML5 audio tags back to MDX sound:// format",
	),
}
