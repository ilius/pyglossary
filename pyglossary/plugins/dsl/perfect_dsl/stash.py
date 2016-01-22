# -*- coding: utf-8 -*-
# perfect_dsl/stash.py
#
""" utility class to temporary stash away chunks of text."""
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

import re


class Stash(object):
    """
    replace matched part of string with simple unique stub and losslessly expand it them back.
    """
    def __init__(self, prefix):
        """
        :param prefix: prefix to generated XML entity.
        :return:
        """
        self.prefix = prefix
        self.stash = []
        self.next = 0

    def save(self, line, start, end):
        """
        :return: modified string
        """
        if end is None:
            end = len(line)
        stub = '\0&%s.%d;' % (self.prefix, self.next)
        self.stash.append(self.pop(line[start:end]))
        self.next += 1
        return '%s%s%s' % (line[:start], stub, line[end:])

    def pop(self, line):
        """
        expand stub items back.

        :param line: str
        :return: str
        """
        stub_re = re.compile(r'\x00&%s.(\d+);' % self.prefix)
        delta = 0
        for m in stub_re.finditer(line):
            expand = self.stash[int(m.group(1))]
            line = '%s%s%s' % (line[:m.start() + delta], expand, line[m.end() + delta:])
            delta += len(expand) - len(m.group())
        return line

    def clear(self):
        del self.stash[:]
        self.next = 0
