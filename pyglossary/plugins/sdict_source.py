# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'SdictSource'
description = 'Sdictionary Source (sdct)'
extentions = ['.sdct']
readOptions = []
writeOptions = [
    'writeInfo',## bool
    'newline',## str, or choice ('\r\n', '\n', or '\r')
]

def write(glos, filename, writeInfo=True, newline='\n'):
    ## Source Glossary for "Sdictionary" (http://sdict.org)
    ## It has extention '.sdct'
    head = ''
    if writeInfo:
        head += '<header>\n'
        head += 'title = %s\n'%glos.getInfo('name')
        head += 'author = %s\n'%glos.getInfo('author')
        head += 'description = %s\n'%glos.getInfo('description')
        head += 'w_lang = %s\n'%glos.getInfo('inputlang')
        head += 'a_lang = %s\n'%glos.getInfo('outputlang')
        head += '</header>\n#\n#\n#\n'
    glos.writeTxt(
        ('___', newline),
        filename,
        writeInfo=False,
        rplList=(
            ('\n', '<BR>'),
        ),
        ext='.sdct',
        head=head,
    )


