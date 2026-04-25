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
from builtins import open as fopen

from ._binary import meld_ints, unmeld_ints
from ._blob import Blob, KeydItemDict
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
	MAX_BIN_ITEM_COUNT,
	MAX_LARGE_BYTE_STRING_LEN,
	MAX_TEXT_LEN,
	MAX_TINY_TEXT_LEN,
	MIME_HTML,
	MIME_TEXT,
	U_CHAR,
	U_CHAR_SIZE,
	U_INT,
	U_INT_SIZE,
	U_LONG_LONG,
	U_LONG_LONG_SIZE,
	U_SHORT,
	U_SHORT_SIZE,
	UTF8,
	calcmax,
)
from ._exceptions import (
	FileFormatException,
	IncorrectFileSize,
	UnknownCompression,
	UnknownEncoding,
	UnknownFileFormat,
)
from ._header import read_header
from ._item_lists import (
	Bin,
	BinMemWriter,
	ItemList,
	RefList,
	Store,
	StoreItem,
)
from ._multifile import MultiFileReader
from ._slob_obj import Slob
from ._struct import StructReader, StructWriter, read_byte_string
from ._types import Header, Ref
from ._writer import Writer, WriterEvent

__all__ = [
	"COMPRESSIONS",
	"DEFAULT_COMPRESSION",
	"IDENTICAL",
	"MAGIC",
	"MAX_BIN_ITEM_COUNT",
	"MAX_LARGE_BYTE_STRING_LEN",
	"MAX_TEXT_LEN",
	"MAX_TINY_TEXT_LEN",
	"MIME_HTML",
	"MIME_TEXT",
	"PRIMARY",
	"QUATERNARY",
	"SECONDARY",
	"TERTIARY",
	"UTF8",
	"U_CHAR",
	"U_CHAR_SIZE",
	"U_INT",
	"U_INT_SIZE",
	"U_LONG_LONG",
	"U_LONG_LONG_SIZE",
	"U_SHORT",
	"U_SHORT_SIZE",
	"Bin",
	"BinMemWriter",
	"Blob",
	"Compression",
	"FileFormatException",
	"Header",
	"IncorrectFileSize",
	"ItemList",
	"KeydItemDict",
	"MultiFileReader",
	"Ref",
	"RefList",
	"Slob",
	"Store",
	"StoreItem",
	"StructReader",
	"StructWriter",
	"UnknownCompression",
	"UnknownEncoding",
	"UnknownFileFormat",
	"Writer",
	"WriterEvent",
	"calcmax",
	"encodings",
	"fopen",
	"meld_ints",
	"open",
	"read_byte_string",
	"read_header",
	"sortkey",
	"unmeld_ints",
]


def open(*filenames: str) -> Slob:  # noqa: A001
	return Slob(*filenames)
