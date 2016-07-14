# -*- coding: utf-8 -*-
import sys

import os
from os.path import (
    dirname,
    realpath,
)
import re
import gzip
from time import time as now
from collections import Counter

from pyglossary.text_utils import (
    intToBinStr,
    binStrToInt,
    runDictzip,
)

from formats_common import *

enable = True
format = 'Stardict'
description = 'StarDict (ifo)'
extentions = ['.ifo']
readOptions = []
writeOptions = [
    'dictzip',  # bool
]
sortOnWrite = ALWAYS
# sortKey also is defined in line 52
supportsAlternates = True

infoKeys = (
    'bookname',
    'author',
    'email',
    'website',
    'description',
    'date',
)


def sortKeyBytes(b_word):
    """
    b_word is a bytes instance
    """
    assert isinstance(b_word, bytes)
    return (
        b_word.lower(),
        b_word,
    )


def sortKey(word):
    """
    word is a str instance
    """
    assert isinstance(word, str)
    return sortKeyBytes(word.encode('utf-8'))


def newlinesToSpace(text):
    return re.sub('[\n\r]+', ' ', text)


def newlinesToBr(text):
    return re.sub('\n\r?|\r\n?', '<br>', text)


def verifySameTypeSequence(s):
    if not s:
        return True
    if not s.isalpha():
        log.error('Invalid sametypesequence option')
        return False
    return True


class Reader(object):
    def __init__(self, glos):
        self.glos = glos
        self.clear()
        """
        indexData format
        indexData[i] - i-th record in index file
        indexData[i][0] - b_word (bytes)
        indexData[i][1] - definition block offset in dict file
        indexData[i][2] - definition block size in dict file

        REMOVE:
        indexData[i][3] - list of definitions
        indexData[i][3][j][0] - definition data
        indexData[i][3][j][1] - definition type - 'h', 'm' or 'x'
        indexData[i][4] - list of synonyms (strings)

        synDict:
            a dict { wordIndex -> altList }
        """

    def close(self):
        if self._dictFile:
            self._dictFile.close()
        self.clear()

    def clear(self):
        self._dictFile = None
        self._filename = ''  # base file path, no extension
        self._indexData = []
        self._synDict = {}
        self._sametypesequence = ''
        self._resDir = ''
        self._resFileNames = []
        self._wordCount = None

    def open(self, filename):
        if splitext(filename)[1].lower() == '.ifo':
            self._filename = splitext(filename)[0]
        else:
            self._filename = filename
        self._filename = realpath(self._filename)
        self.readIfoFile()
        sametypesequence = self.glos.getInfo('sametypesequence')
        if not verifySameTypeSequence(sametypesequence):
            return False
        self._indexData = self.readIdxFile()
        self._wordCount = len(self._indexData)
        self._synDict = self.readSynFile()
        self._sametypesequence = sametypesequence
        if isfile(self._filename + '.dict.dz'):
            self._dictFile = gzip.open(self._filename+'.dict.dz', mode='rb')
        else:
            self._dictFile = open(self._filename+'.dict', mode='rb')
        self._resDir = join(dirname(self._filename), 'res')
        if isdir(self._resDir):
            self._resFileNames = os.listdir(self._resDir)
        else:
            self._resDir = ''
            self._resFileNames = []
        # self.readResources()

    def __len__(self):
        if self._wordCount is None:
            raise RuntimeError(
                'StarDict: len(reader) called while reader is not open'
            )
        return self._wordCount + len(self._resFileNames)

    def readIfoFile(self):
        """
        .ifo file is a text file in utf-8 encoding
        """
        with open(self._filename+'.ifo', 'r') as ifoFile:
            for line in ifoFile:
                line = line.strip()
                if not line:
                    continue
                if line == "StarDict's dict ifo file":
                    continue
                key, eq, value = line.partition('=')
                if not (key and value):
                    log.warning('Invalid ifo file line: %s' % line)
                    continue
                self.glos.setInfo(key, value)

    def readIdxFile(self):
        if isfile(self._filename+'.idx.gz'):
            with gzip.open(self._filename+'.idx.gz') as idxFile:
                idxBytes = idxFile.read()
        else:
            with open(self._filename+'.idx', 'rb') as idxFile:
                idxBytes = idxFile.read()

        indexData = []
        pos = 0
        while pos < len(idxBytes):
            beg = pos
            pos = idxBytes.find(b'\x00', beg)
            if pos < 0:
                log.error('Index file is corrupted')
                break
            b_word = idxBytes[beg:pos]
            pos += 1
            if pos + 8 > len(idxBytes):
                log.error('Index file is corrupted')
                break
            offset = binStrToInt(idxBytes[pos:pos+4])
            pos += 4
            size = binStrToInt(idxBytes[pos:pos+4])
            pos += 4
            indexData.append([b_word, offset, size])

        return indexData

    def __iter__(self):
        indexData = self._indexData
        synDict = self._synDict
        sametypesequence = self._sametypesequence
        dictFile = self._dictFile

        if not dictFile:
            log.error('%s is not open, can not iterate' % self)
            raise StopIteration

        if not indexData:
            log.warning('indexData is empty')
            raise StopIteration

        for wordIndex, (b_word, defiOffset, defiSize) in enumerate(indexData):
            if not b_word:
                continue

            dictFile.seek(defiOffset)
            if dictFile.tell() != defiOffset:
                log.error(
                    'Unable to read definition for word "%s"' % b_word
                )
                continue

            b_defiBlock = dictFile.read(defiSize)

            if len(b_defiBlock) != defiSize:
                log.error(
                    'Unable to read definition for word "%s"' % b_word
                )
                continue

            if sametypesequence:
                defisData = self.parseDefiBlockCompact(
                    b_defiBlock,
                    sametypesequence,
                )
            else:
                defisData = self.parseDefiBlockGeneral(b_defiBlock)

            if defisData is None:
                log.error('Data file is corrupted. Word "%s"' % b_word)
                continue

            # defisData is a list of (b_defi, defiFormatCode) tuples

            defis = []
            defiFormats = []
            for b_defi, defiFormatCode in defisData:
                defis.append(b_defi.decode('utf-8'))
                defiFormats.append(
                    {
                        'm': 'm',
                        't': 'm',
                        'y': 'm',
                        'g': 'h',
                        'h': 'h',
                        'x': 'x',
                    }.get(chr(defiFormatCode), '')
                )

            # FIXME
            defiFormat = defiFormats[0]
            # defiFormat = Counter(defiFormats).most_common(1)[0][0]

            if not defiFormat:
                log.warning(
                    'Definition format %s is not supported' % defiFormat
                )

            word = b_word.decode('utf-8')
            try:
                alts = synDict[wordIndex]
            except KeyError:  # synDict is dict
                pass
            else:
                word = [word] + alts
            if len(defis) == 1:
                defis = defis[0]

            yield Entry(
                word,
                defis,
                defiFormat=defiFormat,
            )

        if isdir(self._resDir):
            for fname in os.listdir(self._resDir):
                fpath = join(self._resDir, fname)
                with open(fpath, 'rb') as fromFile:
                    yield self._glos.newDataEntry(
                        fname,
                        fromFile.read(),
                    )

    def readSynFile(self):
        """
        return synDict, a dict { wordIndex -> altList }
        """
        if not isfile(self._filename+'.syn'):
            return {}
        with open(self._filename+'.syn', 'rb') as synFile:
            synBytes = synFile.read()
        synBytesLen = len(synBytes)
        synDict = {}
        pos = 0
        while pos < synBytesLen:
            beg = pos
            pos = synBytes.find(b'\x00', beg)
            if pos < 0:
                log.error('Synonym file is corrupted')
                break
            b_alt = synBytes[beg:pos]  # b_alt is bytes
            pos += 1
            if pos + 4 > len(synBytes):
                log.error('Synonym file is corrupted')
                break
            wordIndex = binStrToInt(synBytes[pos:pos+4])
            pos += 4
            if wordIndex >= self._wordCount:
                log.error(
                    'Corrupted synonym file. ' +
                    'Word "%s" references invalid item' % b_alt
                )
                continue

            s_alt = b_alt.decode('utf-8')  # s_alt is str
            try:
                synDict[wordIndex].append(s_alt)
            except KeyError:
                synDict[wordIndex] = [s_alt]

        return synDict

    def parseDefiBlockCompact(self, b_block, sametypesequence):
        """
        Parse definition block when sametypesequence option is specified.

        Return a list of (b_defi, defiFormatCode) tuples
            where b_defi is a bytes instance
            and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
        """
        assert isinstance(b_block, bytes)
        sametypesequence = sametypesequence.encode('utf-8')
        assert len(sametypesequence) > 0
        res = []
        i = 0
        for t in sametypesequence[:-1]:
            if i >= len(b_block):
                return None
            if bytes([t]).islower():
                beg = i
                i = b_block.find(b'\x00', beg)
                if i < 0:
                    return None
                res.append((b_block[beg:i], t))
                i += 1
            else:
                assert bytes([t]).isupper()
                if i + 4 > len(b_block):
                    return None
                size = binStrToInt(b_block[i:i+4])
                i += 4
                if i + size > len(b_block):
                    return None
                res.append((b_block[i:i+size], t))
                i += size

        if i >= len(b_block):
            return None
        t = sametypesequence[-1]
        if bytes([t]).islower():
            if 0 in b_block[i:]:
                return None
            res.append((b_block[i:], t))
        else:
            assert bytes([t]).isupper()
            res.append((b_block[i:], t))

        return res

    def parseDefiBlockGeneral(self, b_block):
        """
        Parse definition block when sametypesequence option is not specified.

        Return a list of (b_defi, defiFormatCode) tuples
            where b_defi is a bytes instance
            and defiFormatCode is int, so: defiFormat = chr(defiFormatCode)
        """
        res = []
        i = 0
        while i < len(b_block):
            t = b_block[i]
            if not bytes([t]).isalpha():
                return None
            i += 1
            if bytes([t]).islower():
                beg = i
                i = b_block.find(b'\x00', beg)
                if i < 0:
                    return None
                res.append((b_block[beg:i], t))
                i += 1
            else:
                assert bytes([t]).isupper()
                if i + 4 > len(b_block):
                    return None
                size = binStrToInt(b_block[i:i+4])
                i += 4
                if i + size > len(b_block):
                    return None
                res.append((b_block[i:i+size], t))
                i += size
        return res

    # def readResources(self):
    #    if not isdir(self._resDir):
    #        resInfoPath = join(baseDirPath, 'res.rifo')
    #        if isfile(resInfoPath):
    #            log.warning(
    #                'StarDict resource database is not supported. Skipping'
    #            )


class Writer(object):
    def __init__(self, glos):
        self.glos = glos

    def write(
        self,
        filename,
        dictzip=True,
    ):
        fileBasePath = ''
        ##
        if splitext(filename)[1].lower() == '.ifo':
            fileBasePath = splitext(filename)[0]
        elif filename.endswith(os.sep):
            if not isdir(filename):
                os.makedirs(filename)
            fileBasePath = join(filename, split(filename[:-1])[-1])
        elif isdir(filename):
            fileBasePath = join(filename, split(filename)[-1])
        ##
        if fileBasePath:
            fileBasePath = realpath(fileBasePath)
        self._filename = fileBasePath
        self._resDir = join(dirname(self._filename), 'res')

        self.writeGeneral()
#        if self.glossaryHasAdditionalDefinitions():
#            self.writeGeneral()
#        else:
#            defiFormat = self.detectMainDefinitionFormat()
#            if defiFormat == None:
#                self.writeGeneral()
#            else:
#                self.writeCompact(defiFormat)

        if dictzip:
            runDictzip(self._filename)

#    def writeCompact(self, defiFormat):
#        """
#        Build StarDict dictionary with sametypesequence option specified.
#        Every item definition consists of a single article.
#        All articles have the same format, specified in defiFormat parameter.
#
#        Parameters:
#        defiFormat - format of article definition: h - html, m - plain text
#        """
#        dictMark = 0
#        idxBytes = b''
#        dictStr = ''
#        altIndexList = [] # contains tuples (b'alternate', wordIndex)
#        for i, entry in enumerate(self.glos):
#            words = entry.getWords()
#            defi = entry.getDefi()
#            for alt in words[1:]:
#                altIndexList.append((alt.encode('utf-8'), i))
#            dictStr += defi
#            defiLen = len(defi)
#            idxBytes += words[0] + b'\x00' + intToBinStr(dictMark, 4) + \
#                intToBinStr(defiLen, 4)
#            dictMark += defiLen
#        wordCount = i + 1
#        with open(self._filename+'.dict', 'wb') as dictFile:
#            dictFile.write(dictStr)
#        with open(self._filename+'.idx', 'wb') as idxFile:
#            idxFile.write(idxBytes)
#        indexFileSize = len(idxBytes)
#        del idxBytes, dictStr
#
#        self.writeSynFile(altIndexList)
#        self.writeIfoFile(
#            wordCount,
#            indexFileSize,
#            len(altIndexList),
#            defiFormat,
#        )

    def writeGeneral(self):
        """
        Build StarDict dictionary in general case.
        Every item definition may consist of an arbitrary number of articles.
        sametypesequence option is not used.
        """
        dictMark = 0
        altIndexList = []  # list of tuples (b'alternate', wordIndex)

        dictFile = open(self._filename+'.dict', 'wb')
        idxFile = open(self._filename+'.idx', 'wb')
        indexFileSize = 0

        t0 = now()
        wordCount = 0
        defiFormatCounter = Counter()
        if not isdir(self._resDir):
            os.mkdir(self._resDir)
        for entryI, entry in enumerate(self.glos):
            if entry.isData():
                entry.save(self._resDir)
                continue
            words = entry.getWords()  # list of strs
            word = words[0]  # str
            defis = entry.getDefis()  # list of strs

            entry.detectDefiFormat()  # call no more than once
            defiFormat = entry.getDefiFormat()
            defiFormatCounter[defiFormat] += 1
            if defiFormat not in ('m', 'h'):
                defiFormat = 'm'
            assert isinstance(defiFormat, str) and len(defiFormat) == 1

            b_dictBlock = b''

            for alt in words[1:]:
                altIndexList.append((alt.encode('utf-8'), entryI))

            b_dictBlock += (defiFormat + defis[0]).encode('utf-8') + b'\x00'

            for altDefi in defis[1:]:
                b_dictBlock += (defiFormat + altDefi).encode('utf-8') + b'\x00'

            dictFile.write(b_dictBlock)

            blockLen = len(b_dictBlock)
            b_idxBlock = word.encode('utf-8') + b'\x00' + \
                intToBinStr(dictMark, 4) + \
                intToBinStr(blockLen, 4)
            idxFile.write(b_idxBlock)

            dictMark += blockLen
            indexFileSize += len(b_idxBlock)

            wordCount += 1

        dictFile.close()
        idxFile.close()
        if not os.listdir(self._resDir):
            os.rmdir(self._resDir)
        log.info('Writing dict file took %.2f seconds' % (now() - t0))
        log.pretty(defiFormatCounter.most_common(), 'defiFormatsCount: ')

        self.writeSynFile(altIndexList)
        self.writeIfoFile(wordCount, indexFileSize, len(altIndexList))

    def writeSynFile(self, altIndexList):
        """
        Build .syn file
        """
        if not altIndexList:
            return

        log.info('Sorting %s synonyms...' % len(altIndexList))
        t0 = now()

        altIndexList.sort(
            key=lambda x: sortKeyBytes(x[0])
        )
        # 28 seconds with old sort key (converted from custom cmp)
        # 0.63 seconds with my new sort key
        # 0.20 seconds without key function (default sort)

        log.info('Sorting %s synonyms took %.2f seconds' % (
            len(altIndexList),
            now() - t0,
        ))
        log.info('Writing %s synonyms...' % len(altIndexList))
        t0 = now()
        with open(self._filename+'.syn', 'wb') as synFile:
            synFile.write(b''.join([
                b_alt + b'\x00' + intToBinStr(wordIndex, 4)
                for b_alt, wordIndex in altIndexList
            ]))
        log.info('Writing %s synonyms took %.2f seconds' % (
            len(altIndexList),
            now() - t0,
        ))

    def writeIfoFile(
        self,
        wordCount,
        indexFileSize,
        synwordcount,
        sametypesequence=None,
    ):
        """
        Build .ifo file
        """
        ifoStr = "StarDict's dict ifo file\n" \
            + 'version=3.0.0\n' \
            + 'bookname=%s\n' % newlinesToSpace(self.glos.getInfo('name')) \
            + 'wordcount=%s\n' % wordCount \
            + 'idxfilesize=%s\n' % indexFileSize
        if sametypesequence is not None:
            ifoStr += 'sametypesequence=%s\n' % sametypesequence
        if synwordcount > 0:
            ifoStr += 'synwordcount=%s\n' % synwordcount
        for key in infoKeys:
            if key in (
                'bookname',
                'wordcount',
                'idxfilesize',
                'sametypesequence',
            ):
                continue
            value = self.glos.getInfo(key)
            if value == '':
                continue
            if key == 'description':
                value = newlinesToBr(value)
            else:
                value = newlinesToSpace(value)

            ifoStr += '%s=%s\n' % (key, value)

        with open(self._filename+'.ifo', 'w', encoding='utf-8') as ifoFile:
            ifoFile.write(ifoStr)

    def glossaryHasAdditionalDefinitions(self):
        """
        Search for additional definitions in the glossary.
        We need to know if the glossary contains additional definitions
        to make the decision on the format of the StarDict dictionary.
        """
        for entry in self.glos:
            if len(entry.getDefis()) > 1:
                return True
        return False

    def detectMainDefinitionFormat(self):
        """
        Scan main definitions of the glossary.
        Return format common to all definitions: 'h' or 'm'

        If definitions has different formats return None.
        """
        self.glos.setDefaultDefiFormat('m')
        formatsCount = self.glos.getMostUsedDefiFormats()
        if not formatsCount:
            return None
        if len(formatsCount) > 1:  # FIXME
            return None

        return formatsCount[0]


def write(glos, filename, **kwargs):
    writer = Writer(glos)
    writer.write(filename, **kwargs)
