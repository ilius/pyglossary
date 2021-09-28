# -*- coding: utf-8 -*-
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from .bgl_language import languageByCode
from .bgl_charset import charsetByCode

from pyglossary.plugins.formats_common import log
import pyglossary.gregorian as gregorian
from pyglossary.text_utils import (
	uintFromBytes,
)


class InfoItem(object):
	__slots__ = (
		"name",
		"decode",
		"attr",
	)

	def __init__(
		self,
		name: str,
		decode: "Optional[Callable[[bytes], Any]]" = None,
		attr: bool = False,
	):
		self.name = name
		self.decode = decode
		self.attr = attr


def decodeBglBinTime(b_value):
	jd1970 = gregorian.to_jd(1970, 1, 1)
	djd, hm = divmod(uintFromBytes(b_value), 24 * 60)
	year, month, day = gregorian.jd_to(djd + jd1970)
	hour, minute = divmod(hm, 60)
	return f"{year:04d}/{month:02d}/{day:02d}, {hour:02d}:{minute:02d}"


def languageInfoDecode(b_value):
	"""
		returns BabylonLanguage instance
	"""
	intValue = uintFromBytes(b_value)
	try:
		return languageByCode[intValue]
	except IndexError:
		log.warning(f"read_type_3: unknown language code = {intValue}")
		return


def charsetInfoDecode(b_value):
	value = b_value[0]
	try:
		return charsetByCode[value]
	except KeyError:
		log.warning(f"read_type_3: unknown charset {value!r}")


def aboutInfoDecode(b_value):
	if not b_value:
		return
	aboutExt, _, aboutContents = b_value.partition(b"\x00")
	if not aboutExt:
		log.warning("read_type_3: about: no file extension")
		return
	return {
		"about_extension": aboutExt,
		"about": aboutContents,
	}


def utf16InfoDecode(b_value):
	"""
		b_value is byte array
		returns str, or None (on errors)

		block type = 3
		block format: <2 byte code1><2 byte code2>
		if code2 == 0: then the block ends
		if code2 == 1: then the block continues as follows:
		<4 byte len1> \x00 \x00 <message in utf-16>
		len1 - length of message in 2-byte chars
	"""
	if b_value[0] != 0:
		log.warning(
			f"utf16InfoDecode: b_value={b_value}, null expected at 0",
		)
		return

	if b_value[1] == 0:
		if len(b_value) > 2:
			log.warning(
				f"utf16InfoDecode: unexpected b_value size: {len(b_value)}",
			)
		return

	elif b_value[1] > 1:
		log.warning(
			f"utf16InfoDecode: b_value={b_value!r}, unexpected byte at 1",
		)
		return

	# now b_value[1] == 1
	size = 2 * uintFromBytes(b_value[2:6])
	if tuple(b_value[6:8]) != (0, 0):
		log.warning(
			f"utf16InfoDecode: b_value={b_value!r}, null expected at 6:8",
		)
	if size != len(b_value) - 8:
		log.warning(
			f"utf16InfoDecode: b_value={b_value!r}, size does not match",
		)

	return b_value[8:].decode("utf16")  # str


def flagsInfoDecode(b_value):
	"""
		returns a dict with these keys:
			utf8Encoding
				when this flag is set utf8 encoding is used for all articles
				when false, the encoding is set according to the source and
					target alphabet
			bgl_spellingAlternatives
				determines whether the glossary offers spelling alternatives
				for searched terms
			bgl_caseSensitive
				defines if the search for terms in this glossary is
					case sensitive
				see code 0x20 as well

	"""
	flags = uintFromBytes(b_value)
	return {
		"utf8Encoding": (flags & 0x8000 != 0),
		"bgl_spellingAlternatives": (flags & 0x10000 == 0),
		"bgl_caseSensitive": (flags & 0x1000 != 0),
	}


infoType3ByCode = {
	# glossary name
	0x01: InfoItem("title"),

	# glossary author name, a list of "|"-separated values
	0x02: InfoItem("author"),

	# glossary author e-mail
	0x03: InfoItem("email"),

	0x04: InfoItem("copyright"),
	0x07: InfoItem(
		"sourceLang",
		decode=languageInfoDecode,
		attr=True,
	),
	0x08: InfoItem(
		"targetLang",
		decode=languageInfoDecode,
		attr=True,
	),
	0x09: InfoItem("description"),

	# 0: browsing disabled, 1: browsing enabled
	0x0a: InfoItem(
		"bgl_browsingEnabled",
		decode=lambda b_value: (b_value[0] != 0),
	),

	0x0b: InfoItem("icon1.ico"),

	0x0c: InfoItem(
		"bgl_numEntries",
		decode=uintFromBytes,
		attr=True,
	),

	# the value is a dict
	0x11: InfoItem("flags", decode=flagsInfoDecode),

	0x14: InfoItem("creationTime", decode=decodeBglBinTime),
	0x1a: InfoItem(
		"sourceCharset",
		decode=charsetInfoDecode,
		attr=True,
	),
	0x1b: InfoItem(
		"targetCharset",
		decode=charsetInfoDecode,
		attr=True,
	),
	0x1c: InfoItem(
		"bgl_firstUpdated",
		decode=decodeBglBinTime,
	),
	# bgl_firstUpdated was prevously called middleUpdated
	# in rare cases, bgl_firstUpdated is before creationTime
	# but usually it looks like to be the first update (after creation)
	# in some cases, it's the same as lastUpdated
	# in some cases, it's minutes after creationTime
	# bgl_firstUpdated exists in more glossaries than lastUpdated
	# so if lastUpdated is not there, we use bgl_firstUpdated as lastUpdated

	0x20: InfoItem(
		"bgl_caseSensitive2",
		decode=lambda b_value: (b_value[0] == 0x31),
		# 0x30 - case sensitive search is disabled
		# 0x31 - case sensitive search is enabled
	),

	0x24: InfoItem("icon2.ico"),

	0x2c: InfoItem(
		"bgl_purchaseLicenseMsg",
		decode=utf16InfoDecode,
	),
	0x2d: InfoItem(
		"bgl_licenseExpiredMsg",
		decode=utf16InfoDecode,
	),
	0x2e: InfoItem("bgl_purchaseAddress"),

	0x30: InfoItem(
		"bgl_titleWide",
		decode=utf16InfoDecode,
	),

	# a list of "|"-separated values
	0x31: InfoItem(
		"bgl_authorWide",
		decode=utf16InfoDecode,
	),

	0x33: InfoItem(
		"lastUpdated",
		decode=decodeBglBinTime,
	),
	0x3b: InfoItem("bgl_contractions"),

	# contains a value like "Arial Unicode MS" or "Tahoma"
	0x3d: InfoItem("bgl_fontName"),

	# value would be dict
	0x41: InfoItem(
		"bgl_about",
		decode=aboutInfoDecode,
	),

	# the length of the substring match in a term
	0x43: InfoItem(
		"bgl_length",
		decode=uintFromBytes,
	),
}
