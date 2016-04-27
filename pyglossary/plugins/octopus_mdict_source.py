# -*- coding: utf-8 -*-
## http://www.octopus-studio.com/download.en.htm

from formats_common import *

enable = True
format = 'OctopusMdictSource'
description = 'Octopus MDict Source'
extentions = ['.mtxt']
readOptions = []
writeOptions = []

def read(glos, filename):
    with open(filename) as fp:
        text = fp.read()
    text = text.replace('\r\n', '\n')
    text = text.replace('entry://', 'bword://')
    for section in text.split('</>'):
        lines = section.strip().split('\n')
        if len(lines) < 2:
            continue
        word = lines[0]
        defi = '\n'.join(lines[1:])
        glos.addEntry(
            word,
            defi,
        )

def writeEntryGen(glos):
    for entry in glos:
        words = entry.getWords()
        defis = entry.getDefis()

        yield Entry(words[0], defis)

        for alt in words[1:]:
            yield Entry(
                alt,
                '@@@LINK=%s'%words[0],
            )


def write(glos, filename):
    glos.writeTxt(
        ('\r\n', '\r\n</>\r\n'),
        filename=filename,
        writeInfo=False,
        rplList=[
            ('bword://', 'entry://'),
        ],
        ext='.mtxt',
        head='',
        iterEntries=writeEntryGen(glos),
    )


