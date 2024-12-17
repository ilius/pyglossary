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
from __future__ import annotations

import binascii
import logging
import re
import struct
import sys
from typing import AnyStr

__all__ = [
	"crc32hex",
	"escapeNTB",
	"excMessage",
	"fixUtf8",
	"joinByBar",
	"replacePostSpaceChar",
	"splitByBar",
	"splitByBarUnescapeNTB",
	"toStr",
	"uint32FromBytes",
	"uint32ToBytes",
	"uint64FromBytes",
	"uint64ToBytes",
	"uintFromBytes",
	"unescapeBar",
	"unescapeNTB",
	"urlToPath",
]

log = logging.getLogger("pyglossary")

endFormat = "\x1b[0;0;0m"  # len=8


def toStr(s: AnyStr) -> str:
	if isinstance(s, bytes):
		return str(s, "utf-8")
	return str(s)


def fixUtf8(st: AnyStr) -> str:
	if isinstance(st, str):
		return st.encode("utf-8").replace(b"\x00", b"").decode("utf-8", "replace")
	return st.replace(b"\x00", b"").decode("utf-8", "replace")


pattern_n_us = re.compile(r"((?<!\\)(?:\\\\)*)\\n")
pattern_t_us = re.compile(r"((?<!\\)(?:\\\\)*)\\t")
pattern_bar_us = re.compile(r"((?<!\\)(?:\\\\)*)\\\|")
pattern_bar_sp = re.compile(r"(?:(?<!\\)(?:\\\\)*)\|")


def escapeNTB(st: str, bar: bool = False) -> str:
	"""Scapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)."""
	st = st.replace("\\", "\\\\")
	st = st.replace("\t", r"\t")
	st = st.replace("\r", "")
	st = st.replace("\n", r"\n")
	if bar:
		st = st.replace("|", r"\|")
	return st  # noqa: RET504


def unescapeNTB(st: str, bar: bool = False) -> str:
	"""Unscapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)."""
	st = pattern_n_us.sub("\\1\n", st)
	st = pattern_t_us.sub("\\1\t", st)
	if bar:
		st = pattern_bar_us.sub(r"\1|", st)
	st = st.replace("\\\\", "\\")  # probably faster than re.sub
	return st  # noqa: RET504


def splitByBarUnescapeNTB(st: str) -> list[str]:
	r"""
	Split by "|" (and not "\\|") then unescapes Newline (\\n),
	Tab (\\t), Baskslash (\\) and Bar (\\|) in each part
	returns a list.
	"""
	return [unescapeNTB(part, bar=True) for part in pattern_bar_sp.split(st)]


def escapeBar(st: str) -> str:
	r"""Scapes vertical bar (\|)."""
	return st.replace("\\", "\\\\").replace("|", r"\|")


def unescapeBar(st: str) -> str:
	r"""Unscapes vertical bar (\|)."""
	# str.replace is probably faster than re.sub
	return pattern_bar_us.sub(r"\1|", st).replace("\\\\", "\\")


def splitByBar(st: str) -> list[str]:
	r"""
	Split by "|" (and not "\\|")
	then unescapes Baskslash (\\) and Bar (\\|) in each part.
	"""
	return [unescapeBar(part) for part in pattern_bar_sp.split(st)]


def joinByBar(parts: list[str]) -> str:
	return "|".join(escapeBar(part) for part in parts)


# return a message string describing the current exception
def excMessage() -> str:
	i = sys.exc_info()
	if not i[0]:
		return ""
	return f"{i[0].__name__}: {i[1]}"


# ___________________________________________ #


def uint32ToBytes(n: int) -> bytes:
	return struct.pack(">I", n)


def uint64ToBytes(n: int) -> bytes:
	return struct.pack(">Q", n)


def uint32FromBytes(bs: bytes) -> int:
	return struct.unpack(">I", bs)[0]


def uint64FromBytes(bs: bytes) -> int:
	return struct.unpack(">Q", bs)[0]


def uintFromBytes(bs: bytes) -> int:
	n = 0
	for c in bs:
		n = (n << 8) + c
	return n


def crc32hex(bs: bytes) -> str:
	return struct.pack(">I", binascii.crc32(bs) & 0xFFFFFFFF).hex()


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
	return (
		st.replace(f" {ch}", ch)
		.replace(ch, f"{ch} ")
		.replace(f"{ch}  ", f"{ch} ")
		.removesuffix(" ")
	)
