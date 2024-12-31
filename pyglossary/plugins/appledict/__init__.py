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

from pyglossary.option import (
	BoolOption,
	DictOption,
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
# FIXME: rename indexes arg/option to indexes_lang?
optionsProp: dict[str, Option] = {
	"clean_html": BoolOption(comment="use BeautifulSoup parser"),
	"css": StrOption(
		comment="custom .css file path",
	),
	"xsl": StrOption(
		comment="custom XSL transformations file path",
	),
	"default_prefs": DictOption(
		comment="default prefs in python dict format",
		# example: {"key": "value", "version": "1"}
	),
	"prefs_html": StrOption(
		comment="preferences XHTML file path",
	),
	"front_back_matter": StrOption(
		comment="XML file path with top-level tag",
	),
	"jing": BoolOption(comment="run Jing check on generated XML"),
	"indexes": StrOption(
		customValue=False,
		values=["", "ru", "zh"],
		comment="Additional indexes to dictionary entries",
	),
}

extraDocs = [
	(
		"Also see:",
		"See [doc/apple.md](./doc/apple.md) for additional AppleDict instructions.",
	),
]
