# -*- coding: utf-8 -*-
#
# Copyright © 2016 Ratijas <ratijas.t@me.com>
# Copyright © 2016-2017 Saeed Rasooli <saeed.gnu@gmail.com>
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
internal stuff. Tag class
"""


from collections import namedtuple
from typing import Iterable

from . import layer as _layer

Tag = namedtuple("Tag", ["opening", "closing"])

Tag.__repr__ = lambda tag: \
	f"Tag({tag.opening!r})" if tag.opening == tag.closing \
	else f"Tag({tag.opening!r}, {tag.closing!r})"

predefined = [
	"m",
	"*",
	"ex",
	"i",
	"c",
]


def was_opened(stack: "Iterable[_layer.Layer]", tag: "Tag") -> bool:
	"""
	check if tag was opened at some layer before.
	"""
	if not len(stack):
		return False
	layer = stack[-1]
	if tag in layer:
		return True
	return was_opened(stack[:-1], tag)


def canonical_order(tags: "Iterable[Tag]") -> "list[Tag]":
	"""
	arrange tags in canonical way, where (outermost to innermost):
	m  >  *  >  ex  >  i  >  c
	with all other tags follow them in alphabetical order.
	"""
	result = []
	tags = list(tags)
	for predef in predefined:
		t = next((t for t in tags if t.closing == predef), None)
		if t:
			result.append(t)
			tags.remove(t)
	result.extend(sorted(tags, key=lambda x: x.opening))
	return result


def index_of_layer_containing_tag(
	stack: "Iterable[_layer.Layer]",
	tag: str,
) -> "int | None":
	"""
	return zero based index of layer with `tag` or None
	"""
	for i, layer in enumerate(reversed(stack)):
		for t in layer.tags:
			if t.closing == tag:
				return len(stack) - i - 1
	return None
