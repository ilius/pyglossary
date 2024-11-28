# -*- coding: utf-8 -*-
# appledict/indexes/ru.py
#
# Copyright © 2016 ivan tkachenko me@ratijas.tk
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
"""Russian indexes based on pymorphy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence

from pyglossary.core import log, pip

from . import languages

try:
	import pymorphy2  # type: ignore
except ImportError:
	log.error(
		f"""module pymorphy2 is required to build extended Russian indexes.
You can download it here: http://pymorphy2.readthedocs.org/en/latest/.
Or by running: {pip} install pymorphy2""",
	)
	raise

morphy = pymorphy2.MorphAnalyzer()


def ru(titles: Sequence[str], _: str) -> set[str]:
	"""
	Give a set of all declines, cases and other forms of word `title`.
	note that it works only if title is one word.
	"""
	indexes: set[str] = set()
	indexes_norm: set[str] = set()
	for title in titles:
		# in-place modification
		_ru(title, indexes, indexes_norm)
	return indexes


def _ru(title: str, a: set[str], a_norm: set[str]) -> None:
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
				# "й" and "и", "ё" and "е", so we're trying to avoid
				# "* Duplicate index. Skipped..." warning.
				# new: return indexes with original letters but check for
				# occurrence against "normal forms".
				word_norm = normalize(word)
				if word_norm not in a_norm:
					a.add(word)
					a_norm.add(word_norm)


def normalize(word: str) -> str:
	return word.lower().replace("й", "и").replace("ё", "е").replace("-", " ")


languages["ru"] = ru
