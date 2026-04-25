# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2008-2021 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2011-2012 kubtek <kubtek@gmail.com>
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
# Thanks to Raul Fernandes <rgfbr@yahoo.com.br> and Karl Grill for reverse
# engineering as part of https://sourceforge.net/projects/ktranslator/
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

import os
import re
from typing import TYPE_CHECKING

from pyglossary.core import log

from .options import debugReadOptions, optionsProp
from .reader_charset import _BglReaderCharset
from .reader_data import (
	BGLGzipFile,
	Block,
	DefinitionFields,
	EntryWordData,
	FileOffS,
)
from .reader_defi import _BglReaderDefi
from .reader_entries import _BglReaderEntries
from .reader_io import _BglReaderIO
from .reader_meta import _BglReaderMeta

if TYPE_CHECKING:
	from pyglossary.glossary_types import ReaderGlossaryType

__all__ = [
	"BGLGzipFile",
	"Block",
	"DefinitionFields",
	"EntryWordData",
	"FileOffS",
	"Reader",
	"debugReadOptions",
	"optionsProp",
	"tmpDir",
]

if os.sep == "/":  # Operating system is Unix-like
	tmpDir = "/tmp"  # noqa: S108
elif os.sep == "\\":  # Operating system is ms-windows
	tmpDir = os.getenv("TEMP")
else:
	raise RuntimeError(
		f"Unknown path separator(os.sep=={os.sep!r}). What is your operating system?",
	)


class Reader(
	_BglReaderEntries,
	_BglReaderDefi,
	_BglReaderCharset,
	_BglReaderMeta,
	_BglReaderIO,
):
	useByteProgress = False

	_default_encoding_overwrite: str = ""
	_source_encoding_overwrite: str = ""
	_target_encoding_overwrite: str = ""
	_part_of_speech_color: str = "007000"
	_no_control_sequence_in_defi: bool = False
	_strict_string_conversion: bool = False
	# process keys and alternates as HTML
	_process_html_in_key: bool = True
	_key_rstrip_chars: str = ""

	##########################################################################
	"""
	Dictionary properties
	---------------------

	Dictionary (or glossary) properties are textual data like glossary name,
	glossary author name, glossary author e-mail, copyright message and
	glossary description. Most of the dictionaries have these properties set.
	Since they contain textual data we need to know the encoding.
	There may be other properties not listed here. I've enumerated only those
	that are available in Babylon Glossary builder.

	Playing with Babylon builder allows us detect how encoding is selected.
	If global utf-8 flag is set, utf-8 encoding is used for all properties.
	Otherwise the target encoding is used, that is the encoding corresponding
	to the target language. The chars that cannot be represented in the target
	encoding are replaced with question marks.

	Using this algorithm to decode dictionary properties you may encounter that
	some of them are decoded incorrectly. For example, it is clear that the
	property is in cp1251 encoding while the algorithm says we must use cp1252,
	and we get garbage after decoding. That is OK, the algorithm is correct.
	You may install that dictionary in Babylon and check dictionary properties.
	It shows the same garbage. Unfortunately, we cannot detect correct encoding
	in this case automatically. We may add a parameter the will overwrite the
	selected encoding, so the user may fix the encoding if needed.
	"""

	def __init__(self, glos: ReaderGlossaryType) -> None:  # no more arguments
		self._glos = glos
		self._filename = ""
		self.info = {}
		self.numEntries = None
		####
		self.sourceLang = ""
		self.targetLang = ""
		##
		self.defaultCharset = ""
		self.sourceCharset = ""
		self.targetCharset = ""
		##
		self.sourceEncoding = None
		self.targetEncoding = None
		####
		self.bgl_numEntries = None
		self.wordLenMax = 0
		self.defiMaxBytes = 0
		##
		self.metadata2 = None
		self.rawDumpFile = None
		self.msgLogFile = None
		self.samplesDumpFile = None
		##
		self.stripSlashAltKeyPattern = re.compile(r"(^|\s)/(\w)", re.UNICODE)
		self.specialCharPattern = re.compile(r"[^\s\w.]", re.UNICODE)
		###
		self.file = None
		# offset of gzip header, set in self.open()
		self.gzipOffset = None
		# must be a in RRGGBB format
		self.iconDataList = []
		self.aboutBytes: bytes | None = None
		self.aboutExt = ""

	def __len__(self) -> int:
		if self.numEntries is None:
			log.warning("len(reader) called while numEntries=None")
			return 0
		return self.numEntries + self.numResources
