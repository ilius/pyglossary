# -*- coding: utf-8 -*-
#
# Copyright © 2008-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2011-2012 kubtek <kubtek@gmail.com>
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
# Thanks to Raul Fernandes <rgfbr@yahoo.com.br> and Karl Grill
#	   for reverse engineering
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
	binStrToInt,
)


def decodeBglBinTime(b_value):
	jd1970 = gregorian.to_jd(1970, 1, 1)
	djd, hm = divmod(binStrToInt(b_value), 24*60)
	year, month, day = gregorian.jd_to(djd + jd1970)
	hour, minute = divmod(hm, 60)
	return '%.2d/%.2d/%.2d, %.2d:%.2d' % (year, month, day, hour, minute)


def languageInfoDecode(b_value):
	"""
		returns BabylonLanguage instance
	"""
	intValue = binStrToInt(b_value)
	try:
		return languageByCode[intValue]
	except IndexError:
		log.warning('read_type_3: unknown language code = %s' % intValue)
		return


def charsetInfoDecode(b_value):
	value = b_value[0]
	try:
		return charsetByCode[value]
	except KeyError:
		log.warning('read_type_3: unknown charset %s' % value)


def aboutInfoDecode(b_value):
	if not b_value:
		return
	aboutExt, _, aboutContents = b_value.partition(b'\x00')
	if not aboutExt:
		log.warning('read_type_3: about: no file extension')
		return
	return {
		'about_extension': aboutExt,
		'about': aboutContents,
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
			'utf16InfoDecode: b_value=%s, null expected at 0' % list(b_value)
		)
		return

	if b_value[1] == 0:
		if len(b_value) > 2:
			log.warning(
				'utf16InfoDecode: unexpected b_value size: %s' % len(b_value)
			)
		return

	elif b_value[1] > 1:
		log.warning(
			'utf16InfoDecode: b_value=%s, unexpected byte at 1' % list(b_value)
		)
		return

	# now b_value[1] == 1
	size = 2 * binStrToInt(b_value[2:6])
	if tuple(b_value[6:8]) != (0, 0):
		log.warning(
			'utf16InfoDecode: b_value=%s, null expected at 6:8' % list(b_value)
		)
	if size != len(b_value)-8:
		log.warning(
			'utf16InfoDecode: b_value=%s, size does not match' % list(b_value)
		)

	return b_value[8:].decode('utf16')  # str


def flagsInfoDecode(b_value):
	"""
		returns a dict with these keys:
			utf8Encoding
				when this flag is set utf8 encoding is used for all articles
				when false, the encoding is set according to the source and
					target alphabet
			spellingAlternatives
				determines whether the glossary offers spelling alternatives
				for searched terms
			caseSensitive
				defines if the search for terms in this glossary is
					case sensitive
				see code 0x20 as well

	"""
	flags = binStrToInt(b_value)
	return {
		'utf8Encoding': (flags & 0x8000 != 0),
		'spellingAlternatives': (flags & 0x10000 == 0),
		'caseSensitive': (flags & 0x1000 != 0),
	}


infoKeysByCode = {
	0x01: 'title',  # glossary name
	0x02: 'author',  # glossary author name, a list of '|'-separated values
	0x03: 'email',  # glossary author e-mail
	0x04: 'copyright',  # copyright message
	0x07: 'sourceLang',
	0x08: 'targetLang',
	0x09: 'description',  # Glossary description
	0x0a: 'browsingEnabled',  # 0: browsing disabled, 1: browsing enabled
	0x0b: 'iconData',  # FIXME
	0x0c: 'bgl_numEntries',
	0x11: 'flags',  # the value is a dict
	0x14: 'creationTime',
	0x1a: 'sourceCharset',
	0x1b: 'targetCharset',
	0x1c: 'middleUpdated',
	0x2c: 'purchaseLicenseMsg',
	0x2d: 'licenseExpiredMsg',
	0x2e: 'purchaseAddress',
	0x30: 'titleWide',
	0x31: 'authorWide',
	0x33: 'lastUpdated',
	0x3b: 'contractions',
	0x3d: 'fontName',  # contains a value like "Arial Unicode MS" or "Tahoma"
	0x41: 'about',  # (aboutExtention, aboutContents)
	0x43: 'length',  # the length of the substring match in a term
}


infoKeyDecodeMethods = {
	'sourceLang': languageInfoDecode,
	'targetLang': languageInfoDecode,
	'browsingEnabled': lambda b_value: (b_value[0] != 0),
	'bgl_numEntries': binStrToInt,
	'creationTime': decodeBglBinTime,
	'middleUpdated': decodeBglBinTime,
	'lastUpdated': decodeBglBinTime,
	'sourceCharset': charsetInfoDecode,
	'targetCharset': charsetInfoDecode,
	'about': aboutInfoDecode,
	'length': binStrToInt,
	'purchaseLicenseMsg': utf16InfoDecode,
	'licenseExpiredMsg': utf16InfoDecode,
	'licenseExpiredMsg': utf16InfoDecode,
	'titleWide': utf16InfoDecode,
	'authorWide': utf16InfoDecode,  # a list of '|'-separated values
	'flags': flagsInfoDecode,
}

"""
bgl_numEntries (0x0c):
	bgl_numEntries does not always matches the number of entries in the
		dictionary, but it's close to it.
	the difference is usually +- 1 or 2, in rare cases may be 9, 29 and more
length (0x43)
	The length of the substring match in a term.
	For example, if your glossary contains the term "Dog" and the substring
		length is 2,
	search of the substrings "Do" or "og" will retrieve the term dog.
	Use substring length 0 for exact match.
contractions (0x3b):
	contains a value like this:
	V-0#Verb|V-0.0#|V-0.1#Infinitive|V-0.1.1#|V-1.0#|V-1.1#|V-1.1.1#Present Simple|V-1.1.2#Present Simple (3rd pers. sing.)|V-2.0#|V-2.1#|V-2.1.1#Past Simple|V-3.0#|V-3.1#|V-3.1.1#Present Participle|V-4.0#|V-4.1#|V-4.1.1#Past Participle|V-5.0#|V-5.1#|V-5.1.1#Future|V2-0#|V2-0.0#|V2-0.1#Infinitive|V2-0.1.1#|V2-1.0#|V2-1.1#|V2-1.1.1#Present Simple (1st pers. sing.)|V2-1.1.2#Present Simple (2nd pers. sing. & plural forms)|V2-1.1.3#Present Simple (3rd pers. sing.)|V2-2.0#|V2-2.1#|V2-2.1.1#Past Simple (1st & 3rd pers. sing.)|V2-2.1.2#Past Simple (2nd pers. sing. & plural forms)|V2-3.0#|V2-3.1#|V2-3.1.1#Present Participle|V2-4.0#|V2-4.1#|V2-4.1.1#Past Participle|V2-5.0#|V2-5.1#|V2-5.1.1#Future||N-0#Noun|N-1.0#|N-1.1#|N-1.1.1#Singular|N-2.0#|N-2.1#|N-2.1.1#Plural|N4-1.0#|N4-1.1#|N4-1.1.1#Singular Masc.|N4-1.1.2#Singular Fem.|N4-2.0#|N4-2.1#|N4-2.1.1#Plural Masc.|N4-2.1.2#Plural Fem.||ADJ-0#Adjective|ADJ-1.0#|ADJ-1.1#|ADJ-1.1.1#Adjective|ADJ-1.1.2#Comparative|ADJ-1.1.3#Superlative||
	value format: (<contraction> '#' [<value>] '|')+
	The value is in second language, that is for Babylon Russian-English.BGL
		the value in russian,
	for Babylon English-Spanish.BGL the value is spanish (I guess), etc.
Glossary manual file (0x41)
	additional information about the dictionary
	in .txt format this may be short info like this:

	Biology Glossary
	Author name: Hafez Divandari
	Author email: hafezdivandari@gmail.com
	-------------------------------------------
	A functional glossary for translating
	English biological articles to fluent Farsi
	-------------------------------------------
	Copyright (c) 2009 All rights reserved.

	in .pdf format this may be a quite large document (about 30 pages),
	an introduction into the dictionary. It describing structure of an article,
	editors, how to use the dictionary.

	format <file extension> '\x00' <file contents>
	file extension may be: '.txt', '.pdf'

purchaseLicenseMsg (0x2c):
	contains a value like this:
	In order to view this glossary, you must purchase a license.
	<br /><a href="http://www.babylon.com/redirects/purchase.cgi?type=170&trid=BPCWHAR">Click here</a> to purchase.

licenseExpiredMsg (0x2d):
	contains a value like this:
	Your license for this glossary has expired.
	In order to view this glossary, you must have a valid license. <br><a href="http://www.babylon.com/redirects/purchase.cgi?type=130&trid=BPCBRTBR">Renew</a> your license today.

purchaseAddress (0x2e):
	contains a value like this:
	http://www.babylon.com/redirects/purchase.cgi?type=169&trid=BPCOT
	or
	mailto:larousse@babylon.com

#elif keyCode==0x20:
#	# 0x30 - case sensitive search is disabled
#	# 0x31 - case sensitive search is enabled
#	# see code 0x11 as well
#	if b_value:
#		value = b_value[0]
"""
