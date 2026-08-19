#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

"""
This module is used in plugins.

Shared glossary error types and filename helpers.

Defines ``Error``, ``ReadError``, and ``WriteError`` as the common exception
hierarchy for conversion failures, and ``splitFilenameExt`` to peel compression
and format extensions from a dictionary path.

This module is used in plugins.
"""

from __future__ import annotations

import logging
from os.path import splitext

from .compress import stdCompressions

__all__ = ["Error", "ReadError", "WriteError", "splitFilenameExt"]

log = logging.getLogger("pyglossary")

MAX_EXT_LEN = 4  # FIXME


class Error(Exception):
	"""Base PyGlossary error."""


class ReadError(Error):
	"""Raised when reading a glossary file fails."""


class WriteError(Error):
	"""Raised when writing a glossary file fails."""


def splitFilenameExt(
	filename: str = "",
) -> tuple[str, str, str, str]:
	"""Return (filenameNoExt, filename, ext, compression)."""
	compression = ""
	filenameNoExt, ext = splitext(filename)
	ext = ext.lower()

	if not ext and len(filenameNoExt) <= MAX_EXT_LEN:
		filenameNoExt, ext = "", filenameNoExt

	if not ext:
		return filename, filename, "", ""

	if ext[1:] in {*stdCompressions, "zip", "dz"}:
		compression = ext[1:]
		filename = filenameNoExt
		filenameNoExt, ext = splitext(filename)
		ext = ext.lower()

	return filenameNoExt, filename, ext, compression
