# -*- coding: utf-8 -*-
#
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright © 2016-2023 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2016 ivan tkachenko <me@ratijas.tk>
# Copyright © 2012-2015 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	DictOption,
	StrOption,
)

from .writer import Writer

if TYPE_CHECKING:
	from pyglossary.option import Option

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
lname = "appledict"
name = "AppleDict"
description = "AppleDict Source"
extensions = (".apple",)
extensionCreate = ".apple/"
singleFile = False
kind = "directory"
wiki = ""
website = (
	"https://support.apple.com/en-gu/guide/dictionary/welcome/mac",
	"Dictionary User Guide for Mac",
)
relatedFormats: list[str] = ["AppleDictBin"]
# FIXME: rename indexes arg/option to indexes_lang?
optionsProp: dict[str, Option] = {
	"clean_html": BoolOption(comment="use BeautifulSoup parser"),
	"css": StrOption(
		comment="custom .css file path",
	),
	"xsl": StrOption(
		comment="custom XSL transformations file path",
	),
	# default_prefs: Default prefs in python dictionary literal format,
	# i.e. {"key1": "value1", "key2": "value2", ...}.  All keys and values
	# must be quoted strings; not allowed characters (e.g. single/double
	# quotes,equal sign "=", semicolon) must be escaped as hex code
	# according to python string literal rules.
	"default_prefs": DictOption(
		comment="default prefs in python dict format",
		# example: {"key": "value", "version": "1"}
	),
	# prefs_html: path to XHTML file with user interface for
	# dictionary's preferences. refer to Apple's documentation for details.
	"prefs_html": StrOption(
		comment="preferences XHTML file path",
	),
	# front_back_matter: path to XML file with top-level tag
	# <d:entry id="front_back_matter" d:title="Your Front/Back Matter Title">
	# 	your front/back matter entry content
	# </d:entry>
	"front_back_matter": StrOption(
		comment="XML file path with top-level tag",
	),
	"jing": BoolOption(comment="run Jing check on generated XML"),
	# indexes: rename to indexes_lang? TODO
	# Dictionary.app is dummy and by default it don't know
	# how to perform flexible search.  we can help it by manually providing
	# additional indexes to dictionary entries.
	"indexes": StrOption(
		customValue=False,
		values=["", "ru", "zh"],
		comment="Additional indexes to dictionary entries",
	),
}

docTail = """### Also see:

See [doc/apple.md](../apple.md) for additional AppleDict instructions.
"""
