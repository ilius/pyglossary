# -*- coding: utf-8 -*-

import logging
log = logging.getLogger('root')

from formats_common import *

enable = True
format = 'LingoesLDF'
description = 'Lingoes Source (LDF)'
extentions = ['.ldf']
readOptions = []
writeOptions = []

infoKeys = [
    'title',
    'description',
    'author',
    'email',
    'website',
    'copyright',
]

def read(glos, filename):
    fileObj = FileLineWrapper(open(filename))
    lineStack = []
    def addDataEntry(lineStack):
        if not lineStack:
            return
        if len(lineStack) < 2:
            log.error('invalid block near line %s in file %s'%(fileObj.line, filename))
            return
        word = lineStack[0]
        defi = '\n'.join(lineStack[1:])
        defi = defi.replace('<br/>', '\n') ## FIXME

        wordParts = [p.strip() for p in word.split('|')]
        word = wordParts[0]
        alts = wordParts[1:]

        glos.data.append((
            word,
            defi,
            {
                'alts': alts,
            },
        ))

    for line in fileObj:
        line = line.strip()
        if not line.startswith('###'):
            if line:
                lineStack.append(line)
            break
        parts = line[3:].split(':')
        if not parts:
            continue
        key = parts[0].lower()
        value = ' '.join(parts[1:]).strip()
        glos.setInfo(key, value)
    ## info lines finished

    for line in fileObj:
        line = line.strip()
        if line:
            lineStack.append(line)
        else:
            addDataEntry(lineStack)
            lineStack = []

    addDataEntry(lineStack)



def write(glos, filename):
    g = glos
    newline = '\n'
    head = newline.join([
        '###%s: %s'%(
            key.capitalize(),
            g.getInfo(key),
        )
        for key in infoKeys
    ])
    head += '\n'
    g.writeTxt(
        (newline, newline*2),
        filename=filename,
        writeInfo=False,
        rplList=(
            ('\n', '<br/>'),
        ),
        ext='.ldf',
        head=head,
    )






