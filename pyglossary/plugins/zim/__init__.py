"""
PyGlossary Zim format plugin.

OpenZIM archives (``.zim``) as used by Kiwix offline Wikipedia and dictionaries.
``Reader`` indexes ZIM entries and extracts article HTML as glossary definitions
keyed by title. ``Writer`` builds Kiwix-compatible archives from glossary
entries using ``libzim``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.flags import INTERNAL
from pyglossary.option import (
	BoolOption,
	StrOption,
	UnicodeErrorsOption,
)

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
lname = "zim"
name = "Zim"
description = "Zim (.zim, for Kiwix)"
extensions = (".zim",)
extensionCreate = ".zim"
singleFile = True
sortOnWrite = INTERNAL
sortKeyName = "zim"
kind = "binary"
wiki = "https://en.wikipedia.org/wiki/ZIM_(file_format)"
website = (
	"https://wiki.openzim.org/wiki/OpenZIM",
	"OpenZIM",
)
relatedFormats: list[str] = ["Aard2Slob"]
docTail = """### Sorting

Entries are always stored in libzim's order: `A/` followed by the percent-encoded
headword, compared byte by byte. `--sort` and `--sort-key` do not change the output.
Duplicate headwords are stored as `A/word_2`, `A/word_3`, and so on, and aliases
(`word|alias`) are read back as separate entries. The order after a round trip can
therefore differ from the source order.
"""

optionsProp: dict[str, Option] = {
	"compress": BoolOption(
		comment="Compress ZIM content (zstd)",
	),
	"indexing": BoolOption(
		comment="Build the ZIM full-text/index metadata",
	),
	"language": StrOption(
		comment="ZIM language code (ISO 639-3), overrides glossary source language",
	),
	"word_title": BoolOption(
		comment="Add headword title to beginning of definition",
	),
	"front_article": BoolOption(
		comment="Include entries in random and suggestion indices",
	),
	"verbose": BoolOption(
		comment="Enable verbose output from libzim",
	),
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
# which wiki.openzim.org points at for downloading zim files
