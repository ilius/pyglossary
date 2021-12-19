# -*- coding: utf-8 -*-
# text_utils.py
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import string
import sys
import os
import re
import struct
import binascii
import logging

from . import core

log = logging.getLogger("pyglossary")

startRed = "\x1b[31m"
endFormat = "\x1b[0;0;0m"  # len=8


def toBytes(s: "AnyStr") -> bytes:
	return bytes(s, "utf-8") if isinstance(s, str) else bytes(s)


def toStr(s: "AnyStr") -> str:
	return str(s, "utf-8") if isinstance(s, bytes) else str(s)


def fixUtf8(st: "AnyStr") -> str:
	return toBytes(st).replace(b"\x00", b"").decode("utf-8", "replace")


pattern_n_us = re.compile(r"((?<!\\)(?:\\\\)*)\\n")
pattern_t_us = re.compile(r"((?<!\\)(?:\\\\)*)\\t")
pattern_bar_us = re.compile(r"((?<!\\)(?:\\\\)*)\\\|")
pattern_bar_sp = re.compile(r"(?:(?<!\\)(?:\\\\)*)\|")
b_pattern_bar_us = re.compile(r"((?<!\\)(?:\\\\)*)\\\|".encode("ascii"))
b_pattern_bar_sp = re.compile(r"(?:(?<!\\)(?:\\\\)*)\|".encode("ascii"))


def replaceStringTable(
	rplList: "List[Tuple[str, str]]",
) -> "Callable[[str], str]":
	def replace(st: str) -> str:
		for rpl in rplList:
			st = st.replace(rpl[0], rpl[1])
		return st
	return replace


def escapeNTB(st: str, bar: bool = False) -> str:
	"""
		scapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)
	"""
	st = st.replace("\\", "\\\\")
	st = st.replace("\t", r"\t")
	st = st.replace("\r", "")
	st = st.replace("\n", r"\n")
	if bar:
		st = st.replace("|", r"\|")
	return st


def unescapeNTB(st: str, bar: bool = False) -> str:
	"""
		unscapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)
	"""
	st = pattern_n_us.sub("\\1\n", st)
	st = pattern_t_us.sub("\\1\t", st)
	if bar:
		st = pattern_bar_us.sub(r"\1|", st)
	st = st.replace("\\\\", "\\")  # probably faster than re.sub
	return st


def splitByBarUnescapeNTB(st: str) -> "List[str]":
	"""
		splits by "|" (and not "\\|") then unescapes Newline (\\n),
			Tab (\\t), Baskslash (\\) and Bar (\\|) in each part
		returns a list
	"""
	return [
		unescapeNTB(part, bar=True)
		for part in pattern_bar_sp.split(st)
	]


def escapeBar(st: str) -> str:
	"""
		scapes vertical bar (\|)
	"""
	st = st.replace("\\", "\\\\")
	st = st.replace("|", r"\|")
	return st


def unescapeBar(st: str) -> str:
	"""
		unscapes vertical bar (\|)
	"""
	st = pattern_bar_us.sub(r"\1|", st)
	st = st.replace("\\\\", "\\")  # probably faster than re.sub
	return st


def splitByBar(st: str) -> "List[str]":
	"""
		splits by "|" (and not "\\|") then unescapes Baskslash (\\) and Bar (\\|) in each part
	"""
	return [
		unescapeBar(part)
		for part in pattern_bar_sp.split(st)
	]


def joinByBar(parts: "List[str]") -> "str":
	return "|".join([
		escapeBar(part)
		for part in parts
	])


def unescapeBarBytes(st: bytes) -> bytes:
	"""
		unscapes vertical bar (\|)
	"""
	st = b_pattern_bar_us.sub(b"\\1|", st)
	st = st.replace(b"\\\\", b"\\")  # probably faster than re.sub
	return st


def splitByBarBytes(st: bytes) -> "List[bytes]":
	"""
		splits by "|" (and not "\\|") then unescapes Newline (\\n),
			Tab (\\t), Baskslash (\\) and Bar (\\|) in each part
		returns a list
	"""
	return [
		unescapeBarBytes(part)
		for part in b_pattern_bar_sp.split(st)
	]


# return a message string describing the current exception
def excMessage() -> str:
	i = sys.exc_info()
	return f"{i[0].__name__}: {i[1]}"


def formatHMS(h: int, m: int, s: int) -> str:
	if h == 0:
		if m == 0:
			return f"{s:02d}"
		else:
			return f"{m:02d}:{s:02d}"
	else:
		return f"{h:02d}:{m:02d}:{s:02d}"


# ___________________________________________ #


def uint32ToBytes(n: int) -> bytes:
	return struct.pack('>I', n)


def uint32FromBytes(bs: bytes) -> int:
	return struct.unpack('>I', bs)[0]


def uintFromBytes(bs: bytes) -> int:
	n = 0
	for c in bs:
		n = (n << 8) + c
	return n


def crc32hex(bs: bytes) -> str:
	return struct.pack('>I', binascii.crc32(bs) & 0xffffffff).hex()

# ___________________________________________ #


def urlToPath(url: str) -> str:
	if not url.startswith("file://"):
		return url
	path = url[7:]
	if path[-2:] == "\r\n":
		path = path[:-2]
	elif path[-1] == "\r":
		path = path[:-1]
	# here convert html unicode symbols to utf8 string:
	if "%" not in path:
		return path
	path2 = ""
	n = len(path)
	i = 0
	while i < n:
		if path[i] == "%" and i < n - 2:
			path2 += chr(eval("0x" + path[i + 1:i + 3]))
			i += 3
		else:
			path2 += path[i]
			i += 1
	return path2


def replacePostSpaceChar(st: str, ch: str) -> str:
	return (
		st.replace(f" {ch}", ch)
		.replace(ch, f"{ch} ")
		.replace(f"{ch}  ", f"{ch} ")
	)


def isControlChar(y: int) -> bool:
	# y: char code
	if y < 32 and chr(y) not in "\t\n\r\v":
		return True
	# according to ISO-8859-1
	if 128 <= y <= 159:
		return True
	return False


def isASCII(data: str, exclude: "Optional[List[str]]" = None) -> bool:
	if exclude is None:
		exclude = []
	for c in data:
		co = ord(c)
		if co >= 128 and co not in exclude:
			return False
	return True


def formatByteStr(text: str) -> str:
	out = ""
	for c in text:
		out += f"{ord(c):0>2x} "
	return out
