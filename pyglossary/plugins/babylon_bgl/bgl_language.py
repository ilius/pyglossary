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
language properties.

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

from dataclasses import dataclass

__all__ = ["BabylonLanguage", "languageByCode"]


@dataclass(slots=True, frozen=True)
class BabylonLanguage:

	"""
	Babylon language properties.

	name: bab:SourceLanguage, bab:TargetLanguage .gpr tags (English, French, Japanese)
	charset: bab:SourceCharset, bab:TargetCharset .gpr tags (Latin, Arabic, Cyrillic)
	encoding: Windows code page (cp1250, cp1251, cp1252)
	code: value of the type 3, code in .bgl file
	"""

	name: str
	encoding: str
	code: int
	name2: str = ""


languages = (
	BabylonLanguage(
		name="English",
		encoding="cp1252",
		code=0x00,
	),
	BabylonLanguage(
		name="French",
		encoding="cp1252",
		code=0x01,
	),
	BabylonLanguage(
		name="Italian",
		encoding="cp1252",
		code=0x02,
	),
	BabylonLanguage(
		name="Spanish",
		encoding="cp1252",
		code=0x03,
	),
	BabylonLanguage(
		name="Dutch",
		encoding="cp1252",
		code=0x04,
	),
	BabylonLanguage(
		name="Portuguese",
		encoding="cp1252",
		code=0x05,
	),
	BabylonLanguage(
		name="German",
		encoding="cp1252",
		code=0x06,
	),
	BabylonLanguage(
		name="Russian",
		encoding="cp1251",
		code=0x07,
	),
	BabylonLanguage(
		name="Japanese",
		encoding="cp932",
		code=0x08,
	),
	BabylonLanguage(
		name="Chinese",
		name2="Traditional Chinese",
		encoding="cp950",
		code=0x09,
	),
	BabylonLanguage(
		name="Chinese",
		name2="Simplified Chinese",
		encoding="cp936",
		code=0x0A,
	),
	BabylonLanguage(
		name="Greek",
		encoding="cp1253",
		code=0x0B,
	),
	BabylonLanguage(
		name="Korean",
		encoding="cp949",
		code=0x0C,
	),
	BabylonLanguage(
		name="Turkish",
		encoding="cp1254",
		code=0x0D,
	),
	BabylonLanguage(
		name="Hebrew",
		encoding="cp1255",
		code=0x0E,
	),
	BabylonLanguage(
		name="Arabic",
		encoding="cp1256",
		code=0x0F,
	),
	BabylonLanguage(
		name="Thai",
		encoding="cp874",
		code=0x10,
	),
	BabylonLanguage(
		name="Other",
		encoding="cp1252",
		code=0x11,
	),
	BabylonLanguage(
		name="Chinese",
		name2="Other Simplified Chinese dialects",
		encoding="cp936",
		code=0x12,
	),
	BabylonLanguage(
		name="Chinese",
		name2="Other Traditional Chinese dialects",
		encoding="cp950",
		code=0x13,
	),
	BabylonLanguage(
		name="Other Eastern-European languages",
		encoding="cp1250",
		code=0x14,
	),
	BabylonLanguage(
		name="Other Western-European languages",
		encoding="cp1252",
		code=0x15,
	),
	BabylonLanguage(
		name="Other Russian languages",
		encoding="cp1251",
		code=0x16,
	),
	BabylonLanguage(
		name="Other Japanese languages",
		encoding="cp932",
		code=0x17,
	),
	BabylonLanguage(
		name="Other Baltic languages",
		encoding="cp1257",
		code=0x18,
	),
	BabylonLanguage(
		name="Other Greek languages",
		encoding="cp1253",
		code=0x19,
	),
	BabylonLanguage(
		name="Other Korean dialects",
		encoding="cp949",
		code=0x1A,
	),
	BabylonLanguage(
		name="Other Turkish dialects",
		encoding="cp1254",
		code=0x1B,
	),
	BabylonLanguage(
		name="Other Thai dialects",
		encoding="cp874",
		code=0x1C,
	),
	BabylonLanguage(
		name="Polish",
		encoding="cp1250",
		code=0x1D,
	),
	BabylonLanguage(
		name="Hungarian",
		encoding="cp1250",
		code=0x1E,
	),
	BabylonLanguage(
		name="Czech",
		encoding="cp1250",
		code=0x1F,
	),
	BabylonLanguage(
		name="Lithuanian",
		encoding="cp1257",
		code=0x20,
	),
	BabylonLanguage(
		name="Latvian",
		encoding="cp1257",
		code=0x21,
	),
	BabylonLanguage(
		name="Catalan",
		encoding="cp1252",
		code=0x22,
	),
	BabylonLanguage(
		name="Croatian",
		encoding="cp1250",
		code=0x23,
	),
	BabylonLanguage(
		name="Serbian",
		encoding="cp1250",
		code=0x24,
	),
	BabylonLanguage(
		name="Slovak",
		encoding="cp1250",
		code=0x25,
	),
	BabylonLanguage(
		name="Albanian",
		encoding="cp1252",
		code=0x26,
	),
	BabylonLanguage(
		name="Urdu",
		encoding="cp1256",
		code=0x27,
	),
	BabylonLanguage(
		name="Slovenian",
		encoding="cp1250",
		code=0x28,
	),
	BabylonLanguage(
		name="Estonian",
		encoding="cp1252",
		code=0x29,
	),
	BabylonLanguage(
		name="Bulgarian",
		encoding="cp1250",
		code=0x2A,
	),
	BabylonLanguage(
		name="Danish",
		encoding="cp1252",
		code=0x2B,
	),
	BabylonLanguage(
		name="Finnish",
		encoding="cp1252",
		code=0x2C,
	),
	BabylonLanguage(
		name="Icelandic",
		encoding="cp1252",
		code=0x2D,
	),
	BabylonLanguage(
		name="Norwegian",
		encoding="cp1252",
		code=0x2E,
	),
	BabylonLanguage(
		name="Romanian",
		encoding="cp1252",
		code=0x2F,
	),
	BabylonLanguage(
		name="Swedish",
		encoding="cp1252",
		code=0x30,
	),
	BabylonLanguage(
		name="Ukrainian",
		encoding="cp1251",
		code=0x31,
	),
	BabylonLanguage(
		name="Belarusian",
		encoding="cp1251",
		code=0x32,
	),
	BabylonLanguage(
		name="Persian",  # aka "Farsi"
		encoding="cp1256",
		code=0x33,
	),
	BabylonLanguage(
		name="Basque",
		encoding="cp1252",
		code=0x34,
	),
	BabylonLanguage(
		name="Macedonian",
		encoding="cp1250",
		code=0x35,
	),
	BabylonLanguage(
		name="Afrikaans",
		encoding="cp1252",
		code=0x36,
	),
	BabylonLanguage(
		# Babylon Glossary Builder spells this language "Faeroese"
		name="Faroese",
		encoding="cp1252",
		code=0x37,
	),
	BabylonLanguage(
		name="Latin",
		encoding="cp1252",
		code=0x38,
	),
	BabylonLanguage(
		name="Esperanto",
		encoding="cp1254",
		code=0x39,
	),
	BabylonLanguage(
		name="Tamazight",
		# aka "Standard Moroccan Tamazight", "Standard Moroccan Berber"
		# or "Standard Moroccan Amazigh"
		encoding="cp1252",
		code=0x3A,
	),
	BabylonLanguage(
		name="Armenian",
		encoding="cp1252",
		code=0x3B,
	),
	BabylonLanguage(
		name="Hindi",
		encoding="cp1252",
		code=0x3C,
	),
	BabylonLanguage(
		name="Somali",
		encoding="cp1252",
		code=0x3D,
	),
)
languageByCode = {lang.code: lang for lang in languages}
