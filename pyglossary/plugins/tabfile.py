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
from pyglossary.text_utils import escapeNTB, unescapeNTB, splitByBarUnescapeNTB


class Reader(TextGlossaryReader):
    def isInfoWord(self, word):
        return word.startswith('#')

    def fixInfoWord(self, word):
        return word.lstrip('#')

    def nextPair(self):
        if not self._file:
            raise StopIteration
        line = self._file.readline()
        if not line:
            raise StopIteration
        line = line.strip()## This also removed tailing newline
        if not line:
            return
        ###
        word, tab, defi = line.partition('\t')
        if not tab:
            log.error('Warning: line starting with "%s" has no tab!'%line[:10])
            return
        ###
        if self._glos.getPref('enable_alts', True):
            word = splitByBarUnescapeNTB(word)
            if len(word)==1:
                word = word[0]
        else:
            word = unescapeNTB(word, bar=True)
        ###
        defi = unescapeNTB(defi)
        ###
        return word, defi



def write(glos, filename, writeInfo=True):
    return glos.writeTabfile(
        filename,
        writeInfo=writeInfo,
    )


