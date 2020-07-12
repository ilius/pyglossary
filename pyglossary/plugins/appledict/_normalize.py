# -*- coding: utf-8 -*-
# appledict/_normalize.py
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

import re

re_spaces = re.compile(r"[ \t\n]{2,}")
re_title = re.compile('<[^<]+?>|"|[<>]|\xef\xbb\xbf')
re_title_short = re.compile(r"\[.*?\]")
re_whitespace = re.compile("(\t|\n|\r)")


def spaces(s):
	"""
	strip off leading and trailing whitespaces and
	replace contiguous whitespaces with just one space.
	"""
	return re_spaces.sub(" ", s.strip())


_brackets_sub = (
	(
		re.compile(r"( *)\{( *)\\\[( *)"),  # { \[
		r"\1\2\3[",
	),
	(
		re.compile(r"( *)\\\]( *)\}( *)"),  # \] }
		r"]\1\2\3",
	),
	(
		re.compile(r"( *)\{( *)\(( *)\}( *)"),  # { ( }
		r"\1\2\3\4[",
	),
	(
		re.compile(r"( *)\{( *)\)( *)\}( *)"),  # { ) }
		r"]\1\2\3\4",
	),
	(
		re.compile(r"( *)\{( *)\(( *)"),  # { (
		r"\1\2\3[",
	),
	(
		re.compile(r"( *)\)( *)\}( *)"),  # ) }
		r"]\1\2\3",
	),
	(
		re.compile(r"( *)\{( *)"),  # {
		r"\1\2[",
	),
	(
		re.compile(r"( *)\}( *)"),  # }
		r"]\1\2",
	),
	(
		re.compile(r"{.*?}"),
		r"",
	),
)


def brackets(s):
	r"""
	replace all crazy brackets with square ones [].

	following combinations are to replace:
		{ \[ ... \] }
		{ ( } ... { ) }
		{ ( ... ) }
		{ ... }
	"""
	if "{" in s:
		for exp, sub in _brackets_sub:
			s = exp.sub(sub, s)
	return spaces(s)


def truncate(text, length=449):
	"""
	trunct a string to given length
	:param str text:
	:return: truncated text
	:rtype: str
	"""
	content = re_whitespace.sub(" ", text)
	if len(text) > length:
		# find the next space after max_len chars (do not break inside a word)
		pos = content[:length].rfind(" ")
		if pos == -1:
			pos = length
		text = text[:pos]
	return text


def title(title, BeautifulSoup):
	"""
	strip double quotes and html tags.
	"""
	if BeautifulSoup:
		title = title.replace("\xef\xbb\xbf", "")
		if len(title) > 1:
			# BeautifulSoup has a bug when markup <= 1 char length
			title = BeautifulSoup.BeautifulSoup(
				title,
				features="lxml",
				# FIXME: html or lxml? gives warning unless it's lxml
			).get_text(strip=True)
	else:
		title = re_title.sub("", title)
		title = title.replace("&", "&amp;")
	title = brackets(title)
	title = truncate(title, 1126)
	return title


def title_long(s):
	"""
	title_long("str[ing]") -> "string"
	"""
	return s.replace("[", "").replace("]", "")


def title_short(s):
	"""
	title_short("str[ing]") -> "str"
	"""
	return spaces(re_title_short.sub("", s))
