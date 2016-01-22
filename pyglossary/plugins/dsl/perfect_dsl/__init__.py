# -*- coding: utf-8 -*-
# perfect_dsl/__init__.py
#
""" only clean perfect DSL markup on output!"""
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

from .stash import Stash

BRACKET_L = '\0\1'
BRACKET_R = '\0\2'


class PerfectDSLParser(object):
    """
    only clean perfect dsl on output!
    """

    def __init__(self, tags=frozenset({
        'b',
        '\'',
        ('c', '(?: \w+)?'),
        'i',
        'sup',
        'sub',
        'ex',
        'p',
        r'\*',
        ('m', '\d'),
    })):
        """
        :type tags: set[str | tuple[str]] | frozenset[str | tuple[str]]
        :param tags: set (or any other iterable) of tags where each tag is a
                     string or two-tuple.  if string, it is tag name without
                     brackets, non-save regex characters must be escaped,
                     e.g.: 'i', 'sub', "\*".
                     if 2-tuple, then first item is tag's base name, and
                     second is its extension for opening tag,
                     e.g.: ('c', r' (\w+)'), ('m', r'\d')
        """
        self.tags = frozenset({t if isinstance(t, tuple) else (t, '') for t in tags})
        self.stash = Stash('dsl')

    def parse(self, line):
        r"""
        parse dsl markup in `line` and return clean valid dsl markup.

        :type line: str
        :param line: line with dsl formatting.

        :rtype: str

        four cases when something went wrong:

        1. ^...[/tag],,,  =>  ^...,,,
        2. ...[tag],,,$  =>  ...,,,$
        3. ...[tag1],,,[/tag2]+++  =>  ...[tag1],,,[/tag1][/tag2][tag1]+++  => ...{}[/tag2][tag1]+++
        4. ...[tag][/tag],,,  => ...,,,

        case 5 where everything alright.

        5. ...[tag],,,[/tag]+++  =>  ...{}+++

        case 4 can appear after any of them including itself (consider markup "[b][i][/i][/b]"),
        so it needs to be executed after every step.
        """
        line = self.put_brackets_away(line, self.tags)
        paragraphs, m_tags = self.split_line_by_paragraphs(line)
        # paragraphs does not contain valid [m_]...[/m] tags.  invadid standalone tags will be removed by parser.
        paragraphs = map(self._parse_paragraph, paragraphs)
        line = self.join_paragraphs(paragraphs, m_tags)
        return self.bring_brackets_back(line)

    @staticmethod
    def put_brackets_away(line, tags):
        """put away \[, \] and brackets that does not belong to any of given tags.

        :rtype: str
        """
        clean_line = ''
        openings = '|'.join('%s%s' % _ for _ in tags)
        closings = '|'.join(_[0] for _ in tags)
        startswith_tag = re.compile(r'(?:(?:%s)|/(?:%s))\]' % (openings, closings))
        for i, chunk in enumerate(re.split(r'(?<!\\)\[', line)):
            if i != 0:
                m = startswith_tag.match(chunk)
                if m:
                    clean_line += '[%s%s' % (m.group(), chunk[m.end():].replace('[', BRACKET_L).replace(']', BRACKET_R))
                else:
                    clean_line += BRACKET_L + chunk.replace('[', BRACKET_L).replace(']', BRACKET_R)
            else:  # firsr chunk
                clean_line += chunk.replace('[', BRACKET_L).replace(']', BRACKET_R)
        return clean_line


    @staticmethod
    def bring_brackets_back(line):
        return line.replace(BRACKET_L, '[').replace(BRACKET_R, ']')

    @staticmethod
    def split_line_by_paragraphs(line):
        """
        :type line: str
        :rtype: tuple(list[str], list[str])

        :return: list of markup lines between and inside [m_]...[/m] tags and list of "[m_", "[/m]" tags.
         list of lines always be one item longer than list of tags.
         for example:
         "...[m1],,,[/m]+++[m2]```[/m]***"  =>  ["...", ",,,", "+++", "```", "***"], ["[m1]", "[/m]", "[m2]", "[/m]"]
         "[m1]...[/m]"  =>  ["", "...", ""], ["[m1]", "[/m]"]
         note the empty strings in first of returned lists in second example.
        """
        paragraphs = []
        m_tags = []
        last_pos = 0
        for i, m in enumerate(re.finditer(r'(\[m\d\])(.*?)(\[/m\])', line)):
            paragraphs.extend((line[last_pos:m.start()], m.group(2)))
            m_tags.extend((m.group(1), m.group(3)))
            last_pos = m.end()
        paragraphs.append(line[last_pos:])
        return paragraphs, m_tags

    @staticmethod
    def join_paragraphs(paragraphs, m_tags):
        """
        :type paragraphs: Iterable[str]
        :type m_tags: Iterable[str]

        :rtype: str
        """
        return ''.join(map(''.join, zip(paragraphs, m_tags))) + paragraphs[-1]

    def _parse_paragraph(self, para):
        """
        :type para: str
        :rtype: str
        """
        stash = self.stash
        stash.clear()
        tags = self.tags
        non_open = r'[^\[]'

        prev_line = ''
        while prev_line != para:
            prev_line = para
            for tag, ext in tags:
                tag_open_re = r'\[%s%s\]' % (tag, ext)
                tag_close_re = r'\[/%s\]' % tag
                tag_close_s = '[/%s]' % tag

                # case 1.
                # XXX: no way str.startswith, `tag` may itself be a regex
                m = re.match(r'(?:%(non_open)s)*(%(tag_close_re)s)' %
                             {'non_open': non_open, 'tag_close_re': tag_close_re}, para)
                if m:
                    para = '%s%s' % (para[:m.start(1)], para[m.end():])

                # case 2.
                m = re.search(r'(%(tag_open_re)s)(?:%(non_open)s)*$' %
                              {'tag_open_re': tag_open_re, 'non_open': non_open}, para)
                if m:
                    para = '%s%s' % (para[:m.start()], para[m.end(1):])
                    # para += tag_close_s
                    # para = stash.save(para, m.start(), None)

                # case 3.
                closings = '|'.join(t for t, _ in tags if t != tag)

                # keep propagating with current tag
                m = True
                while m:
                    m = re.search(r'(?P<self>%(tag_open_re)s)(?P<txt>(?:%(non_open)s)*)(?P<other>\[/(?:%(others)s)\])' %
                                  {'tag_open_re': tag_open_re, 'non_open': non_open, 'others': closings}, para)
                    if m:
                        opening = m.group('self')
                        txt = m.group('txt')
                        other = m.group('other')
                        if not txt:
                            # don't stash, just swap tags: [i][/c]  =>  [/c][i]
                            para = '%s%s%s%s' % (para[:m.start()], other, opening, para[m.end():])
                        else:
                            o_start = m.start('other')
                            o_end = m.end('other')
                            replacement = '%s%s%s' % (tag_close_s, other, opening)
                            para = '%s%s%s' % (para[:o_start], replacement, para[o_end:])
                            para = stash.save(para, m.start(), o_start + len(tag_close_s))

                # case 4.
                m = re.search(r'%s%s' % (tag_open_re, tag_close_re), para)
                if m:
                    para = '%s%s' % (para[:m.start()], para[m.end():])

                # case 5.
                m = re.search(r'%s(?:%s)+%s' % (tag_open_re, non_open, tag_close_re), para)
                if m:
                    para = stash.save(para, m.start(), m.end())

        return stash.pop(para)


def parse(line, tags=None):
    if tags:
        parser = PerfectDSLParser(tags)
    else:
        parser = PerfectDSLParser()
    return parser.parse(line)


put_brackets_away = PerfectDSLParser.put_brackets_away
bring_brackets_back = PerfectDSLParser.bring_brackets_back
