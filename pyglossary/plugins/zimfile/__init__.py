# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import Option, UnicodeErrorsOption

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
lname = "zim"
name = "Zim"
description = "Zim (.zim, for Kiwix)"
extensions = (".zim",)
extensionCreate = ".zim"
singleFile = True
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/ZIM_(file_format)"
website = (
	"https://wiki.openzim.org/wiki/OpenZIM",
	"OpenZIM",
)
optionsProp: dict[str, Option] = {
	"text_unicode_errors": UnicodeErrorsOption(
		comment="Unicode Errors for plaintext, values: `strict`, `ignore`, `replace`",
	),
	"html_unicode_errors": UnicodeErrorsOption(
		comment="Unicode Errors for HTML, values: `strict`, `ignore`, `replace`",
	),
}

# https://wiki.kiwix.org/wiki/Software

# to download zim files:
# https://archive.org/details/zimarchive
# https://dumps.wikimedia.org/other/kiwix/zim/

# I can't find any way to download zim files from https://library.kiwix.org/
# which wiki.openzim.org points at for downloaing zim files
