# -*- coding: utf-8 -*-

# Copyright © 2023 soshial <soshial@gmail.com> (soshial)
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

from struct import unpack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import io

__all__ = [
	"APPLEDICT_FILE_OFFSET",
	"guessFileOffsetLimit",
	"readInt",
	"read_2_bytes_here",
	"read_x_bytes_as_word",
]


APPLEDICT_FILE_OFFSET = 0x40
# addressing of AppleDict binary files always ignores first 0x40 bytes


def readIntPair(buffer: io.BufferedIOBase) -> tuple[int, int]:
	# to satisfy mymy, put them in vars with declared type
	a: int
	b: int
	a, b = unpack("ii", buffer.read(8))
	return a, b


def readInt(buffer: io.BufferedIOBase) -> int:
	return unpack("i", buffer.read(4))[0]


def read_x_bytes_as_word(buffer: io.BufferedIOBase, x: int) -> str:
	return buffer.read(x).decode("UTF-16LE")


def read_2_bytes_here(buffer: io.BufferedIOBase) -> int:
	lower_byte = buffer.read(1)
	higher_byte = buffer.read(1)
	return ord(higher_byte) * 0x100 + ord(lower_byte)


def guessFileOffsetLimit(file: io.BufferedIOBase) -> tuple[int, int]:
	"""Returns address offset to start parsing from and EOF address."""
	file.seek(APPLEDICT_FILE_OFFSET)
	limit = readInt(file)
	intPair = readIntPair(file)

	if intPair == (0, -1):  # 0000 0000 FFFF FFFF
		return 0x20, limit
	return 0x4, limit
