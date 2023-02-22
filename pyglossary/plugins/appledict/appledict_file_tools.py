# -*- coding: utf-8 -*-

from io import BufferedReader
from struct import unpack
from typing import List, Tuple

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


OFFSET_FILE_START = 0x40


def readIntAt(buffer: BufferedReader, address: int) -> int:
	buffer.seek(address)
	return unpack('i', buffer.read(4))[0]


def readIntPair(buffer: BufferedReader) -> "Tuple[int, int]":
	return unpack("ii", buffer.read(8))


def readInt(buffer: BufferedReader) -> int:
	return unpack('i', buffer.read(4))[0]


def read_x_bytes_as_word(buffer: BufferedReader, x: int) -> str:
	word = ''
	while x > 0:
		word += chr(read_2_bytes_here(buffer))
		x -= 2
	return word


def read_2_bytes(buffer: BufferedReader, address: int) -> int:
	buffer.seek(address)
	return read_2_bytes_here(buffer)


def read_2_bytes_here(buffer: BufferedReader) -> int:
	lower_byte = buffer.read(1)
	higher_byte = buffer.read(1)
	return ord(higher_byte) * 0x100 + ord(lower_byte)


def read_x_bytes_as_int(buffer: BufferedReader, x) -> int:
	if x == 2:
		return read_2_bytes_here(buffer)
	elif x == 4:
		return readInt(buffer)
	else:
		raise IOError


def guessFileOffsetLimit(file) -> "Tuple[int, int]":
	file.seek(OFFSET_FILE_START)
	limit = OFFSET_FILE_START + readInt(file)
	intPair = readIntPair(file)

	if intPair == (0, -1):  # 0000 0000 FFFF FFFF
		return OFFSET_FILE_START + 0x20, limit

	return OFFSET_FILE_START + 0x4, limit
