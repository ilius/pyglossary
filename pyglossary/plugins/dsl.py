# -*- coding: utf-8 -*-
## dsl.py
## Read ABBYY Lingvo DSL dictionary format
##
## Copyright (C) 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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


import codecs
import re

enable = True
format = 'ABBYYLingvoDSL'
description = 'ABBYY Lingvo DSL (dsl)'
extentions = ['.dsl']
readOptions = ['encoding','audio']
writeOptions = []
def _clean_tags(line, audio):
    # remove {{...}} blocks
    line = re.sub('\{\{[^}]*\}\}','', line)

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
    
    #fix unclosed tag like [b]...[c]...[/b]...[/c]
    #change it to [b]...[c]...[/c][/b][c]...[/c]
    import string
    import copy
    tags = ['b','\'','c','i','sup','sub','ex','p']
    #for tags like:[p]n[/c][/i][/p], these line need scan again
    change = True
    while change == True:
        origin = line
        for tag in tags:
            temp = copy.deepcopy(tags)
            temp.remove(tag)
            include_tag = string.join(temp,'|')
            search_expression = '\['+ tag +'\](?P<content>[^\[\]]*)(?P<wrongTag>\[/('+ include_tag +')\])'
            replace_expression = '[' + tag + ']' + '\g<content>' + '[/' + tag + ']' + '\g<wrongTag>' + '[' + tag + ']'
            line = re.sub(search_expression,replace_expression,line)
        if line == origin:
            change = False
        else:
            change = True

    print 'clean' + line

    # text formats
    line = re.sub("\[(/?)'\]", '<\g<1>u>', line)
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
    line = re.sub('\[s\]([^[]*?)(jpg|jpeg|gif|tif|tiff)\s*\[/s\]',
                  '<img align="top" src="\g<1>\g<2>" alt="\g<1>\g<2>" />', line)

    # \[...\]
    line = re.sub('\\\\(\[|\])', '\g<1>', line)
    return line

def read(glos, fname, **options):
    encoding = options.get('encoding', 'utf-8')
    audio = (options.get('audio', 'no') == 'yes')

    f = codecs.open(fname, 'r', encoding)

    current_key = ''
    current_key_alters = []
    current_text = []
    line_type = 'header'
    unfinished_line = ''

    glos.data = []
    for line in f:
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
        # title word(s)
        elif line[0] not in ['\t', ' ']:
            # alternative titles
            if line_type == 'title':
                current_key_alters += [line]
            # previous line type is text -> start new title
            else:
                # append previous entry
                if line_type == 'text':
                    glos.data += [(current_key, '\n'.join(current_text), {'alts' : current_key_alters})]
                # start new entry
                current_key = line
                current_key_alters = []
                current_text = []
                unfinished_line = ''
            line_type = 'title'
        # texts
        else:
            # indent level
            m = re.search('\[m(\d)\]', line)
            if m:
                indent = int(m.groups()[0])
            else:
                indent = 0
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
            else:
                unfinished_line = ''

            # convert DSL tags to HTML tags
            line = _clean_tags(line, audio)
            #current_text += ['<br />' + '&#160;' * indent + line.lstrip()]
            current_text += ['<div style="margin-left:%dem">'%(indent) + line + '</div>']

    # last entry
    if line_type == 'text':
        glos.data += [(current_key, '\n'.join(current_text), {'alts' : current_key_alters})]

    return glos
