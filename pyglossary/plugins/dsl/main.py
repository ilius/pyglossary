# -*- coding: utf-8 -*-
#
# Copyright © 2016 Ratijas <ratijas.t@me.com>
# Copyright © 2016-2018 Saeed Rasooli <saeed.gnu@gmail.com>
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
exposed API lives here.
"""


import copy
import re

from . import tag as _tag
from . import layer as _layer


def process_closing_tags(stack, tags):
	"""
	close `tags`, closing some inner layers if necessary.

	:param stack: Iterable[layer.Layer]
	:param tags: Iterable[str]
	"""
	index = len(stack) - 1
	for tag in copy.copy(tags):
		index_for_tag = _tag.index_of_layer_containing_tag(stack, tag)
		if index_for_tag is not None:
			index = min(index, index_for_tag)
		else:
			tags.remove(tag)

	if not tags:
		return

	to_open = set()
	for layer in stack[:index:-1]:
		for lt in layer.tags:
			if lt.closing not in tags:
				to_open.add(lt)
		_layer.close_layer(stack)

	to_close = set()
	layer = stack[index]
	for lt in layer.tags:
		if lt.closing in tags:
			to_close.add(lt)
	_layer.close_tags(stack, to_close, index)

	if to_open:
		_layer.Layer(stack)
		stack[-1].tags = to_open


OPEN = 1
CLOSE = 2
TEXT = 3

BRACKET_L = "\0\1"
BRACKET_R = "\0\2"

# precompiled regexs
# re_m_tag_with_content = re.compile(r"(\[m\d\])(.*?)(\[/m\])")
re_non_escaped_bracket = re.compile(r"(?<!\\)\[")
_startswith_tag_cache = {}


class DSLParser(object):
	"""
	only clean dsl on output!
	"""

	def __init__(self, tags=frozenset({
		("m", r"\d"),
		"*",
		"ex",
		"i",
		("c", r"(?: \w+)?"),
		"p",
		"\"",
		"b",
		"s",
		"sup",
		"sub",
		"ref",
		"url",
	})):
		r"""
		:type tags: set[str | tuple[str]] | frozenset[str | tuple[str]]
		:param tags: set (or any other iterable) of tags where each tag is a
					string or two-tuple. if string, it is tag name without
					brackets, must be constant, i.e. non-save regex characters
					will be escaped, e.g.: "i", "sub", "*".
					if 2-tuple, then first item is tag"s base name, and
					second is its extension for opening tag,
					e.g.: ("c", r" (\w+)"), ("m", r"\d")
		"""
		tags_ = set()
		for tag, ext_re in (
			t if isinstance(t, tuple) else (t, "")
			for t in tags
		):
			tag_re = re.escape(tag)
			re_tag_open = re.compile(fr"\[{tag_re}{ext_re}\]")
			tags_.add((tag, tag_re, ext_re, re_tag_open))
		self.tags = frozenset(tags_)

	def parse(self, line):
		r"""
		parse dsl markup in `line` and return clean valid dsl markup.

		:type line: str
		:param line: line with dsl formatting.

		:rtype: str
		"""
		line = self.put_brackets_away(line)
		line = self._parse(line)
		return self.bring_brackets_back(line)

	def _parse(self, line):
		items = self._split_line_by_tags(line)
		line = self._tags_and_text_loop(items)
		return line

	def _split_line_by_tags(self, line):
		"""
		split line into chunks, each chunk is whether opening / closing
		tag or text.

		return iterable of two-tuples. first element is item's type, one of:
		- OPEN, second element is Tag object
		- CLOSE, second element is str with closed tag's name
		- TEXT, second element is str

		:param line: str
		:return: Iterable
		"""
		ptr = 0
		while ptr < len(line):
			bracket = line.find("[", ptr)
			if bracket != -1:
				chunk = line[ptr:bracket]
			else:
				chunk = line[ptr:]

			if chunk:
				yield TEXT, chunk

			if bracket == -1:
				break

			ptr = bracket
			# at least two chars after opening bracket:
			bracket = line.find("]", ptr + 2)
			if line[ptr + 1] == "/":
				yield CLOSE, line[ptr + 2:bracket]
			else:
				for tag, _, _, re_tag_open in self.tags:
					if re_tag_open.match(line[ptr:bracket + 1]):
						yield OPEN, _tag.Tag(line[ptr + 1:bracket], tag)
						break
				else:
					tag = line[ptr + 1:bracket]
					yield OPEN, _tag.Tag(tag, tag)
			ptr = bracket + 1

	@staticmethod
	def _tags_and_text_loop(tags_and_text):
		"""
		parse chunks one by one.

		:param tags_and_text:
			Iterable[["OPEN", Tag] | ["CLOSE", str] | ["TEXT", str]]
		:return: str
		"""
		state = TEXT
		stack = []
		closings = set()

		for item_t, item in tags_and_text:

			if item_t is OPEN:
				if _tag.was_opened(stack, item) and item.closing not in closings:
					continue

				if item.closing == "m" and len(stack) >= 1:
					# close all layers. [m*] tags can only appear
					# at top layer.
					# note: do not reopen tags that were marked as
					# closed already.
					to_open = set.union(*(
						{t for t in l.tags if t.closing not in closings}
						for l in stack
					))
					for i in range(len(stack)):
						_layer.close_layer(stack)
					# assert len(stack) == 1
					# assert not stack[0].tags
					_layer.Layer(stack)
					stack[-1].tags = to_open

				elif state is CLOSE:
					process_closing_tags(stack, closings)

				if not stack or stack[-1].text:
					_layer.Layer(stack)

				stack[-1].tags.add(item)
				state = OPEN
				continue

			elif item_t is CLOSE:
				if state in (OPEN, TEXT):
					closings.clear()
				closings.add(item)
				state = CLOSE
				continue

			elif item_t is TEXT:
				if state is CLOSE:
					process_closing_tags(stack, closings)

				if not stack:
					_layer.Layer(stack)
				stack[-1].text += item
				state = TEXT
				continue

		if state is CLOSE and closings:
			process_closing_tags(stack, closings)
		# shutdown unclosed tags
		return "".join([l.text for l in stack])

	def put_brackets_away(self, line):
		r"""put away \[, \] and brackets that does not belong to any of given tags.

		:rtype: str
		"""
		clean_line = ""
		startswith_tag = _startswith_tag_cache.get(self.tags, None)
		if startswith_tag is None:
			openings = "|".join(f"{_[1]}{_[2]}" for _ in self.tags)
			closings = "|".join(_[1] for _ in self.tags)
			startswith_tag = re.compile(
				fr"(?:(?:{openings})|/(?:{closings}))\]"
			)
			_startswith_tag_cache[self.tags] = startswith_tag
		for i, chunk in enumerate(re_non_escaped_bracket.split(line)):
			if i != 0:
				m = startswith_tag.match(chunk)
				if m:
					clean_line += "[" + \
						m.group() + \
						chunk[m.end():].replace("[", BRACKET_L)\
							.replace("]", BRACKET_R)
				else:
					clean_line += BRACKET_L + chunk.replace("[", BRACKET_L)\
						.replace("]", BRACKET_R)
			else:  # firsr chunk
				clean_line += chunk.replace("[", BRACKET_L)\
					.replace("]", BRACKET_R)
		return clean_line

	@staticmethod
	def bring_brackets_back(line):
		return line.replace(BRACKET_L, "[").replace(BRACKET_R, "]")
