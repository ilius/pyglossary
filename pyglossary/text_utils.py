# -*- coding: utf-8 -*-
# text_utils.py
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
	from urllib.parse import unquote
	if not url.startswith("file://"):
		return unquote(url)
	path = url[7:]
	if path[-2:] == "\r\n":
		path = path[:-2]
	elif path[-1] == "\r":
		path = path[:-1]
	# here convert html unicode symbols to utf-8 string:
	return unquote(path)


def replacePostSpaceChar(st: str, ch: str) -> str:
	st = (
		st.replace(f" {ch}", ch)
		.replace(ch, f"{ch} ")
		.replace(f"{ch}  ", f"{ch} ")
	)
	if st.endswith(" "):
		st = st[:-1]
	return st


def isASCII(data: str) -> bool:
	for c in data:
		if ord(c) >= 128:
			return False
	return True
