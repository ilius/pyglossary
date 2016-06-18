# -*- coding: utf-8 -*-
# flawless_dsl/layer.py
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
internal stuff. Layer class
"""

from . import tag


class Layer(object):

    __slots__ = ['tags', 'text']

    def __init__(self, stack):
        stack.append(self)
        self.tags = set()
        self.text = ''

    def __contains__(self, tag):
        """
        :param tag: tag.Tag
        :return: bool
        """
        return tag in self.tags

    def __repr__(self):
        return 'Layer({%s}, %r)' % (', '.join(map(str, self.tags)), self.text)

    def __eq__(self, other):
        """
        mostly for unittest.
        """
        return self.text == other.text and self.tags == other.tags


i_and_c = {tag.Tag('i', 'i'), tag.Tag('c', 'c')}
p_tag = tag.Tag('p', 'p')


def close_tags(stack, tags, layer_index=-1):
    """
    close given tags on layer with index `layer_index`.

    :param stack: Iterable[Layer]
    :param layer_index: int
    :param tags: Iterable[tag.Tag]
    :return: None
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
        layer.text = '[%s]%s[/%s]' % (
            ']['.join([x.opening for x in ordered_tags]),
            layer.text,
            '][/'.join([x.closing for x in reversed(ordered_tags)]))

    # remove tags from layer
    layer.tags -= tags
    if layer.tags or layer_index == 0:
        return
    superlayer = stack[layer_index - 1]
    superlayer.text += layer.text
    del stack[layer_index]


def close_layer(stack):
    """
    close top layer on stack.
    """
    if not stack:
        return
    tags = stack[-1].tags
    close_tags(stack, tags)
