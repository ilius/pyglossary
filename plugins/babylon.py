# -*- coding: utf-8 -*-

## Source Glossary for "Babylon Builder".
## A plain text file. Not binary like BGL files.

enable = True
format = 'Babylon'
description = 'Babylon Source (gls)'
extentions = ['.gls', '.babylon']
readOptions = []
writeOptions = [
    'writeInfo',
    'newline',
    'encoding',
]

from text_utils import recodeToWinArabic

def write(glos, filename, writeInfo=True, newline='', encoding=''):
    g = glos
    if encoding.lower() in ('', 'utf8', 'utf-8'):
        encoding = 'UTF-8'
    else:
        g = glos.copy()
        if encoding.lower() in (
            'arabic',
            'windows-1256',
            'windows-arabic',
            'arabic-windows',
            'arabic windows',
            'windows arabic',
        ):
            encoding = 'Arabic'
            for i in xrange(len(g.data)):
                for j in 0, 1:
                    g.data[i][j] = recodeToWinArabic(g.data[i][j])
            if not newline:
                newline='\r\n'
        else:
            for i in xrange(len(g.data)):
                for j in 0, 1:
                    g.data[i][j] = g.data[i][j].decode('utf8').encode(encoding)
    if not newline:
        newline = '\n'
    head = ''
    if writeInfo:
        head += '### Glossary title:%s%s' %(g.getInfo('name'), newline)
        head += '### Author:%s%s'%(g.getInfo('author'), newline)
        head += '### Description:%s%s'%(g.getInfo('description'), newline)
        head += '### Source language:%s%s'%(g.getInfo('inputlang'), newline)
        head += '### Source alphabet:%s%s'%(encoding, newline)
        head += '### Target language:%s%s'%(g.getInfo('outputlang'), newline)
        head += '### Target alphabet:%s%s'%(encoding, newline)
        head += '### Browsing enabled?Yes%s'%newline
        head += '### Type of glossary:00000000%s'%newline
        head += '### Case sensitive words?0%s'%newline
        head += '%s### Glossary section:%s'%(newline, newline)
    g.writeTxt(
        (newline, newline*2),
        filename=filename,
        writeInfo=False,
        rplList=(
            ('\n', '<BR>'),
        ),
        ext='.gls',
        head=head,
    )

