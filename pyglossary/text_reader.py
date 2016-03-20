from pyglossary.file_utils import fileCountLines
from pyglossary.entry import Entry

class TextGlossaryReader(object):
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
            self.loadInfo()
    def close(self):
        if not self._fp:
            return
        try:
            self._fp.close()
        except:
            log.exception('error while closing file "%s"'%self._filename)
        self._fp = None
    def loadInfo(self):
        self._pendingEntries = []
        self._leadingLinesCount = 0
        try:
            while True:
                wordDefi = self.nextPair()
                if not wordDefi:
                    continue
                word, defi = wordDefi
                if not self.isInfoWord(word):
                    self._pendingEntries.append(Entry(word, defi))
                    break
                self._leadingLinesCount += 1
                word = self.fixInfoWord(word)
                if not word:
                    continue
                self._glos.setInfo(word, defi)
        except StopIteration:
            pass
    def next(self):
        try:
            return self._pendingEntries.pop(0)
        except IndexError:
            pass
        ###
        wordDefi = self.nextPair()
        if not wordDefi:
            return
        word, defi = wordDefi
        ###
        return Entry(word, defi)
    def __len__(self):
        if self._len is None:
            log.warn('Try not to use len(reader) as it takes extra time')
            self._len = fileCountLines(self._filename) - self._leadingLinesCount
        return self._len
    __iter__ = lambda self: self

    def isInfoWord(self, word):
        raise NotImplementedError

    def fixInfoWord(self, word):
        raise NotImplementedError

    def nextPair(self):
        raise NotImplementedError





