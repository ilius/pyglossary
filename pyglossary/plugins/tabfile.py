# -*- coding: utf-8 -*-

from formats_common import *
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import escapeNTB, unescapeNTB, splitByBarUnescapeNTB

enable = True
format = 'Tabfile'
description = 'Tabfile (txt, dic)'
extentions = ['.txt', '.tab', '.dic']
readOptions = [
    'encoding',
]
writeOptions = [
    'encoding',  # str
    'writeInfo',  # bool
    'resources',  # bool
]


class Reader(TextGlossaryReader):
    def isInfoWord(self, word):
        if isinstance(word, str):
            return word.startswith('#')
        else:
            return False

    def fixInfoWord(self, word):
        if isinstance(word, str):
            return word.lstrip('#')
        else:
            return word

    def nextPair(self):
        if not self._file:
            raise StopIteration
        line = self._file.readline()
        if not line:
            raise StopIteration
        line = line.strip()  # This also removes tailing newline
        if not line:
            return
        ###
        word, tab, defi = line.partition('\t')
        if not tab:
            log.error(
                'Warning: line starting with "%s" has no tab!' % line[:10]
            )
            return
        ###
        if self._glos.getPref('enable_alts', True):
            word = splitByBarUnescapeNTB(word)
            if len(word) == 1:
                word = word[0]
        else:
            word = unescapeNTB(word, bar=True)
        ###
        defi = unescapeNTB(defi)
        ###
        return word, defi


def write(
    glos,
    filename,
    encoding='utf-8',
    writeInfo=True,
    resources=True,
):
    return glos.writeTabfile(
        filename,
        encoding=encoding,
        writeInfo=writeInfo,
        resources=resources,
    )
