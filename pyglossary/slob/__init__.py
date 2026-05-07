# slob — Aard dictionary blob format (pyglossary)
# Copyright (C) 2020-2023 Saeed Rasooli
# Copyright (C) 2019 Igor Tkach <itkach@gmail.com>
# 	as part of https://github.com/itkach/slob
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

import encodings

from ._collate import (
	IDENTICAL,
	PRIMARY,
	QUATERNARY,
	SECONDARY,
	TERTIARY,
	sortkey,
)
from ._compressions import COMPRESSIONS, Compression
from ._constants import (
	DEFAULT_COMPRESSION,
	MAGIC,
	MIME_HTML,
	MIME_TEXT,
	UTF8,
)
from ._exceptions import (
	FileFormatException,
	IncorrectFileSize,
	UnknownCompression,
	UnknownEncoding,
	UnknownFileFormat,
)
from ._multifile import MultiFileReader
from ._slob_obj import Slob
from ._writer import Writer

__all__ = [
	"COMPRESSIONS",
	"DEFAULT_COMPRESSION",
	"IDENTICAL",
	"MAGIC",
	"MIME_HTML",
	"MIME_TEXT",
	"PRIMARY",
	"QUATERNARY",
	"SECONDARY",
	"TERTIARY",
	"UTF8",
	"Compression",
	"FileFormatException",
	"IncorrectFileSize",
	"MultiFileReader",
	"Slob",
	"UnknownCompression",
	"UnknownEncoding",
	"UnknownFileFormat",
	"Writer",
	"encodings",
	"sortkey",
]
