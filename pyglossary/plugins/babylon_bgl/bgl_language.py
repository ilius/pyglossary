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

"""
language properties

In this short note we describe how Babylon select encoding for key words,
alternates and definitions.
There are source and target encodings. The source encoding is used to
encode keys and alternates, the target encoding is used to encode
definitions.
The source encoding is selected based on the source language of the
dictionary, the target encoding is tied to the target language.
Babylon Glossary Builder allows you to specify source and target languages.
If you open a Builder project (a file with .gpr extension) in a text
editor, you should find the following elements:
<bab:SourceCharset>Latin</bab:SourceCharset>
<bab:SourceLanguage>English</bab:SourceLanguage>
<bab:TargetCharset>Latin</bab:TargetCharset>
<bab:TargetLanguage>English</bab:TargetLanguage>
Here bab:SourceLanguage is the source language that you select in the
builder wizard, bab:SourceCharset - is the corresponding charset.
bab:TargetLanguage - target language, bab:TargetCharset - corresponding
charset.
Unfortunately, builder does not tell us what encoding corresponds to charset,
but we can detect it.

A few words about how definitions are encoded. If all chars of the
definition fall into the target charset, Babylon use that charset to encode
the definition. If at least one char does not fall into the target charset,
Babylon use utf-8 encoding, wrapping the definition into <charset c=U> and
</charset> tags.
You can make Babylon use utf-8 encoding for the whole dictionary, in that case
all definitions, keys and alternates are encoded with utf-8. See Babylon
Glossary Builder wizard, Glossary Properties tab, Advanced button, Use UTF-8
encoding check box. Definitions are not augmented with extra mackup in this
case, that is you'll not find charset tags in definitions.

How you can tell what encoding was used for the particular definition in
.bgl file? You need to check the following conditions.

Block type 3, code 0x11. If 0x8000 bit is set, the whole dictionary use
utf-8 encoding.

If the definition starts with <charset c=U>, that definition uses utf-8
encoding.

Otherwise you need to consult the target encoding.

Block type 3, code 0x1b. That field normally contains 1 byte code of the
target encoding. Codes fill the range of 0x41 to 0x4e. Babylon Builder
generate codes 0x42 - 0x4e. How to generate code 0x41?
Occasionally you may encounter the field value is four zero bytes. In this
case, I guess, the default encoding for the target language is used.

Block type 3, code 0x08. That field contains 4-bytes code of the target
language. The first three bytes are always zero, the last byte is the code.
Playing with Babylon Glossary builder we can find language codes corresponding
to target language. The language codes fill the range of 0 to 0x3d.

How to detect the target encoding? Here is the technique I've used.
- Create a babylon glossary source file ( a file with .gls extension) with
	the following contents. Start the file with utf-8 BOM for the builder
	to recognize the utf-8 encoding. Use unicode code point code as key,
	and a single unicode chars encoding in utf-8 as definition. Create keys
	for all code points in the range 32 - 0x10000, or you may use wider range.
	We do not use code points in the range 0-31, since they are control chars.
	You should skip the following three chars: & < >. Since the definition
	is supposed to contain html, these chars are be replaced by &amp; &lt;
	&gt; respectively. You should skip the char $ as well, it has special
	meaning in definitions (?). Skip all code point that cannot encoded in
	utf-8 (not all code points in the range 32-0x10000 represent valid chars).
- Now that you have a glossary source file, process it with builder selecting
	the desired target language. Make sure the "use utf-8" option is no set.
	You'll get a .bgl file.
- Process the generated .bgl file with pyglossary. Skip all definitions that
	start with <charset c=U> tag. Try to decode definitions using different
	encodings and match the result with the real value (key - code point char
	code). Thus you'll find the encoding having the best match.

	For example, you may do the following.
	Loop over all available encodings, loop over all definitions in the
	dictionary. Count the number of definitions that does not start with
	charset tag - total. Among them count the number of definitions that were
	correctly decoded - success. The encoding where total == success, is
	the target encoding.

There are a few problems I encountered. It looks like python does not
correctly implement cp932 and cp950 encodings. For Japanese charset I
got 99.12% match, and for Traditional Chinese charset I got even less -
66.97%. To conform my guess that Japanese is cp932 and Traditional Chinese
is cp950 I built a C++ utility that worked on the data extracted from .bgl
dictionary. I used WideCharToMultiByte function for conversion. The C++
utility confirmed the cp932 and cp950 encodings, I got 100% match.
"""


class BabylonLanguage(object):
	"""
		Babylon language properties.

		name - bab:SourceLanguage, bab:TargetLanguage .gpr tags
			(English, French, Japanese)
		charset - bab:SourceCharset, bab:TargetCharset .gpr tags
			(Latin, Arabic, Cyrillic)
		encoding - Windows code page
			(cp1250, cp1251, cp1252)
		code - value of the type 3, code in .bgl file
	"""
	def __init__(self, name, charset, encoding, code):
		self.name = name
		self.charset = charset
		self.encoding = encoding
		self.code = code

languages = (
	BabylonLanguage(
		name='English',
		charset='Latin',
		encoding='cp1252',
		code=0x00,
	),
	BabylonLanguage(
		name='French',
		charset='Latin',
		encoding='cp1252',
		code=0x01,
	),
	BabylonLanguage(
		name='Italian',
		charset='Latin',
		encoding='cp1252',
		code=0x02,
	),
	BabylonLanguage(
		name='Spanish',
		charset='Latin',
		encoding='cp1252',
		code=0x03,
	),
	BabylonLanguage(
		name='Dutch',
		charset='Latin',
		encoding='cp1252',
		code=0x04,
	),
	BabylonLanguage(
		name='Portuguese',
		charset='Latin',
		encoding='cp1252',
		code=0x05,
	),
	BabylonLanguage(
		name='German',
		charset='Latin',
		encoding='cp1252',
		code=0x06,
	),
	BabylonLanguage(
		name='Russian',
		charset='Cyrillic',
		encoding='cp1251',
		code=0x07,
	),
	BabylonLanguage(
		name='Japanese',
		charset='Japanese',
		encoding='cp932',
		code=0x08,
	),
	BabylonLanguage(
		name='Chinese (T)',
		charset='Traditional Chinese',
		encoding='cp950',
		code=0x09,
	),
	BabylonLanguage(
		name='Chinese (S)',
		charset='Simplified Chinese',
		encoding='cp936',
		code=0x0a,
	),
	BabylonLanguage(
		name='Greek',
		charset='Greek',
		encoding='cp1253',
		code=0x0b,
	),
	BabylonLanguage(
		name='Korean',
		charset='Korean',
		encoding='cp949',
		code=0x0c,
	),
	BabylonLanguage(
		name='Turkish',
		charset='Turkish',
		encoding='cp1254',
		code=0x0d,
	),
	BabylonLanguage(
		name='Hebrew',
		charset='Hebrew',
		encoding='cp1255',
		code=0x0e,
	),
	BabylonLanguage(
		name='Arabic',
		charset='Arabic',
		encoding='cp1256',
		code=0x0f,
	),
	BabylonLanguage(
		name='Thai',
		charset='Thai',
		encoding='cp874',
		code=0x10,
	),
	BabylonLanguage(
		name='Other',
		charset='Latin',
		encoding='cp1252',
		code=0x11,
	),
	BabylonLanguage(
		name='Other Simplified Chinese dialects',
		charset='Simplified Chinese',
		encoding='cp936',
		code=0x12,
	),
	BabylonLanguage(
		name='Other Traditional Chinese dialects',
		charset='Traditional Chinese',
		encoding='cp950',
		code=0x13,
	),
	BabylonLanguage(
		name='Other Eastern-European languages',
		charset='Eastern European',
		encoding='cp1250',
		code=0x14,
	),
	BabylonLanguage(
		name='Other Western-European languages',
		charset='Latin',
		encoding='cp1252',
		code=0x15,
	),
	BabylonLanguage(
		name='Other Russian languages',
		charset='Cyrillic',
		encoding='cp1251',
		code=0x16,
	),
	BabylonLanguage(
		name='Other Japanese languages',
		charset='Japanese',
		encoding='cp932',
		code=0x17,
	),
	BabylonLanguage(
		name='Other Baltic languages',
		charset='Baltic',
		encoding='cp1257',
		code=0x18,
	),
	BabylonLanguage(
		name='Other Greek languages',
		charset='Greek',
		encoding='cp1253',
		code=0x19,
	),
	BabylonLanguage(
		name='Other Korean dialects',
		charset='Korean',
		encoding='cp949',
		code=0x1a,
	),
	BabylonLanguage(
		name='Other Turkish dialects',
		charset='Turkish',
		encoding='cp1254',
		code=0x1b,
	),
	BabylonLanguage(
		name='Other Thai dialects',
		charset='Thai',
		encoding='cp874',
		code=0x1c,
	),
	BabylonLanguage(
		name='Polish',
		charset='Eastern European',
		encoding='cp1250',
		code=0x1d,
	),
	BabylonLanguage(
		name='Hungarian',
		charset='Eastern European',
		encoding='cp1250',
		code=0x1e,
	),
	BabylonLanguage(
		name='Czech',
		charset='Eastern European',
		encoding='cp1250',
		code=0x1f,
	),
	BabylonLanguage(
		name='Lithuanian',
		charset='Baltic',
		encoding='cp1257',
		code=0x20,
	),
	BabylonLanguage(
		name='Latvian',
		charset='Baltic',
		encoding='cp1257',
		code=0x21,
	),
	BabylonLanguage(
		name='Catalan',
		charset='Latin',
		encoding='cp1252',
		code=0x22,
	),
	BabylonLanguage(
		name='Croatian',
		charset='Eastern European',
		encoding='cp1250',
		code=0x23,
	),
	BabylonLanguage(
		name='Serbian',
		charset='Eastern European',
		encoding='cp1250',
		code=0x24,
	),
	BabylonLanguage(
		name='Slovak',
		charset='Eastern European',
		encoding='cp1250',
		code=0x25,
	),
	BabylonLanguage(
		name='Albanian',
		charset='Latin',
		encoding='cp1252',
		code=0x26,
	),
	BabylonLanguage(
		name='Urdu',
		charset='Arabic',
		encoding='cp1256',
		code=0x27,
	),
	BabylonLanguage(
		name='Slovenian',
		charset='Eastern European',
		encoding='cp1250',
		code=0x28,
	),
	BabylonLanguage(
		name='Estonian',
		charset='Latin',
		encoding='cp1252',
		code=0x29,
	),
	BabylonLanguage(
		name='Bulgarian',
		charset='Eastern European',
		encoding='cp1250',
		code=0x2a,
	),
	BabylonLanguage(
		name='Danish',
		charset='Latin',
		encoding='cp1252',
		code=0x2b,
	),
	BabylonLanguage(
		name='Finnish',
		charset='Latin',
		encoding='cp1252',
		code=0x2c,
	),
	BabylonLanguage(
		name='Icelandic',
		charset='Latin',
		encoding='cp1252',
		code=0x2d,
	),
	BabylonLanguage(
		name='Norwegian',
		charset='Latin',
		encoding='cp1252',
		code=0x2e,
	),
	BabylonLanguage(
		name='Romanian',
		charset='Latin',
		encoding='cp1252',
		code=0x2f,
	),
	BabylonLanguage(
		name='Swedish',
		charset='Latin',
		encoding='cp1252',
		code=0x30,
	),
	BabylonLanguage(
		name='Ukranian',
		charset='Cyrillic',
		encoding='cp1251',
		code=0x31,
	),
	BabylonLanguage(
		name='Belarusian',
		charset='Cyrillic',
		encoding='cp1251',
		code=0x32,
	),
	BabylonLanguage(
		name='Farsi',
		charset='Arabic',
		encoding='cp1256',
		code=0x33,
	),
	BabylonLanguage(
		name='Basque',
		charset='Latin',
		encoding='cp1252',
		code=0x34,
	),
	BabylonLanguage(
		name='Macedonian',
		charset='Eastern European',
		encoding='cp1250',
		code=0x35,
	),
	BabylonLanguage(
		name='Afrikaans',
		charset='Latin',
		encoding='cp1252',
		code=0x36,
	),
	BabylonLanguage(
		# Babylon Glossary Builder spells this language 'Faeroese'
		name='Faroese',
		charset='Latin',
		encoding='cp1252',
		code=0x37,
	),
	BabylonLanguage(
		name='Latin',
		charset='Latin',
		encoding='cp1252',
		code=0x38,
	),
	BabylonLanguage(
		name='Esperanto',
		charset='Turkish',
		encoding='cp1254',
		code=0x39,
	),
	BabylonLanguage(
		name='Tamazight',
		charset='Latin',
		encoding='cp1252',
		code=0x3a,
	),
	BabylonLanguage(
		name='Armenian',
		charset='Latin',
		encoding='cp1252',
		code=0x3b,
	),
	BabylonLanguage(
		name='Hindi',
		charset='Latin',
		encoding='cp1252',
		code=0x3c,
	),
	BabylonLanguage(
		name='Somali',
		charset='Latin',
		encoding='cp1252',
		code=0x3d,
	),
)
languageByCode = {lang.code: lang for lang in languages}
languageByName = {lang.name: lang for lang in languages}
