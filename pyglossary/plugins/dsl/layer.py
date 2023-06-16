
import typing

# -*- coding: utf-8 -*-
#
# Copyright © 2016 ivan tkachenko me@ratijas.tk
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
internal stuff. Layer class
"""

from typing import Iterable

from . import tag


class Layer(object):

	__slots__ = ["tags", "text"]

	def __init__(self: "typing.Self", stack: "list[Layer]") -> None:
		stack.append(self)
		self.tags = set()
		self.text = ""

	def __contains__(self: "typing.Self", tag: "tag.Tag") -> bool:
		return tag in self.tags

	def __repr__(self: "typing.Self") -> str:
		tags = "{" + ", ".join(map(str, self.tags)) + "}"
		return f"Layer({tags}, {self.text!r})"

	def __eq__(self: "typing.Self", other: "Layer") -> bool:
		"""
		mostly for unittest.
		"""
		return self.text == other.text and self.tags == other.tags


i_and_c = {tag.Tag("i", "i"), tag.Tag("c", "c")}
p_tag = tag.Tag("p", "p")


def close_tags(
	stack: "Iterable[Layer]",
	tags: "Iterable[tag.Tag]",
	layer_index: bool = -1,
) -> None:
	"""
	close given tags on layer with index `layer_index`.
	"""
	if layer_index == -1:
		layer_index = len(stack) - 1
	layer = stack[layer_index]

	if layer.text:
		tags = set.intersection(layer.tags, tags)
		if not tags:
			return

		# shortcut: [i][c] equivalent to [p]
		if tags.issuperset(i_and_c):
			tags -= i_and_c
			tags.add(p_tag)
			layer.tags -= i_and_c
			# no need to layer.tags.add()

		ordered_tags = tag.canonical_order(tags)
		layer.text = "".join(
			[f"[{x.opening}]" for x in ordered_tags] +
			[layer.text] +
			[f"[/{x.closing}]" for x in reversed(ordered_tags)],
		)

	# remove tags from layer
	layer.tags -= tags
	if layer.tags or layer_index == 0:
		return
	superlayer = stack[layer_index - 1]
	superlayer.text += layer.text
	del stack[layer_index]


def close_layer(stack: "list[Layer]") -> None:
	"""
	close top layer on stack.
	"""
	if not stack:
		return
	tags = stack[-1].tags
	close_tags(stack, tags)
