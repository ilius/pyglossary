# -*- coding: utf-8 -*-
## dsl.py
## Read ABBYY Lingvo DSL dictionary format
##
## Copyright (C) 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
## Copyright (C) 2013 Saeed Rasooli <saeed.gnu@gmail.com>
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

from formats_common import *

enable = True
format = 'ABBYYLingvoDSL'
description = 'ABBYY Lingvo DSL (dsl)'
extentions = ['.dsl']
readOptions = ['encoding', 'audio']
writeOptions = []


import codecs
import re


def _clean_tags(line, audio):
    # remove {{...}} blocks
    line = re.sub('\{\{[^}]*\}\}', '', line)

    # remove trn tags
    line = re.sub('\[\/?!?tr[ns]\]', '', line)
    # remove lang tags
    line = re.sub('\[\/?lang[^\]]*\]', '', line)
    # remove com tags
    line = re.sub('\[/?com\]', '', line)
    # remove t tags
    line = re.sub('\[t\]', '<!-- T --><span style=\"font-family:\'Helvetica\'\">', line)
    line = re.sub('\[/t\]', '</span><!-- T -->', line)

    # remove m tags
    line = re.sub('\[/?m\d*\]', '', line)
    # remove * tags
    line = re.sub('\[/?\*\]', '', line)
    # remove ref tags
    line = re.sub('\[/?ref[^]]*\]', '', line)
    # remove url tags
    line = re.sub('\[url\].*?\[/url\]', '', line)
    
    #fix unclosed tags like [b]...[c]...[/b]...[/c]
    #change it to [b]...[c]...[/c][/b][c]...[/c]
    tags = (
        'b',
        '\'',
        'c',
        'i',
        'sup',
        'sub',
        'ex',
        'p',
    )
    #for tags like:[p]n[/c][/i][/p], the line needs scan again
    while True:
        prevLine = line
        for tag in tags:
            otherTags = list(tags)
            otherTags.remove(tag)
            searchExpression = '\[%s\](?P<content>[^\[\]]*)(?P<wrongTag>\[/(%s)\])'%(
                tag,
                '|'.join(otherTags),
            )
            replaceExpression = '[%s]\g<content>[/%s]\g<wrongTag>[%s]'%(
                tag,
                tag,
                tag,
            )
            line = re.sub(searchExpression, replaceExpression, line)
        if line == prevLine:
            break

    #log.debug('clean' + line)

    # text formats
    line = re.sub('\[(/?)\'\]', '<\g<1>u>', line)
    line = re.sub('\[(/?)b\]', '<\g<1>b>', line)
    line = re.sub('\[(/?)i\]', '<\g<1>i>', line)
    line = re.sub('\[(/?)u\]', '<\g<1>u>', line)
    line = re.sub('\[(/?)sup\]', '<\g<1>sup>', line)
    line = re.sub('\[(/?)sub\]', '<\g<1>sub>', line)

    # color
    line = re.sub('\[c\]', '<span style="color:green">', line)
    line = re.sub('\[c (\w+)\]', '<span style="color:\g<1>">', line)
    line = re.sub('\[/c\]', ' </span>', line)

    # example zone
    line = re.sub('\[ex\]', '<span style="color:steelblue">', line)
    line = re.sub('\[/ex\]', '</span>', line)

    # abbrev. label
    line = re.sub('\[p\]', '<span style="color:green">', line)
    line = re.sub('\[/p\]', '</span>', line)

    # cross reference
    line = re.sub('<<(.*?)>>', '<a href="bword://\g<1>">\g<1></a>', line)

    # sound file
    if audio:
        sound_tag = '<object type="audio/x-wav" data="\g<1>\g<2>" width="40" height="40">' \
                    '<param name="autoplay" value="false" />' \
                    '</object>'
    else:
        sound_tag = ''
    line = re.sub('\[s\]([^[]*?)(wav|mp3)\s*\[/s\]', sound_tag, line)

    # image file
    line = re.sub(
        '\[s\]([^[]*?)(jpg|jpeg|gif|tif|tiff)\s*\[/s\]',
        '<img align="top" src="\g<1>\g<2>" alt="\g<1>\g<2>" />',
        line,
    )

    # \[...\]
    line = re.sub('\\\\(\[|\])', '\g<1>', line)
    return line

def read(glos, fname, **options):
    encoding = options.get('encoding', 'utf-8')
    audio = (options.get('audio', 'no') == 'yes')


    current_key = ''
    current_key_alters = []
    current_text = []
    line_type = 'header'
    unfinished_line = ''

    glos.data = []
    
    fp = codecs.open(fname, 'r', encoding)
    for line in fp:
        line = line.encode('utf-8').rstrip()
        if not line:
            continue
        # header
        if line.startswith('#'):
            if line.startswith('#NAME'):
                glos.setInfo('title', line[6:])
            elif line.startswith('#INDEX_LANGUAGE'):
                glos.setInfo('sourceLang', line[16:])
            elif line.startswith('#CONTENTS_LANGUAGE'):
                glos.setInfo('targetLang', line[20:])
            line_type = 'header'
        # texts
        elif line.startswith(' ') or line.startswith('\t'):
            # indent level
            m = re.search('\[m(\d)\]', line)
            indent = 0
            if m:
                try:
                    indent = int(m.groups()[0])
                except IndexError:
                    pass
            # remove m tags
            line = re.sub('\[/?m\d*\]', '', line)

            line_type = 'text'
            line = unfinished_line + line.lstrip()

            # some ill formated source may have tags spanned into multiple lines
            # try to match opening and closing tags
            tags_open  = re.findall('(?<!\\\\)\[(c |[cuib]\])', line)
            tags_close = re.findall('\[/[cuib]\]', line)
            if len(tags_open) != len(tags_close):
                unfinished_line = line
                continue

            unfinished_line = ''

            # convert DSL tags to HTML tags
            line = _clean_tags(line, audio)
            #line = '<br />' + '&#160;' * indent + line.lstrip()
            line = '<div style="margin-left:%dem">%s</div>'%(indent, line)
            current_text.append(line)
        # title word(s)
        else:
            # alternative titles
            if line_type == 'title':
                current_key_alters.append(line)
            # previous line type is text -> start new title
            else:
                # append previous entry
                if line_type == 'text':
                    glos.data.append((
                        current_key,
                        '\n'.join(current_text),
                        {
                            'alts': current_key_alters,
                        },
                    ))
                # start new entry
                current_key = line
                current_key_alters = []
                current_text = []
                unfinished_line = ''
            line_type = 'title'
    fp.close()
    
    # last entry
    if line_type == 'text':
        glos.data.append((
            current_key,
            '\n'.join(current_text),
            {
                'alts': current_key_alters,
            }
        ))

