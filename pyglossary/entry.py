# -*- coding: utf-8 -*-


class Entry(object):
    sep = '|'

    def join(self, parts):
        return self.sep.join([
            part.replace(self.sep, '\\'+self.sep)
            for part in parts
        ])

    @staticmethod
    def getEntrySortKey(key=None):
        if key:
            return lambda entry: key(entry.getWords()[0])
        else:
            return lambda entry: entry.getWords()[0]

    @staticmethod
    def getRawEntrySortKey(key=None):
        if key:
            return lambda x: key(
                x[0][0] if isinstance(x[0], (list, tuple)) else x[0]
            )
        else:
            return lambda x: \
                x[0][0] if isinstance(x[0], (list, tuple)) else x[0]

    def __init__(self, word, defi, defiFormat=None):
        """
            word: string or a list of strings (including alternate words)
            defi: string or a list of strings (including alternate definitions)
            defiFormat (optional): definition format:
                'm': plain text
                'h': html
                'x': xdxf
        """

        # memory optimization:
        if isinstance(word, list):
            if len(word) == 1:
                word = word[0]
        elif not isinstance(word, str):
            raise TypeError('invalid word type %s' % type(word))

        if isinstance(defi, list):
            if len(defi) == 1:
                defi = defi[0]
        elif not isinstance(defi, str):
            raise TypeError('invalid defi type %s' % type(defi))

        self._word = word
        self._defi = defi
        self._defiFormat = defiFormat

    def getWord(self):
        """
            returns string of word,
                and all the alternate words
                seperated by '|'
        """
        if isinstance(self._word, str):
            return self._word
        else:
            return self.join(self._word)

    def getWords(self):
        """
            returns list of the word and all the alternate words
        """
        if isinstance(self._word, str):
            return [self._word]
        else:
            return self._word

    def getDefi(self):
        """
            returns string of definition,
                and all the alternate definitions
                seperated by '|'
        """
        if isinstance(self._defi, str):
            return self._defi
        else:
            return self.join(self._defi)

    def getDefis(self):
        """
            returns list of the definition and all the alternate definitions
        """
        if isinstance(self._defi, str):
            return [self._defi]
        else:
            return self._defi

    def getDefiFormat(self):
        """
            returns definition format:
                'm': plain text
                'h': html
                'x': xdxf
        """
        return self._defiFormat

    def addAlt(self, alt):
        words = self.getWords()
        words.append(alt)
        self._word = words

    def editFuncWord(self, func):
        """
            run function `func` on all the words
            `func` must accept only one string as argument
            and return the modified string
        """
        if isinstance(self._word, str):
            self._word = func(self._word)
        else:
            self._word = tuple(
                func(st) for st in self._word
            )

    def editFuncDefi(self, func):
        """
            run function `func` on all the definitions
            `func` must accept only one string as argument
            and return the modified string
        """
        if isinstance(self._defi, str):
            self._defi = func(self._defi)
        else:
            self._defi = tuple(
                func(st) for st in self._defi
            )

    def strip(self):
        """
            strip whitespaces from all words and definitions
        """
        self.editFuncWord(str.strip)
        self.editFuncDefi(str.strip)

    def replaceInWord(self, source, target):
        """
            replace string `source` with `target` in all words
        """
        if isinstance(self._word, str):
            self._word = self._word.replace(source, target)
        else:
            self._word = tuple(
                st.replace(source, target) for st in self._word
            )

    def replaceInDefi(self, source, target):
        """
            replace string `source` with `target` in all definitions
        """
        if isinstance(self._defi, str):
            self._defi = self._defi.replace(source, target)
        else:
            self._defi = tuple(
                st.replace(source, target) for st in self._defi
            )

    def replace(self, source, target):
        """
            replace string `source` with `target` in all words and definitions
        """
        self.replaceInWord(source, target)
        self.replaceInDefi(source, target)

    def getRaw(self):
        """
            returns a tuple (word, defi) or (word, defi, defiFormat)
            where both word and defi might be string or list of strings
        """
        if self._defiFormat:
            return (
                self._word,
                self._defi,
                self._defiFormat,
            )
        else:
            return (
                self._word,
                self._defi,
            )

    @classmethod
    def fromRaw(cls, rawEntry, defaultDefiFormat=None):
        """
            rawEntry can be (word, defi) or (word, defi, defiFormat)
            where both word and defi can be string or list of strings
            if defiFormat is missing, defaultDefiFormat will be used

            creates and return an Entry object from `rawEntry` tuple
        """
        word = rawEntry[0]
        defi = rawEntry[1]
        try:
            defiFormat = rawEntry[2]
        except IndexError:
            defiFormat = defaultDefiFormat

        if isinstance(word, tuple):
            word = list(word)
        if isinstance(defi, tuple):
            defi = list(defi)

        return cls(
            word,
            defi,
            defiFormat=defiFormat,
        )
