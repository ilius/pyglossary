# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2008-2021 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
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

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	HtmlColorOption,
	StrOption,
)

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
	"debugReadOptions",
	"optionsProp",
]

debugReadOptions = {
	"search_char_samples",  # bool
	"collect_metadata2",  # bool
	"write_gz",  # bool
	"char_samples_path",  # str, file path
	"msg_log_path",  # str, file path
	"raw_dump_path",  # str, file path
	"unpacked_gzip_path",  # str, file path
}

optionsProp: dict[str, Option] = {
	"default_encoding_overwrite": EncodingOption(
		comment="Default encoding (overwrite)",
	),
	"source_encoding_overwrite": EncodingOption(
		comment="Source encoding (overwrite)",
	),
	"target_encoding_overwrite": EncodingOption(
		comment="Target encoding (overwrite)",
	),
	"part_of_speech_color": HtmlColorOption(
		comment="Color for Part of Speech",
	),
	"no_control_sequence_in_defi": BoolOption(
		comment="No control sequence in definitions",
	),
	"strict_string_conversion": BoolOption(
		comment="Strict string conversion",
	),
	"process_html_in_key": BoolOption(
		comment="Process HTML in (entry or info) key",
	),
	"key_rstrip_chars": StrOption(
		multiline=True,
		comment="Characters to strip from right-side of keys",
	),
	"search_char_samples": BoolOption(
		comment="(debug) Search character samples",
	),
	"collect_metadata2": BoolOption(
		comment="(debug) Collect second pass metadata from definitions",
	),
	"write_gz": BoolOption(
		comment="(debug) Create a file named *-data.gz",
	),
	"char_samples_path": StrOption(
		comment="(debug) File path for character samples",
	),
	"msg_log_path": StrOption(
		comment="(debug) File path for message log",
	),
	"raw_dump_path": StrOption(
		comment="(debug) File path for writing raw blocks",
	),
	"unpacked_gzip_path": StrOption(
		comment="(debug) Path to create unzipped file",
	),
}
