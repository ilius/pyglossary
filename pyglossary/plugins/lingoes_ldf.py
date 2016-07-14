# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'LingoesLDF'
description = 'Lingoes Source (LDF)'
extentions = ['.ldf']
readOptions = []
writeOptions = [
    'newline',  # str, or choice ('\r\n', '\n', or '\r')
    'resources',  # bool
]

infoKeys = [
    'title',
    'description',
    'author',
    'email',
    'website',
    'copyright',
]


def read(glos, filename):
    glos.setDefaultDefiFormat('h')
    fileObj = FileLineWrapper(open(filename))
    lineStack = []

    def addDataEntry(lineStack):
        if not lineStack:
            return
        if len(lineStack) < 2:
            log.error(
                'invalid block near line %s' % fileObj.line +
                ' in file %s' % filename
            )
            return
        word = lineStack[0]
        defi = '\n'.join(lineStack[1:])
        defi = defi.replace('<br/>', '\n')  # FIXME

        word = [p.strip() for p in word.split('|')]

        glos.addEntry(
            word,
            defi,
        )

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
    # info lines finished

    for line in fileObj:
        line = line.strip()
        if line:
            lineStack.append(line)
        else:
            addDataEntry(lineStack)
            lineStack = []

    addDataEntry(lineStack)


def write(
    glos,
    filename,
    newline='\n',
    resources=True,
):
    g = glos
    head = '\n'.join([
        '###%s: %s' % (
            key.capitalize(),
            g.getInfo(key),
        )
        for key in infoKeys
    ])
    head += '\n'
    g.writeTxt(
        '\n',
        '\n\n',
        filename=filename,
        writeInfo=False,
        rplList=(
            ('\n', '<br/>'),
        ),
        ext='.ldf',
        head=head,
        newline=newline,
        resources=resources,
    )
