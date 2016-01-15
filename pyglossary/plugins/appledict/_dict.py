# -*- coding: utf-8 -*-
## appledict/_appledict.py
## Output to Apple Dictionary xml sources for Dictionary Development Kit.
##
## Copyright (C) 2012 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, version 3 of the License.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

import re
import string

from . import _normalize

def dictionary_begin(glos, f, frontBackMatter):
    # progress bar
    if glos.ui:
        glos.ui.progressStart()

    # write header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

    if frontBackMatter:
        with open(frontBackMatter, 'r') as front_back_matter:
            f.write(front_back_matter.read())

def get_beautiful_soup():
    try:
        import bs4 as BeautifulSoup
    except:
        try:
            import BeautifulSoup
        except:
            return None
    return BeautifulSoup

digs = string.digits + string.letters

def base36(x):
    """
    simplified version of int2base
    http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python#2267446
    """
    digits = []
    while x:
        digits.append(digs[x % 36])
        x /= 36
    digits.reverse()
    return ''.join(digits)

def id_generator():
    # closure
    cnt = [1]

    def generate_id():
        s = '_%s' % base36(cnt[0])
        cnt[0] += 1
        return s

    return generate_id

def indexes_generator():
    # it will be factory that atcs according to glossary language
    def generate_indexes(title, alts, BeautifulSoup):
        indexes = [_normalize.title_long(title), _normalize.title_short(title)]
        for alt in alts:
            normal = _normalize.title(alt, BeautifulSoup)
            indexes.append(_normalize.title_long(normal))
            indexes.append(_normalize.title_short(normal))
        indexes = set(indexes)
        s = ''
        for idx in indexes:
            if BeautifulSoup:
                s += '<d:index d:value=%s/>' % BeautifulSoup.dammit.EntitySubstitution.substitute_xml(idx, True)
            else:
                s += '<d:index d:value="%s"/>' % idx.replace('>', '&gt;')
        return s
    return generate_indexes


close_tag = re.compile('<(BR|HR)>', re.IGNORECASE)
nonprintable = re.compile('[\x00-\x07\x0e-\x1f]')
img_tag = re.compile('<IMG (.*?)>', re.IGNORECASE)

def format_clean_content(title, body, BeautifulSoup):
    # nice header to display
    content = '<h1>%s</h1>%s' % (title, body)
    # xhtml is strict
    if BeautifulSoup:
        soup = BeautifulSoup.BeautifulSoup(content, from_encoding='utf-8')
        b = soup.body  # difference between 'lxml' and 'html.parser'
        content = ''.join(map(str, (b if b else soup).contents))
    else:
        content = close_tag.sub('<\g<1> />', content)
        content = img_tag.sub('<img \g<1>/>', content)
    content = content.replace('&nbsp;', '&#160;')
    content = nonprintable.sub('', content)
    return content

def write_entries(glos, f, cleanHTML):
    if cleanHTML:
        BeautifulSoup = get_beautiful_soup()
        if not BeautifulSoup:
            import logging
            log = logging.getLogger('root')
            log.warn('cleanHTML option passed but BeautifulSoup not found.  '
                     'to fix this run `easy_install beautifulsoup4` or '
                     '`pip2 install beautifulsoup4`.')
    else:
        BeautifulSoup = None

    # write entries
    generate_id = id_generator()
    generate_indexes = indexes_generator()
    total = float(len(glos.data))

    for i, item in enumerate(glos.data):
        title = _normalize.title(item[0], BeautifulSoup)
        if not title:
            continue

        id = generate_id()
        if BeautifulSoup:
            norm_long = BeautifulSoup.dammit.EntitySubstitution.substitute_xml(_normalize.title_long(title), True)
        else:
            norm_long = '"%s"' % _normalize.title_long(title)

        begin_entry = '<d:entry id="%(id)s" d:title=%(title)s>\n' % {
            'id': id,
            'title': norm_long,
        }
        f.write(begin_entry)

        # get alternatives list
        try:
            alts = item[2]['alts']
        except:
            alts = []

        indexes = generate_indexes(title, alts, BeautifulSoup)
        f.write(indexes)

        content = format_clean_content(title, item[1], BeautifulSoup)
        f.write(content)

        end_entry = '\n</d:entry>\n'
        f.write(end_entry)

        if i % 1000 == 0 and glos.ui:
            glos.ui.progress(i / total)

def dictionary_end(glos, f):
    f.write('</d:dictionary>\n')

    # end progress bar
    if glos.ui:
        glos.ui.progressEnd()

def write_xml(glos, filename, cleanHTML, frontBackMatter):
    with open(filename, 'wb') as f:
        dictionary_begin(glos, f, frontBackMatter)
        write_entries(glos, f, cleanHTML)
        dictionary_end(glos, f)
