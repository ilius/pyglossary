# -*- coding: utf-8 -*-
## edlin.py
##
## Copyright © 2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
## This file is part of PyGlossary project, http://github.com/ilius/pyglossary
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
## If not, see <http://www.gnu.org/licenses/gpl.txt>.


from formats_common import *

enable = True
format = 'Edlin'
description = 'Editable Linked Entries'
extentions = ['.edlin']
readOptions = []
writeOptions = [
    'encoding',
]

from os.path import join, exists, isdir, isfile
from collections import OrderedDict as odict
from hashlib import sha1

from pyglossary.json_utils import dataToPrettyJson, jsonToOrderedData
from pyglossary.text_utils import escapeNTB, unescapeNTB, splitByBarUnescapeNTB


def makeDir(direc):
    if not isdir(direc):
        os.makedirs(direc)



class Reader(object):
    def __init__(self, glos):
        self._glos = glos
        self._clear()
    def close(self):
        self._clear()
    def _clear(self):
        self._filename = ''
        self._encoding = 'utf-8'
        self._len = None
        self._pos = -1
        self._rootPath = None
        self._nextPath = None
    def open(self, filename, encoding='utf-8'):
        if isdir(filename):
            infoFname = join(filename, 'info.json')
        elif isfile(filename):
            infoFname = filename
            filename = dirname(filename)
        else:
            raise ValueError('error while opening "%s": no such file or directory'%filename)
        self._filename = filename
        self._encoding = encoding
        
        with open(infoFname, 'r', encoding=encoding) as infoFp:
            infoJson = infoFp.read()
            info = jsonToOrderedData(infoJson)
            self._len = info.pop('wordCount')
            self._nextPath = self._rootPath = info.pop('root')
            for key, value in info.items():
                self._glos.setInfo(key, value)

    def __len__(self):
        if self._len is None:
            log.error('called len() on a reader which is not open')
            return 0
        return self._len

    __iter__ = lambda self: self
    def __next__(self):
        if not self._nextPath:
            log.error('iterating over a reader which is not open')
            raise StopIteration
        if self._nextPath == 'END':
            if self._pos != self._len:
                log.warning('%s words found, wordCount in info.json was %s'%(self._pos, self._len))
                self._len = self._pos
            raise StopIteration
        ###
        self._pos += 1
        ###
        with open(join(self._filename, self._nextPath), 'r', encoding=self._encoding) as fp:
            self._nextPath = fp.readline().rstrip()
            word = fp.readline().rstrip()
            defi = fp.read().rstrip()
        ###
        if self._glos.getPref('enable_alts', True):
            word = splitByBarUnescapeNTB(word)
            if len(word)==1:
                word = word[0]
        else:
            word = unescapeNTB(word, bar=True)
        ###
        #defi = unescapeNTB(defi)
        ###
        return Entry(word, defi)




class Writer(object):
    def __init__(self, glos):
        self._glos = glos
        self._clear()
    def close(self):
        self._clear()
    def _clear(self):
        self._filename = ''
        self._encoding = 'utf-8'
        self._hashSet = set()
        #self._len = None
        #self._pos = -1
    def open(self, filename, encoding='utf-8'):
        if exists(filename):
            raise ValueError('directory "%s" already exists'%filename)
        self._filename = filename
        self._encoding = encoding

    hashToPath = lambda self, h: h[:2] + '/' + h[2:]
    def getEntryHash(self, entry):
        """
            return hash string for given entry
            don't call it twice for one entry, if you do you will get a different hash string
        """
        _hash = sha1(toBytes(entry.getWord())).hexdigest()[:8]
        if not _hash in self._hashSet:
            self._hashSet.add(_hash)
            return _hash
        index = 0
        while True:
            tmp_hash = _hash + hex(index)[2:]
            if not tmp_hash in self._hashSet:
                self._hashSet.add(tmp_hash)
                return tmp_hash
            index += 1
    def saveEntry(self, thisEntry, thisHash, nextHash):
        dpath = join(self._filename, thisHash[:2])
        makeDir(dpath)
        with open(join(dpath, thisHash[2:]), 'w', encoding=self._encoding) as fp:
            fp.write('\n'.join([
                self.hashToPath(nextHash) if nextHash else 'END',
                thisEntry.getWord(),
                thisEntry.getDefi(),
            ]))

    def write(self):
        glosIter = iter(self._glos)
        try:
            thisEntry = next(glosIter)
        except StopIteration:
            raise ValueError('glossary is empty')

        os.makedirs(self._filename)
        count = 1
        rootHash = thisHash = self.getEntryHash(thisEntry)
        for nextEntry in glosIter:
            nextHash = self.getEntryHash(nextEntry)
            self.saveEntry(thisEntry, thisHash, nextHash)
            thisEntry = nextEntry
            thisHash = nextHash
            count += 1
        self.saveEntry(thisEntry, thisHash, None)
        
        with open(join(self._filename, 'info.json'), 'w', encoding=self._encoding) as fp:
            info = odict()
            info['name'] = self._glos.getInfo('name')
            info['root'] = self.hashToPath(rootHash)
            info['wordCount'] = count
            #info['modified'] =

            origInfo = self._glos.info.copy()
            for key in ('name', 'root', 'wordCount'):
                try:
                    del origInfo[key]
                except KeyError:
                    pass
            info.update(origInfo)

            fp.write(dataToPrettyJson(info))



def write(glos, filename, encoding='utf-8'):
    writer = Writer(glos)
    writer.open(
        filename,
        encoding=encoding,
    )
    writer.write()
    writer.close()







