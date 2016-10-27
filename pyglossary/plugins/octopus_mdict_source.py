# -*- coding: utf-8 -*-
# http://www.octopus-studio.com/download.en.htm

from formats_common import *

enable = True
format = 'OctopusMdictSource'
description = 'Octopus MDict Source'
extentions = ['.mtxt']
readOptions = [
    'encoding',  # str
]
writeOptions = [
    'resources',  # bool
]


def read(
    glos,
    filename,
    encoding='utf-8',
):
    with open(filename, encoding=encoding) as fp:
        text = fp.read()
    text = text.replace('\r\n', '\n')
    text = text.replace('entry://', 'bword://')
    lastEntry = None
    for section in text.split('</>'):
        lines = section.strip().split('\n')
        if len(lines) < 2:
            continue
        word = lines[0]
        defi = '\n'.join(lines[1:])

        if defi.startswith('@@@LINK='):
            if not lastEntry:
                log.error('alternate section not after a word: %s' % defi)
                continue
            mainWord = defi.partition('=')[2]
            if lastEntry.getWords()[0] != mainWord:
                log.error('alternate is not ride after word: %s' % defi)
                continue
            lastEntry.addAlt(word)
            continue

        # now that we know there are no more alternate forms of lastEntry
        if lastEntry:
            glos.addEntryObj(lastEntry)
        entry = glos.newEntry(word, defi)
        lastEntry = entry

    if lastEntry:
        glos.addEntryObj(lastEntry)


def writeEntryGen(glos):
    for entry in glos:
        words = entry.getWords()
        defis = entry.getDefis()

        yield glos.newEntry(words[0], defis)

        for alt in words[1:]:
            yield glos.newEntry(
                alt,
                '@@@LINK=%s' % words[0],
            )


def write(
    glos,
    filename,
    resources=True,
):
    glos.writeTxt(
        '\n',
        '\n</>\n',
        filename=filename,
        writeInfo=False,
        rplList=[
            ('bword://', 'entry://'),
        ],
        ext='.mtxt',
        head='',
        iterEntries=writeEntryGen(glos),
        newline='\r\n',
        resources=resources,
    )
