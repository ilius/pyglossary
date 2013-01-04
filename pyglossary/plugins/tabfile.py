# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Tabfile'
description = 'Tabfile (txt, dic)'
extentions = ['.txt', '.tab', '.dic']
readOptions = []
writeOptions = [
    'writeInfo',
]

def read(glos, filename):
    fp = open(filename)
    glos.data = []
    while True:
        line = fp.readline()
        if not line:
            break
        line = line.strip()## This also removed tailing newline
        fti = line.find('\t') # first tab's index
        if fti==-1:
            printAsError('Warning: line beganing "%s" has no tab!' %line[:10])
            continue
        word = line[:fti]
        defi = line[fti+1:]#.replace('\\n', '\n')#.replace('<BR>', '\n').replace('\\t', '\t')
        ###
        if glos.getPref('enable_alts', True):
            wordParts = [p.strip() for p in word.split('|')]
            word = wordParts[0]
            alts = wordParts[1:]
            del wordParts
        else:
            alts = []
        ###
        for i in xrange(128):
            c = chr(i)
            if not c in defi:
                defi = defi.replace('\\\\n', c)\
                            .replace('\\n', '\n')\
                            .replace(c, '\\n')\
                            .replace('\\\\t', c)\
                            .replace('\\t', '\t')\
                            .replace(c, '\\t')
                break
        if len(word)>0:
            if word.startswith('#'):
                while word[0]=='#':
                    word=word[1:]
                    if len(word)==0:
                        break
                glos.setInfo(word, defi)
                continue
        glos.data.append((
            word,
            defi,
            {'alts': alts},
        ))


def write(glos, filename, writeInfo=True):
    return glos.writeTxt(
        sep=('\t', '\n'),
        filename=filename,
        writeInfo=writeInfo,
        rplList=(
            ('\\', '\\\\'),
            ('\n', '\\n'),
            ('\t', '\\t'),
        ),
        ext='.txt',
    )


