# -*- coding: utf-8 -*-
# appledict/indexes/ru.py
#
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
"""
Russian indexes based on pymorphy.
"""

from . import languages
from pyglossary.plugins.formats_common import log

try:
	import pymorphy2
except ImportError:
	log.error("""module pymorphy2 is required to build extended russian indexes.  \
you can download it here: http://pymorphy2.readthedocs.org/en/latest/.  \
or run `pip3 install pymorphy2`.
""")
	raise
else:
	morphy = pymorphy2.MorphAnalyzer()


def ru(titles, _):
	"""
	gives a set of all declines, cases and other froms of word `title`.
	note that it works only if title is one word.

	:type titles: Sequence[str]
	:rtype: Set[str]
	"""
	indexes = set()
	indexes_norm = set()
	for title in titles:
		# in-place modification
		_ru(title, indexes, indexes_norm)
	return list(sorted(indexes))


def _ru(title, a, a_norm):
	# uppercase abbreviature
	if title.isupper():
		return

	title_norm = normalize(title)

	# feature: put dot at the end to match only this word
	a.add(title)
	a.add(title + ".")
	a_norm.add(title_norm)

	# decline only one-word titles
	if len(title.split()) == 1:

		normal_forms = morphy.parse(title)

		if len(normal_forms) > 0:

			# forms of most probable match
			normal_form = normal_forms[0]

			for x in normal_form.lexeme:
				word = x.word
				# Apple Dictionary Services see no difference between
				# 'й' and 'и', 'ё' and 'е', so we're trying to avoid
				# "* Duplicate index. Skipped..." warning.
				# new: return indexes with original letters but check for
				# occurence against "normal forms".
				word_norm = normalize(word)
				if word_norm not in a_norm:
					a.add(word)
					a_norm.add(word_norm)


def normalize(word):
	return word.lower().replace('й', 'и').replace('ё', 'е').replace('-', ' ')


languages['ru'] = ru
