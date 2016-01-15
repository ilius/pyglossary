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

import hashlib
import re

def truncate(text, length=449):
    """
    trunct a string to given length
    :param str text:
    :return: truncated text
    :rtype: str
    """
    content = re.sub('(\t|\n|\r)', ' ', text)
    if (len(text)>length):
        # find the next space after max_len chars (do not break inside a word)
        pos = content[:length].rfind(' ')
        if pos == -1:
            pos = length
        text = text[:pos]
    return text

def write_xml(glos, filename, cleanHTML, frontBackMatter):
    try:
        from bs4 import BeautifulSoup
    except:
        try:
            from BeautifulSoup import BeautifulSoup
        except:
            cleanHTML = False
    # progress bar
    ui = glos.ui
    if ui:
        ui.progressStart()

    f = open(filename, 'wb')

    # write header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n')

    if frontBackMatter:
        with open(frontBackMatter, 'r') as front_back_matter:
            f.write(front_back_matter.read())

    # write entries
    entry_ids = set([])
    total = len(glos.data)
    close_tag = re.compile('<(BR|HR)>', re.IGNORECASE)
    nonprintable = re.compile('[\x00-\x07\x0e-\x1f]')
    img_tag = re.compile('<IMG (.*?)>', re.IGNORECASE)
    for index, item in enumerate(glos.data):
        # strip double quotes and html tags
        title = re.sub('<[^<]+?>|"|[<>]|\xef\xbb\xbf', '', item[0])
        if not title:
            continue
        # use MD5 hash of title string as id
        id = hashlib.md5(title).hexdigest()

        # check entry id duplicates
        while id in entry_ids:
            id = id + '_'
        entry_ids.add(id)
        # get alternatives list
        try:
            alts = item[2]['alts']
        except:
            alts = []

        # begin entry
        f.write('<d:entry id="%(id)s" d:title="%(title)s">\n'%{'id':id, 'title':truncate(title.replace('&', '&amp;'), 1126)})

        # index values
        #   title as index
        f.write('    <d:index d:value="%s"/>\n'%truncate(title))
        #   alternative items as index also
        for alt in alts:
            if alt != title:
                f.write('    <d:index d:value="%s"/>\n'%truncate(alt))

        # nice header to display
        content = ('<h1>%s</h1>\n'%title) + item[1]
        # xhtml is strict
        if cleanHTML:
            soup  = BeautifulSoup(content, from_encoding='utf8')
            content = str(soup)
        else:
            content = close_tag.sub('<\g<1> />', content)
            content = img_tag.sub('<img \g<1>/>', content)
        content = content.replace('&nbsp;', '&#160;')
        content = nonprintable.sub('', content)
        f.write(content)

        # end entry
        f.write('\n</d:entry>\n')

        if index%1000==0 and ui:
            ui.progress(1.0*index/total)
    # end dictionary
    f.write('</d:dictionary>\n')
    f.close()

    # end progress bar
    if ui:
        ui.progressEnd()