# -*- coding: utf-8 -*-
# appledict/indexes/ru.py
""" russian indexes based on pymorphy."""
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

from . import languages, log

try:
    import pymorphy2
except ImportError:
    log.error("""module pymorphy2 is required to build extended russian indexes.  \
you can download it here: http://pymorphy2.readthedocs.org/en/latest/.  \
or run `pip2 install pymorphy2`.
""")
    raise
else:
    morphy = pymorphy2.MorphAnalyzer()


def ru(titles, _):
    """
    gives a set of all declines, cases and other froms of word `title`.
    note that it works only if title is one word.

    :type titles: Sequence[str]
    :rtype: Set[str]
    """
    indexes = set()
    for title in titles:
        indexes.update(_ru(title))
    return indexes


def _ru(title):
    # feature: put dot at the end to match only this word
    a = {title, title + "."}

    # decline only one-word titles
    if len(title.split()) == 1:

        normal_forms = morphy.parse(title.decode('utf-8'))

        if len(normal_forms) > 0:

            # forms of most probable match
            normal_form = normal_forms[0]

            for x in normal_form.lexeme:
                word = x.word.encode('utf-8')
                # Apple Dictionary Services see no difference between
                # 'й' and 'и', 'ё' and 'е', so we're trying to avoid
                # "* Duplicate index. Skipped..." warning.
                word = word.replace('й', 'и').replace('ё', 'е')
                a.add(word)

    return a


languages['ru'] = ru
