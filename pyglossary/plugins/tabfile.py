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

from pyglossary.file_utils import fileCountLines

class Reader(object):
    def __init__(self, glos, hasInfo=True):
        self._glos = glos
        self._filename = ''
        self._fp = None
        self._hasInfo = True
        self._leadingLinesCount = 0
        self._pendingEntries = []
        self._len = None
    def open(self, filename):
        self._filename = filename
        self._fp = open(filename)
        if self._hasInfo:
            self._loadInfo()
    def close(self):
        if not self._fp:
            return
        try:
            self._fp.close()
        except:
            log.exception('error while closing tabfile')
        self._fp = None
    def __len__(self):
        if self._len is None:
            log.warn('Try not to use len(reader) as it takes extra time')
            self._len = fileCountLines(self._filename) - self._leadingLinesCount
        return self._len
    __iter__ = lambda self: self
    def next(self):
        try:
            return self._pendingEntries.pop(0)
        except IndexError:
            pass
        ###
        wordDefi = self._nextWordDefi()
        if not wordDefi:
            return
        word, defi = wordDefi
        ###
        return Entry(word, defi)

    def _loadInfo(self):
        self._pendingEntries = []
        self._leadingLinesCount = 0
        try:
            while True:
                wordDefi = self._nextWordDefi()
                if not wordDefi:
                    continue
                word, defi = wordDefi
                if not word.startswith('#'):
                    self._pendingEntries.append(Entry(word, defi))
                    break
                self._leadingLinesCount += 1
                word = word.lstrip('#')
                if not word:
                    continue
                self._glos.setInfo(word, defi)
        except StopIteration:
            pass
    def _nextWordDefi(self):
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


