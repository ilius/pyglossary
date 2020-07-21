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
	def __init__(self, name, charset, encoding, code, code2="", name2=""):
		self.name = name
		self.name2 = name2
		self.charset = charset
		self.encoding = encoding
		self.code = code


languages = (
	BabylonLanguage(
		name="English",
		charset="Latin",
		encoding="cp1252",
		code=0x00,
		code2="en",
	),
	BabylonLanguage(
		name="French",
		charset="Latin",
		encoding="cp1252",
		code=0x01,
		code2="fr",
	),
	BabylonLanguage(
		name="Italian",
		charset="Latin",
		encoding="cp1252",
		code=0x02,
		code2="it",
	),
	BabylonLanguage(
		name="Spanish",
		charset="Latin",
		encoding="cp1252",
		code=0x03,
		code2="es",
	),
	BabylonLanguage(
		name="Dutch",
		charset="Latin",
		encoding="cp1252",
		code=0x04,
		code2="nl",
	),
	BabylonLanguage(
		name="Portuguese",
		charset="Latin",
		encoding="cp1252",
		code=0x05,
		code2="pt",
	),
	BabylonLanguage(
		name="German",
		charset="Latin",
		encoding="cp1252",
		code=0x06,
		code2="de",
	),
	BabylonLanguage(
		name="Russian",
		charset="Cyrillic",
		encoding="cp1251",
		code=0x07,
		code2="ru",
	),
	BabylonLanguage(
		name="Japanese",
		charset="Japanese",
		encoding="cp932",
		code=0x08,
		code2="ja",
	),
	BabylonLanguage(
		name="Chinese",
		name2="Traditional Chinese",
		charset="Traditional Chinese",
		encoding="cp950",
		code=0x09,
		code2="zh",
	),
	BabylonLanguage(
		name="Chinese",
		name2="Simplified Chinese",
		charset="Simplified Chinese",
		encoding="cp936",
		code=0x0a,
		code2="zh",
	),
	BabylonLanguage(
		name="Greek",
		charset="Greek",
		encoding="cp1253",
		code=0x0b,
		code2="el",
	),
	BabylonLanguage(
		name="Korean",
		charset="Korean",
		encoding="cp949",
		code=0x0c,
		code2="ko",
	),
	BabylonLanguage(
		name="Turkish",
		charset="Turkish",
		encoding="cp1254",
		code=0x0d,
		code2="tr",
	),
	BabylonLanguage(
		name="Hebrew",
		charset="Hebrew",
		encoding="cp1255",
		code=0x0e,
		code2="he",
	),
	BabylonLanguage(
		name="Arabic",
		charset="Arabic",
		encoding="cp1256",
		code=0x0f,
		code2="ar",
	),
	BabylonLanguage(
		name="Thai",
		charset="Thai",
		encoding="cp874",
		code=0x10,
		code2="th",
	),
	BabylonLanguage(
		name="Other",
		charset="Latin",
		encoding="cp1252",
		code=0x11,
		code2="",  # none
	),
	BabylonLanguage(
		name="Chinese",
		name2="Other Simplified Chinese dialects",
		charset="Simplified Chinese",
		encoding="cp936",
		code=0x12,
		code2="zh",  # duplicate
	),
	BabylonLanguage(
		name="Chinese",
		name2="Other Traditional Chinese dialects",
		charset="Traditional Chinese",
		encoding="cp950",
		code=0x13,
		code2="zh",  # duplicate
	),
	BabylonLanguage(
		name="Other Eastern-European languages",
		charset="Eastern European",
		encoding="cp1250",
		code=0x14,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Western-European languages",
		charset="Latin",
		encoding="cp1252",
		code=0x15,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Russian languages",
		charset="Cyrillic",
		encoding="cp1251",
		code=0x16,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Japanese languages",
		charset="Japanese",
		encoding="cp932",
		code=0x17,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Baltic languages",
		charset="Baltic",
		encoding="cp1257",
		code=0x18,
		code2="bat",  # no 2-letter code
	),
	BabylonLanguage(
		name="Other Greek languages",
		charset="Greek",
		encoding="cp1253",
		code=0x19,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Korean dialects",
		charset="Korean",
		encoding="cp949",
		code=0x1a,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Turkish dialects",
		charset="Turkish",
		encoding="cp1254",
		code=0x1b,
		code2="",  # none
	),
	BabylonLanguage(
		name="Other Thai dialects",
		charset="Thai",
		encoding="cp874",
		code=0x1c,
		code2="tai",  # no 2-letter code, and "tha" / "th" is for "Thai"
	),
	BabylonLanguage(
		name="Polish",
		charset="Eastern European",
		encoding="cp1250",
		code=0x1d,
		code2="pl",
	),
	BabylonLanguage(
		name="Hungarian",
		charset="Eastern European",
		encoding="cp1250",
		code=0x1e,
		code2="hu",
	),
	BabylonLanguage(
		name="Czech",
		charset="Eastern European",
		encoding="cp1250",
		code=0x1f,
		code2="cs",
	),
	BabylonLanguage(
		name="Lithuanian",
		charset="Baltic",
		encoding="cp1257",
		code=0x20,
		code2="lt",
	),
	BabylonLanguage(
		name="Latvian",
		charset="Baltic",
		encoding="cp1257",
		code=0x21,
		code2="lv",
	),
	BabylonLanguage(
		name="Catalan",
		charset="Latin",
		encoding="cp1252",
		code=0x22,
		code2="ca",
	),
	BabylonLanguage(
		name="Croatian",
		charset="Eastern European",
		encoding="cp1250",
		code=0x23,
		code2="hr",
	),
	BabylonLanguage(
		name="Serbian",
		charset="Eastern European",
		encoding="cp1250",
		code=0x24,
		code2="sr",
	),
	BabylonLanguage(
		name="Slovak",
		charset="Eastern European",
		encoding="cp1250",
		code=0x25,
		code2="sk",
	),
	BabylonLanguage(
		name="Albanian",
		charset="Latin",
		encoding="cp1252",
		code=0x26,
		code2="sq",
	),
	BabylonLanguage(
		name="Urdu",
		charset="Arabic",
		encoding="cp1256",
		code=0x27,
		code2="ur",
	),
	BabylonLanguage(
		name="Slovenian",
		charset="Eastern European",
		encoding="cp1250",
		code=0x28,
		code2="sl",
	),
	BabylonLanguage(
		name="Estonian",
		charset="Latin",
		encoding="cp1252",
		code=0x29,
		code2="et",
	),
	BabylonLanguage(
		name="Bulgarian",
		charset="Eastern European",
		encoding="cp1250",
		code=0x2a,
		code2="bg",
	),
	BabylonLanguage(
		name="Danish",
		charset="Latin",
		encoding="cp1252",
		code=0x2b,
		code2="da",
	),
	BabylonLanguage(
		name="Finnish",
		charset="Latin",
		encoding="cp1252",
		code=0x2c,
		code2="fi",
	),
	BabylonLanguage(
		name="Icelandic",
		charset="Latin",
		encoding="cp1252",
		code=0x2d,
		code2="is",
	),
	BabylonLanguage(
		name="Norwegian",
		charset="Latin",
		encoding="cp1252",
		code=0x2e,
		code2="no",
	),
	BabylonLanguage(
		name="Romanian",
		charset="Latin",
		encoding="cp1252",
		code=0x2f,
		code2="ro",
	),
	BabylonLanguage(
		name="Swedish",
		charset="Latin",
		encoding="cp1252",
		code=0x30,
		code2="sv",
	),
	BabylonLanguage(
		name="Ukrainian",
		charset="Cyrillic",
		encoding="cp1251",
		code=0x31,
		code2="uk",
	),
	BabylonLanguage(
		name="Belarusian",
		charset="Cyrillic",
		encoding="cp1251",
		code=0x32,
		code2="be",
	),
	BabylonLanguage(
		name="Persian",  # aka "Farsi"
		charset="Arabic",
		encoding="cp1256",
		code=0x33,
		code2="fa",
	),
	BabylonLanguage(
		name="Basque",
		charset="Latin",
		encoding="cp1252",
		code=0x34,
		code2="eu",
	),
	BabylonLanguage(
		name="Macedonian",
		charset="Eastern European",
		encoding="cp1250",
		code=0x35,
		code2="mk",
	),
	BabylonLanguage(
		name="Afrikaans",
		charset="Latin",
		encoding="cp1252",
		code=0x36,
		code2="af",
	),
	BabylonLanguage(
		# Babylon Glossary Builder spells this language "Faeroese"
		name="Faroese",
		charset="Latin",
		encoding="cp1252",
		code=0x37,
		code2="fo",
	),
	BabylonLanguage(
		name="Latin",
		charset="Latin",
		encoding="cp1252",
		code=0x38,
		code2="la",
	),
	BabylonLanguage(
		name="Esperanto",
		charset="Turkish",
		encoding="cp1254",
		code=0x39,
		code2="eo",
	),
	BabylonLanguage(
		name="Tamazight",
		# aka "Standard Moroccan Tamazight", "Standard Moroccan Berber"
		# or "Standard Moroccan Amazigh"
		charset="Latin",
		encoding="cp1252",
		code=0x3a,
		code2="zgh",  # no 2-letter code (ISO 639-1)
	),
	BabylonLanguage(
		name="Armenian",
		charset="Latin",
		encoding="cp1252",
		code=0x3b,
		code2="hy",
	),
	BabylonLanguage(
		name="Hindi",
		charset="Latin",
		encoding="cp1252",
		code=0x3c,
		code2="hi",
	),
	BabylonLanguage(
		name="Somali",
		charset="Latin",
		encoding="cp1252",
		code=0x3d,
		code2="so",
	),
)
languageByCode = {lang.code: lang for lang in languages}
