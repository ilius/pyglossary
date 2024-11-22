# -*- coding: utf-8 -*-
# appledict/indexes/zh.py
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
from __future__ import annotations

"""Chinese wildcard and pinyin indexes."""

import re

import bs4

from pyglossary.core import log, pip

try:
	import colorize_pinyin as color  # type: ignore
except ImportError:
	log.error(
		"module colorize_pinyin is required to build extended Chinese"
		" indexes. You can install it by running: "
		f"{pip} install colorize-pinyin",
	)
	raise

from typing import TYPE_CHECKING

from . import languages, log

if TYPE_CHECKING:
	from collections.abc import Sequence

pinyinPattern = re.compile(r",|;")
nonHieroglyphPattern = re.compile(r"[^\u4e00-\u9fff]")


def zh(titles: Sequence[str], content: str) -> set[str]:
	"""
	Chinese indexes.

	assuming that content is HTML and pinyin is inside second tag
	(first is <h1>), we can try to parse pinyin and generate indexes
	with pinyin subwords separated by whitespaces
	- pinyin itself
	- pinyin with diacritics replaced by tone numbers

	multiple pronunciations separated by comma or semicolon are supported.
	"""
	indexes = set()

	for title in titles:
		# feature: put dot at the end to match only this word
		indexes.update({title, title + "。"})

		# remove all non hieroglyph
		indexes.add(nonHieroglyphPattern.sub("", title))

	indexes.update(pinyin_indexes(content))

	return indexes


def pinyin_indexes(content: str) -> set[str]:
	pinyin = find_pinyin(content)
	# assert type(pinyin) == unicode

	if not pinyin or pinyin == "_":
		return set()

	indexes = set()

	# multiple pronunciations
	for pinyinPart in pinyinPattern.split(pinyin):
		# find all pinyin ranges, use them to rip pinyin out
		py = [
			r._slice(pinyinPart) for r in color.ranges_of_pinyin_in_string(pinyinPart)
		]

		# maybe no pinyin here
		if not py:
			return set()

		# just pinyin, with diacritics, separated by whitespace
		indexes.add(color.utf(" ".join(py)) + ".")

		# pinyin with diacritics replaced by tone numbers
		indexes.add(
			color.utf(
				" ".join(
					[
						color.lowercase_string_by_removing_pinyin_tones(p)
						+ str(color.determine_tone(p))
						for p in py
					],
				),
			)
			+ ".",
		)
	return indexes


def find_pinyin(content: str) -> str | None:
	# assume that content is HTML and pinyin is inside second tag
	# (first is <h1>)
	soup = bs4.BeautifulSoup(content.splitlines()[0], features="lxml")
	if soup.body:
		soup = soup.body  # type: ignore # noqa: PGH003
	children = soup.children
	try:
		next(children)  # type: ignore # noqa: PGH003
		pinyin = next(children)  # type: ignore # noqa: PGH003
	except StopIteration:
		return None
	return pinyin.text


languages["zh"] = zh
