"""
PyGlossary XDXF format plugin.

XML Dictionary Exchange Format files (``.xdxf``) with structured dictionary
markup. ``Reader`` parses XDXF entries and can transform definitions to HTML for
downstream formats. ``Writer`` exports entries whose definition format is XDXF.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import BoolOption, IntOption

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
lname = "xdxf"
name = "Xdxf"
description = "XDXF (.xdxf)"
extensions = (".xdxf",)
extensionCreate = ".xdxf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/XDXF"
website = (
	"https://github.com/soshial/xdxf_makedict/tree/master/format_standard",
	"XDXF standard - @soshial/xdxf_makedict",
)
relatedFormats: list[str] = ["XdxfCss", "XdxfLax"]
optionsProp: dict[str, Option] = {
	"html": BoolOption(comment="Entries are HTML"),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
	"auto_rtl": BoolOption(
		comment="Auto-detect and mark Right-to-Left text",
	),
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
		minim=0,
		maxim=10000,
	),
}

"""
new format
<xdxf ...>
	<meta_info>
		<!--All meta information about the dictionary: its title, author etc.!-->
		<basename>...</basename>
		<full_title>...</full_title>
		<description>...</description>
	</meta_info>
	<lexicon>
		<ar>article 1</ar>
		<ar>article 2</ar>
		<ar>article 3</ar>
		<ar>article 4</ar>
		...
	</lexicon>
</xdxf>

old format
<xdxf ...>
	<full_name>...</full_name>
	<description>...</description>
	<ar>article 1</ar>
	<ar>article 2</ar>
	<ar>article 3</ar>
	<ar>article 4</ar>
	...
</xdxf>
"""

docTail = """### Write support

The XDXF writer only writes entries that are already XDXF-formatted, so it is
only useful when reading from StarDict or FreeDict, or when modifying an existing
XDXF glossary."""
