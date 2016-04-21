# -*- coding: utf-8 -*-

import string
import re

from .text_utils import (
    fixUtf8,
    faEditStr,
)

class EntryFilter(object):
    name = ''
    desc = ''
    def __init__(self, glos):
        self.glos = glos
    def run(self, entry):
        """
            returns an Entry object, or None to skip
                may return the same `entry`,
                or modify and return it,
                or return a new Entry object
        """
        return entry

class StripEntryFilter(EntryFilter):
    name = 'strip'
    desc = 'Strip Whitespaces'
    def run(self, entry):
        entry.strip()
        entry.replace('\r', '')
        return entry


class NonEmptyWordFilter(EntryFilter):
    name = 'non_empty_word'
    desc = 'Non-empty Words'
    def run(self, entry):
        if not entry.getWord():
            return
        #words = entry.getWords()
        #if not words:
        #    return
        #wordsStr = ''.join([w.strip() for w in words])
        #if not wordsStr:
        #    return
        return entry

class NonEmptyDefiFilter(EntryFilter):
    name = 'non_empty_defi'
    desc = 'Non-empty Definition'
    def run(self, entry):
        if not entry.getDefi():
            return
        return entry

class FixUnicodeFilter(EntryFilter):
    name = 'fix_unicode'
    desc = 'Fix Unicode'
    def run(self, entry):
        entry.editFuncWord(fixUtf8)
        entry.editFuncDefi(fixUtf8)
        return entry

class LowerWordFilter(EntryFilter):
    name = 'lower_word'
    desc = 'Lowercase Words'
    def run(self, entry):
        entry.editFuncWord(string.lower)
        return entry


class LangEntryFilter(EntryFilter):
    name = 'lang'
    desc = 'Language-dependent Filters'
    def run_fa(self, entry):
        entry.editFuncWord(faEditStr)
        entry.editFuncDefi(faEditStr)
        #RLM = '\xe2\x80\x8f'
        ## defi = '\n'.join([RLM+line for line in defi.split('\n')]) ## for GoldenDict
        return entry
    def run(self, entry):
        langs = (self.glos.getInfo('sourceLang') + self.glos.getInfo('targetLang')).lower()
        if 'persian' in langs or 'farsi' in langs:
            entry = self.run_fa(entry)

        return entry

'''
class MarkupConvertFilter(EntryFilter):
    def removeTags(self, tags):
        n = len(self._data)
        for i in xrange(n):
            self._data[i] = (
                self._data[i][0],
                removeTextTags(self._data[i][1], tags),
            ) + self._data[i][2:]

    def run(self, entry):
        p = self.glos.ui.pref
        if p['remove_tags']:
            self.removeTags(p['tags'])
'''

class CleanEntryFilter(EntryFilter):## FIXME
    name = 'clean'
    desc = 'Clean'
    def cleanDefi(self, st):
        st = st.replace('♦  ', '♦ ')
        st = re.sub('[\r\n]+', '\n', st)
        st = re.sub(' *\n *', '\n', st)

        """
        This code may correct snippets like:
        - First sentence .Second sentence. -> First sentence. Second sentence.
        - First clause ,second clause. -> First clause, second clause.
        But there are cases when this code have undesirable effects
        ( '<' represented as '&lt;' in HTML markup):
        - <Adj.> -> < Adj. >
        - <fig.> -> < fig. >
        """
        """
        for j in range(3):
            for ch in ',.;':
                st = replacePostSpaceChar(st, ch)
        """

        st = re.sub('♦\n+♦', '♦', st)
        if st.endswith('<p'):
            st = st[:-2]
        st = st.strip()
        if st.endswith(','):
            st = st[:-1]
        
        return st

    def run(self, entry):
        entry.editFuncDefi(self.cleanDefi)
        return entry

