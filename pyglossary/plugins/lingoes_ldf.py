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
    entryLines = []

    def addDataEntry(entryLines):
        if not entryLines:
            return
        if len(entryLines) < 2:
            log.error(
                'invalid block near line %s' % fileObj.line +
                ' in file %s' % filename
            )
            return
        word = entryLines[0]
        defi = '\n'.join(entryLines[1:])
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
                entryLines.append(line)
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
            entryLines.append(line)
        else:
            addDataEntry(entryLines)
            entryLines = []

    addDataEntry(entryLines)


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
