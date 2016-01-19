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

__all__ = ['read']

import codecs
import re
from xml.sax.saxutils import escape, quoteattr

def make_a_href(s):
    return '<a href=%s>%s</a>' % (quoteattr(s), escape(s))

def ref_sub(x):
    return make_a_href(x.groups()[0])

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

    line = fix_misplaced_dsl_tags(line)

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
    line = re.sub('\[/c\]', '</span>', line)

    # example zone
    line = re.sub('\[ex\]', '<span class="ex" style="color:steelblue">', line)
    line = re.sub('\[/ex\]', '</span>', line)

    # secondary zone
    line = line.replace('[*]', '<span class="sec">').replace('[/*]', '</span>')

    # abbrev. label
    line = re.sub('\[p\]', '<i class="p" style="color:green">', line)
    line = re.sub('\[/p\]', '</i>', line)

    # cross reference
    line = line.replace('[ref]', '<<').replace('[/ref]', '>>')
    line = line.replace('[url]', '<<').replace('[/url]', '>>')
    line = re.sub('<<(.*?)>>', ref_sub, line)

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
    line = line.replace('[m]', '[m1]')
    # if line somewhere contains '[m_]' tag like
    # """[b]I[/b][m1] [c][i]conj.[/i][/c][/m][m1]1) ..."""
    # then leave it alone.  only wrap in '[m1]' when no 'm' tag found at all.
    if not re.search(r'(?<!\\)\[m\d\]', line):
        line = '[m1]%s[/m]' % line
    line = re.sub(r'\[m(\d)\](.*?)\[/m\]', '<div style="margin-left:\g<1>em">\g<2></div>', line)

    # \[...\]
    line = re.sub('\\\\(\[|\])', '\g<1>', line)
    return line

def fix_misplaced_dsl_tags(line, tags=(
        'b',
        '\'',
        'c',
        'i',
        'sup',
        'sub',
        'ex',
        'p',
        r'\*'
)):
    """
    fix unclosed tags like [b]...[c]...[/b]...[/c]
    change it to [b]...[c]...[/c][/b][c]...[/c]
    """
    # for tags like:[p]n[/c][/i][/p], the line needs scan again
    prevLine = ''
    while prevLine != line:
        prevLine = line
        for tag in tags:
            otherTags = list(tags)
            otherTags.remove(tag)
            searchExpression = '\[%s\](?P<content>[^\[\]]*)(?P<wrongTag>\[/(%s)\])' % (
                tag,
                '|'.join(otherTags),
            )
            replaceExpression = '[%s]\g<content>[/%s]\g<wrongTag>[%s]' % (
                tag,
                tag,
                tag,
            )
            line = re.sub(searchExpression, replaceExpression, line)
        # empty tags may appear as a result of replaces above: [b][i][/i][/b]
        for tag in tags:
            line = re.sub(r'\[%s]\[/%s\]' % (tag, tag), '', line)

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
                    if unfinished_line:
                        # line may be skipped if ill formated
                        current_text.append(_clean_tags(unfinished_line, audio))
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

