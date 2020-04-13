# -*- coding: utf-8 -*-
# text_utils.py
#
# Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
import logging

from typing import (
	AnyStr,
	List,
	Union,
	Optional,
)

from . import core

log = logging.getLogger("root")

startRed = "\x1b[31m"
endFormat = "\x1b[0;0;0m"  # len=8


def toBytes(s: AnyStr) -> bytes:
	return bytes(s, "utf-8") if isinstance(s, str) else bytes(s)


def toStr(s: AnyStr) -> str:
	return str(s, "utf-8") if isinstance(s, bytes) else str(s)


def fixUtf8(st: AnyStr) -> str:
	return toBytes(st).replace(b"\x00", b"").decode("utf-8", "replace")

pattern_n_us = re.compile(r"((?<!\\)(?:\\\\)*)\\n")
pattern_t_us = re.compile(r"((?<!\\)(?:\\\\)*)\\t")
pattern_bar_us = re.compile(r"((?<!\\)(?:\\\\)*)\\\|")
pattern_bar_sp = re.compile(r"(?:(?<!\\)(?:\\\\)*)\|")


def escapeNTB(st: str, bar: bool = True) -> str:
	"""
		scapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)
	"""
	st = st.replace(r"\\", r"\\\\")
	st = st.replace("\t", r"\t")
	st = st.replace("\n", r"\n")
	if bar:
		st = st.replace("|", r"\|")
	return st


def unescapeNTB(st: str, bar: bool = False) -> str:
	"""
		unscapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)
	"""
	st = re.sub(pattern_n_us, "\\1\n", st)
	st = re.sub(pattern_t_us, "\\1\t", st)
	if bar:
		st = re.sub(pattern_bar_us, r"\1\|", st)
#	st = re.sub(r"\\\\", r"\\", st)
	st = st.replace("\\\\", "\\")  # probably faster than re.sub
	return st


def splitByBarUnescapeNTB(st: str) -> List[str]:
	"""
		splits by "|" (and not "\\|") then unescapes Newline (\\n),
			Tab (\\t), Baskslash (\\) and Bar (\\|) in each part
		returns a list
	"""
	return [
		unescapeNTB(part, bar=True)
		for part in re.split(pattern_bar_sp, st)
	]


# return a message string describing the current exception
def excMessage() -> str:
	i = sys.exc_info()
	return "{0}: {1}".format(i[0].__name__, i[1])


def formatHMS(h: int, m: int, s: int) -> str:
	if h == 0:
		if m == 0:
			return "%.2d" % s
		else:
			return "%.2d:%.2d" % (m, s)
	else:
		return "%.2d:%.2d:%.2d" % (h, m, s)


def timeHMS(seconds: Union[int, float]) -> str:
	import time
	(h, m, s) = time.gmtime(int(seconds))[3:6]
	return formatHMS(h, m, s)


def relTimeHMS(seconds: Union[int, float]) -> str:
	(days, s) = divmod(int(seconds), 24*3600)
	(m, s) = divmod(s, 60)
	(h, m) = divmod(m, 60)
	return formatHMS(h, m, s)

# ___________________________________________ #


def intToBinStr(n: int, stLen: int = 0) -> bytes:
	bs = []
	while n > 0:
		bs.insert(0, n & 0xff)
		n >>= 8
	return bytes(bs).rjust(stLen, b"\x00")


def binStrToInt(bs: AnyStr) -> int:
	bs = toBytes(bs)
	n = 0
	for c in bs:
		n = (n << 8) + c
	return n


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
		if path[i] == "%" and i < n-2:
			path2 += chr(eval("0x%s" % path[i+1:i+3]))
			i += 3
		else:
			path2 += path[i]
			i += 1
	return path2


def replacePostSpaceChar(st: str, ch: str) -> str:
	return st.replace(" "+ch, ch).replace(ch, ch+" ").replace(ch+"  ", ch+" ")


def runDictzip(filename: str) -> None:
	import subprocess
	dictzipCmd = "/usr/bin/dictzip"  # Save in pref FIXME
	if not os.path.isfile(dictzipCmd):
		return False
	if filename[-4:] == ".ifo":
		filename = filename[:-4]
	(out, err) = subprocess.Popen(
		[dictzipCmd, filename+".dict"],
		stdout=subprocess.PIPE
	).communicate()
#	out = p3[1].read()
#	err = p3[2].read()
#	log.debug("dictzip command: \"%s\"", dictzipCmd)
#	if err:
#		log.error("dictzip error: %s", err.replace("\n", " "))
#	if out:
#		log.error("dictzip error: %s", out.replace("\n", " "))


def isControlChar(y: int) -> bool:
	# y: char code
	if y < 32 and chr(y) not in "\t\n\r\v":
		return True
	# according to ISO-8859-1
	if 128 <= y <= 159:
		return True
	return False


def isASCII(data: str, exclude: Optional[List[str]] = None) -> bool:
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
		out += "{0:0>2x}".format(ord(c)) + " "
	return out
