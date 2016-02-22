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
    while True:
        line = fp.readline()
        if not line:
            break
        line = line.strip()## This also removed tailing newline
        fti = line.find('\t') # first tab's index
        if fti==-1:
            log.error('Warning: line starting with "%s" has no tab!'%line[:10])
            continue
        word = line[:fti]
        defi = line[fti+1:]#.replace('\\n', '\n')#.replace('<BR>', '\n').replace('\\t', '\t')
        ###
        if glos.getPref('enable_alts', True):
            word = word.split('|')
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
        glos.addEntry(
            word,
            defi,
        )


def write(glos, filename, writeInfo=True):
    return glos.writeTabfile(
        filename,
        writeInfo=writeInfo,
    )


