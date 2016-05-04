# -*- coding: utf-8 -*-

## Source Glossary for "Babylon Builder".
## A plain text file. Not binary like BGL files.

from formats_common import *

enable = True
format = 'BabylonSource'
description = 'Babylon Source (gls)'
extentions = ['.gls', '.babylon']
readOptions = []
writeOptions = [
    'writeInfo',
    'newline',
    'encoding',
]

def entryRecodeToWinArabic(entry):
    from pyglossary.arabic_utils import recodeToWinArabic
    entry.editFuncWord(recodeToWinArabic)
    entry.editFuncDefi(recodeToWinArabic)
    return entry

def write(glos, filename, writeInfo=True, newline='', encoding=''):
    g = glos
    entryFilterFunc = None
    if encoding.lower() in ('', 'utf8', 'utf-8'):
        encoding = 'UTF-8'
    elif encoding.lower() in (
        'arabic',
        'windows-1256',
        'windows-arabic',
        'arabic-windows',
        'arabic windows',
        'windows arabic',
    ):
        encoding = 'Arabic'
        entryFilterFunc = entryRecodeToWinArabic
        if not newline:
            newline='\r\n'

    if not newline:
        newline = '\n'

    head = ''
    if writeInfo:
        head += newline.join([
            '### Glossary title:%s'%g.getInfo('name'),
            '### Author:%s'%g.getInfo('author'),
            '### Description:%s'%g.getInfo('description'),
            '### Source language:%s'%g.getInfo('inputlang'),
            '### Source alphabet:%s'%encoding,
            '### Target language:%s'%g.getInfo('outputlang'),
            '### Target alphabet:%s'%encoding,
            '### Browsing enabled?Yes',
            '### Type of glossary:00000000',
            '### Case sensitive words?0'
            '%s### Glossary section:',
            '',
        ])

    g.writeTxt(
        (newline, newline*2),
        filename=filename,
        writeInfo=False,
        rplList=(
            ('\n', '<BR>'),
        ),
        ext='.gls',
        head=head,
        entryFilterFunc=entryFilterFunc,
    )

