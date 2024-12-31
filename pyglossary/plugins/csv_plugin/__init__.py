# -*- coding: utf-8 -*-
#
# Copyright © 2013-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from __future__ import annotations

import csv

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	NewlineOption,
	Option,
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
lname = "csv"
name = "Csv"
description = "CSV (.csv)"
extensions = (".csv",)
extensionCreate = ".csv"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Comma-separated_values"
website = None

optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"newline": NewlineOption(),
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"delimiter": Option(
		typ="str",
		customValue=True,
		values=[",", ";", "@"],
		comment="Column delimiter",
	),
	"add_defi_format": BoolOption(
		comment="enable adding defiFormat (m/h/x)",
	),
	"enable_info": BoolOption(
		comment="Enable glossary info / metedata",
	),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
}

csv.field_size_limit(0x7FFFFFFF)
