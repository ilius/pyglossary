# -*- coding: utf-8 -*-
#
# Copyright © 2016 ivan tkachenko me@ratijas.tk
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
import typing
from enum import IntEnum
from typing import Any, Dict, FrozenSet, Iterable, List, Literal, Set, Tuple, Union

from . import layer as _layer
from . import tag as _tag


def process_closing_tags(
	stack: "List[_layer.Layer]",
	tags: "Set[str]",
) -> None:
	"""
	close `tags`, closing some inner layers if necessary.
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


class State(IntEnum):
	OPEN = 1
	CLOSE = 2
	TEXT = 3


BRACKET_L = "\0\1"
BRACKET_R = "\0\2"

# precompiled regexs
# re_m_tag_with_content = re.compile(r"(\[m\d\])(.*?)(\[/m\])")
re_non_escaped_bracket = re.compile(r"(?<!\\)\[")
_startswith_tag_cache: Dict[Any, re.Pattern[str]] = {}


class DSLParser(object):
	"""
	only clean dsl on output!
	"""

	EVENT = Union[
		Tuple[Literal[State.OPEN], _tag.Tag],
		Tuple[Literal[State.CLOSE], str],
		Tuple[Literal[State.TEXT], str],
	]

	def __init__(
		self: "typing.Self",
		tags: "FrozenSet[str | Tuple[str, str]]" = frozenset({
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
			# ("ref", r"\[ref(?: [^\[\]]*)?\]"),
			"ref",
			"url",
		}),
	) -> None:
		r"""
		:param tags: set (or any other iterable) of tags where each tag is a
					string or two-tuple. if string, it is tag name without
					brackets, must be constant, i.e. non-save regex characters
					will be escaped, e.g.: "i", "sub", "*".
					if 2-tuple, then first item is tag's base name, and
					second is its extension for opening tag,
					e.g.: ("c", r" (\w+)"), ("m", r"\d")
		"""
		tags_: Set[Tuple[str, str, str, re.Pattern[str]]] = set()
		for tag, ext_re in (
			t if isinstance(t, tuple) else (t, "")
			for t in tags
		):
			tag_re = re.escape(tag)
			re_tag_open = re.compile(fr"\[{tag_re}{ext_re}\]")
			tags_.add((tag, tag_re, ext_re, re_tag_open))
		self.tags = frozenset(tags_)

	def parse(self: "typing.Self", line: str) -> str:
		r"""
		parse dsl markup in `line` and return clean valid dsl markup.

		:type line: str
		:param line: line with dsl formatting.

		:rtype: str
		"""
		line = self.put_brackets_away(line)
		line = self._parse(line)
		return self.bring_brackets_back(line)

	def _parse(self: "typing.Self", line: str) -> str:
		items = self._split_line_by_tags(line)
		return self._tags_and_text_loop(items)

	def _split_line_by_tags(
		self: "typing.Self",
		line: str,
	) -> "Iterable[DSLParser.EVENT]":
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
		m_open = False
		while ptr < len(line):
			bracket = line.find("[", ptr)
			if bracket != -1:
				chunk = line[ptr:bracket]
			else:
				chunk = line[ptr:]

			if chunk:
				yield State.TEXT, chunk

			if bracket == -1:
				break

			ptr = bracket
			# at least two chars after opening bracket:
			bracket = line.find("]", ptr + 2)
			if line[ptr + 1] == "/":
				tag = line[ptr + 2:bracket]
				yield State.CLOSE, tag
				ptr = bracket + 1
				if tag[0] == "m":
					m_open = False
				continue

			for tag, _, _, re_tag_open in self.tags:
				if re_tag_open.match(line[ptr:bracket + 1]):
					tagObj = _tag.Tag(line[ptr + 1:bracket], tag)
					break
			else: # FIXME: is this needed?
				tag = line[ptr + 1:bracket]
				tagObj = _tag.Tag(tag, tag)

			if tagObj.closing == "m":
				if m_open:
					yield State.CLOSE, "m"
				else:
					m_open = True
			yield State.OPEN, tagObj

			ptr = bracket + 1

		if m_open:
			yield State.CLOSE, "m"

	@staticmethod
	def _tags_and_text_loop(
		tags_and_text: "Iterable[DSLParser.EVENT]",
	) -> str:
		"""
		parse chunks one by one.
		"""
		state: State = State.TEXT
		stack: List[_layer.Layer] = []
		closings: Set[str] = set()

		for event, item in tags_and_text:
			# TODO: break into functions like:
			# state = handle_tag_open(_tag, stack, closings, state)
			if event is State.OPEN:
				assert isinstance(item, _tag.Tag)  # linter is not smart enough to infer this fact

				if _tag.was_opened(stack, item) and item.closing not in closings:
					continue

				if item.closing == "m" and len(stack) >= 1:
					# close all layers. [m*] tags can only appear
					# at top layer.
					# note: do not reopen tags that were marked as
					# closed already.
					to_open = set.union(*(
						{t for t in layer.tags if t.closing not in closings}
						for layer in stack
					))
					for _ in range(len(stack)):
						_layer.close_layer(stack)
					# assert len(stack) == 1
					# assert not stack[0].tags
					_layer.Layer(stack)
					stack[-1].tags = to_open

				elif state is State.CLOSE:
					process_closing_tags(stack, closings)

				if not stack or stack[-1].text:
					_layer.Layer(stack)

				stack[-1].tags.add(item)
				state = State.OPEN
				continue

			if event is State.CLOSE:
				assert isinstance(item, str)  # linter is not smart enough to infer this fact

				if state in (State.OPEN, State.TEXT):
					closings.clear()
				closings.add(item)
				state = State.CLOSE
				continue

			if event is State.TEXT:
				assert isinstance(item, str)  # linter is not smart enough to infer this fact

				if state is State.CLOSE:
					process_closing_tags(stack, closings)

				if not stack:
					_layer.Layer(stack)
				stack[-1].text += item
				state = State.TEXT
				continue

		if state is State.CLOSE and closings:
			process_closing_tags(stack, closings)
		# shutdown unclosed tags
		return "".join(layer.text for layer in stack)

	def put_brackets_away(self: "typing.Self", line: str) -> str:
		r"""put away \[, \] and brackets that does not belong to any of given tags.

		:rtype: str
		"""
		clean_line = ""
		startswith_tag = _startswith_tag_cache.get(self.tags, None)
		if startswith_tag is None:
			openings = "|".join(f"{_[1]}{_[2]}" for _ in self.tags)
			closings = "|".join(_[1] for _ in self.tags)
			startswith_tag = re.compile(
				fr"(?:(?:{openings})|/(?:{closings}))\]",
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
			else:  # first chunk
				clean_line += chunk.replace("[", BRACKET_L)\
					.replace("]", BRACKET_R)
		return clean_line

	@staticmethod
	def bring_brackets_back(line: str) -> str:
		return line.replace(BRACKET_L, "[").replace(BRACKET_R, "]")
