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

from pyglossary.text_reader import TextGlossaryReader


class Reader(TextGlossaryReader):
    def isInfoWord(self, word):
        return word.startswith('#')

    def fixInfoWord(self, word):
        return word.lstrip('#')

    def nextPair(self):
        if not self._fp:
            raise StopIteration
        line = self._fp.readline()
        if not line:
            raise StopIteration
        line = line.strip()## This also removed tailing newline
        if not line:
            return
        ###
        fti = line.find('\t') # first tab's index
        if fti==-1:
            log.error('Warning: line starting with "%s" has no tab!'%line[:10])
            return
        word = line[:fti]
        defi = line[fti+1:]#.replace('\\n', '\n')#.replace('<BR>', '\n').replace('\\t', '\t')
        ###
        if self._glos.getPref('enable_alts', True):
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
        ###
        return word, defi



def write(glos, filename, writeInfo=True):
    return glos.writeTabfile(
        filename,
        writeInfo=writeInfo,
    )


