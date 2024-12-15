# -*- coding: utf-8 -*-
# appledict/_dict.py
# Output to Apple Dictionary xml sources for Dictionary Development Kit.
#
# Copyright © 2016-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2016 ivan tkachenko me@ratijas.tk
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
from __future__ import annotations

import logging
import string
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator
	from typing import Any

from . import _normalize

__all__ = ["_normalize", "id_generator", "indexes_generator", "quote_string"]

log = logging.getLogger("pyglossary")

digs = string.digits + string.ascii_letters


def base36(x: int) -> str:
	"""
	Simplified version of int2base
	http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python#2267446.
	"""
	digits: list[str] = []
	while x:
		digits.append(digs[x % 36])
		x //= 36
	digits.reverse()
	return "".join(digits)


def id_generator() -> Iterator[str]:
	cnt = 1

	while True:
		yield "_" + base36(cnt)
		cnt += 1


def quote_string(value: str, BeautifulSoup: Any) -> str:
	if BeautifulSoup:
		return BeautifulSoup.dammit.EntitySubstitution.substitute_xml(
			value,
			make_quoted_attribute=True,
		)

	return '"' + value.replace(">", "&gt;").replace('"', "&quot;") + '"'


def indexes_generator(
	indexes_lang: str,
) -> Callable[
	[str, list[str], str, Any],
	str,
]:
	"""Generate indexes according to glossary language."""
	indexer = None
	"""Callable[[Sequence[str], str], Sequence[str]]"""
	if indexes_lang:
		from . import indexes as idxs

		indexer = idxs.languages.get(indexes_lang, None)
		if not indexer:
			keys_str = ", ".join(idxs.languages)
			msg = (
				"extended indexes not supported for the"
				f" specified language: {indexes_lang}.\n"
				f"following languages available: {keys_str}."
			)
			log.error(msg)
			raise ValueError(msg)

	def generate_indexes(
		title: str,
		alts: list[str],
		content: str,
		BeautifulSoup: Any,
	) -> str:
		indexes = [title]
		indexes.extend(alts)

		quoted_title = quote_string(title, BeautifulSoup)

		if indexer:
			indexes = list(set(indexer(indexes, content)))

		normal_indexes = set()
		for idx in indexes:
			normal = _normalize.title(idx, BeautifulSoup)
			normal_indexes.add(_normalize.title_long(normal))
			normal_indexes.add(_normalize.title_short(normal))
		normal_indexes.discard(title)

		s = f"<d:index d:value={quoted_title} d:title={quoted_title}/>"
		for idx in normal_indexes:
			if not idx.strip():
				# skip empty titles. everything could happen.
				continue
			quoted_idx = quote_string(idx, BeautifulSoup)
			s += f"<d:index d:value={quoted_idx} d:title={quoted_title}/>"
		return s

	return generate_indexes
