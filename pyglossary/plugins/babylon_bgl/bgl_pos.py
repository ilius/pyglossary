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

partOfSpeechByCode = {
	# Use None for codes we have not seen yet
	# Use "" for codes we've seen but part of speech is unknown
	0x30: "noun",
	0x31: "adjective",
	0x32: "verb",
	0x33: "adverb",
	0x34: "interjection",
	0x35: "pronoun",
	0x36: "preposition",
	0x37: "conjunction",
	0x38: "suffix",
	0x39: "prefix",
	0x3A: "article",
	0x3B: "",  # in Babylon Italian-English.BGL,
	# Babylon Spanish-English.BGL,
	# Babylon_Chinese_S_English.BGL
	# no indication of the part of speech
	0x3C: "abbreviation",
	# (short form: 'ר"ת')
	# (full form: "ר"ת: ראשי תיבות")
	# "ת'"
	# adjective
	# (full form: "ת': תואר")

	# "ש"ע"
	# noun
	# (full form: "ש"ע: שם עצם")

	0x3D: "masculine noun and adjective",
	0x3E: "feminine noun and adjective",
	0x3F: "masculine and feminine noun and adjective",
	0x40: "feminine noun",
	# (short form: "נ\'")
	# (full form: "נ': נקבה")
	0x41: "masculine and feminine noun",
	# 0x41: noun that may be used as masculine and feminine
	# (short form: "זו"נ")
	# (full form: "זו"נ: זכר ונקבה")
	0x42: "masculine noun",
	# (short form: 'ז\'')
	# (full form: "ז': זכר")
	0x43: "numeral",
	0x44: "participle",
	0x45: None,
	0x46: None,
	0x47: None,
}
