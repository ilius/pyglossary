# -*- coding: utf-8 -*-
# appledict/indexes/zh.py
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
Chinese wildcard and pinyin indexes.
"""

import re

import bs4
import colorize_pinyin as color

from . import languages, log


def zh(titles, content):
	"""
	chinese indexes.

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
		indexes.update({title, title + '。'})

		# remove all non hieroglyph
		title = re.sub(r'[^\u4e00-\u9fff]', '', title)
		indexes.add(title)

	indexes.update(pinyin_indexes(content))

	return indexes


def pinyin_indexes(content):
	pinyin = find_pinyin(content)
	# assert type(pinyin) == unicode

	if not pinyin or pinyin == '_':
		return ()

	indexes = set()

	# multiple pronunciations
	for pinyin in re.split(r',|;', pinyin):

		# find all pinyin ranges, use them to rip pinyin out
		py = [
			r._slice(pinyin)
			for r in color.ranges_of_pinyin_in_string(pinyin)
		]

		# maybe no pinyin here
		if not py:
			return ()

		# just pinyin, with diacritics, separated by whitespace
		indexes.add('%s.' % color.utf(' '.join(py)))

		# pinyin with diacritics replaced by tone numbers
		indexes.add('%s.' % color.utf(' '.join(
			['%s%d' % (
				color.lowercase_string_by_removing_pinyin_tones(p),
				color.determine_tone(p)) for p in py])))
	return indexes


def find_pinyin(content):
	# assume that content is HTML and pinyin is inside second tag
	# (first is <h1>)
	soup = bs4.BeautifulSoup(content.splitlines()[0], "lxml")
	if soup.body:
		soup = soup.body
	children = soup.children
	try:
		next(children)
		pinyin = next(children)
	except StopIteration:
		return None
	return pinyin.text


languages['zh'] = zh
