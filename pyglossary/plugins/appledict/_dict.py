# -*- coding: utf-8 -*-
# appledict/_dict.py
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2016 Ratijas <ratijas.t@me.com>
# Copyright © 2012-2015 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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

import logging
import re
import string

from . import _normalize

log = logging.getLogger("pyglossary")

digs = string.digits + string.ascii_letters


def base36(x: int) -> str:
	"""
	simplified version of int2base
	http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python#2267446
	"""
	digits = []
	while x:
		digits.append(digs[x % 36])
		x //= 36
	digits.reverse()
	return "".join(digits)


def id_generator() -> "Iterator[str]":
	cnt = 1

	while True:
		yield "_" + str(base36(cnt))
		cnt += 1


def indexes_generator(indexes_lang: str) -> """Callable[
	[str, List[str], str, Any],
	str,
]""":
	"""
	factory that acts according to glossary language
	"""
	indexer = None
	"""Callable[[Sequence[str], str], Sequence[str]]"""
	if indexes_lang:
		from . import indexes as idxs
		indexer = idxs.languages.get(indexes_lang, None)
		if not indexer:
			keys_str = ", ".join(list(idxs.languages.keys()))
			msg = "extended indexes not supported for the" \
				f" specified language: {indexes_lang}.\n" \
				f"following languages available: {keys_str}."
			log.error(msg)
			raise ValueError(msg)

	def generate_indexes(title, alts, content, BeautifulSoup):
		indexes = [title]
		indexes.extend(alts)

		if BeautifulSoup:
			quoted_title = BeautifulSoup.dammit.EntitySubstitution\
				.substitute_xml(title, True)
		else:
			quoted_title = '"' + \
				title.replace(">", "&gt;").replace('"', "&quot;") + \
				'"'

		if indexer:
			indexes = set(indexer(indexes, content))

		normal_indexes = set()
		for idx in indexes:
			normal = _normalize.title(idx, BeautifulSoup)
			normal_indexes.add(_normalize.title_long(normal))
			normal_indexes.add(_normalize.title_short(normal))
		normal_indexes.discard(title)

		normal_indexes = [s for s in normal_indexes if s.strip()]
		# skip empty titles.  everything could happen.

		s = f"<d:index d:value={quoted_title} d:title={quoted_title}/>"
		if BeautifulSoup:
			for idx in normal_indexes:
				quoted_idx = BeautifulSoup.dammit.\
					EntitySubstitution.substitute_xml(idx, True)
				s += f"<d:index d:value={quoted_idx} d:title={quoted_title}/>"
		else:
			for idx in normal_indexes:
				quoted_idx = '"' + \
					idx.replace(">", "&gt;").replace('"', "&quot;") + \
					'"'
				s += f"<d:index d:value={quoted_idx} d:title={quoted_title}/>"
		return s
	return generate_indexes
