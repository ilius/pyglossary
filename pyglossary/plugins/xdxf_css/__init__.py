# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import BoolOption

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
lname = "xdxf_css"
name = "XdxfCss"
description = "XDXF with CSS and JS"
extensions = ()
extensionCreate = ".xdxf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/XDXF"
website = (
	"https://github.com/soshial/xdxf_makedict/tree/master/format_standard",
	"XDXF standard - @soshial/xdxf_makedict",
)
optionsProp: dict[str, Option] = {
	"html": BoolOption(comment="Entries are HTML"),
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
