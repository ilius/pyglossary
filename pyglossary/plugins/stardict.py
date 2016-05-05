# -*- coding: utf-8 -*-
from formats_common import *

enable = True
format = 'Stardict'
description = 'StarDict (ifo)'
extentions = ['.ifo']
readOptions = []
writeOptions = [
    'resOverwrite',
]
supportsAlternates = True

import sys
sys.path.append('/usr/share/pyglossary/src')

import os
import os.path
from os.path import join, split, splitext, isfile, isdir
import re
from functools import cmp_to_key

from pyglossary.text_utils import intToBinStr, binStrToInt, runDictzip

infoKeys = ('bookname', 'author', 'email', 'website', 'description', 'date')


def isAsciiAlpha(c):
    """ c is int """
    return (c >= ord('A') and c <= ord('Z')) or (c >= ord('a') and c <= ord('z'))

def isAsciiLower(c):
    return c >= ord('a') and c <= ord('z')

def isAsciiUpper(c):
    """
        c is int
        imitate ISUPPER macro of glib library gstrfuncs.c file
    """
    return c >= ord('A') and c <= ord('Z')

def asciiLower(c):
    """
        c is int
        returns int (ascii character code)
        
        imitate TOLOWER macro of glib library gstrfuncs.c file

        This function converts upper case Latin letters to corresponding lower case letters,
        other chars are not changed.

        c must be non-Unicode string of length 1.
        You may apply this function to individual bytes of non-Unicode string.
        The following encodings are allowed: single byte encoding like koi8-r, cp1250, cp1251, cp1252, etc,
        and utf-8 encoding.

        Attention! Python Standard Library provides str.lower() method.
        It is not a correct replacement for this function.
        For non-unicode string str.lower() is locale dependent, it not only converts Latin
        letters to lower case, but also locale specific letters will be converted.
    """
    if isAsciiUpper(c):
        return c - ord('A') + ord('a')
    else:
        return c

def stardictStrKeyMy(ba):
    """
        ba is a bytes instance
    """
    assert isinstance(ba, bytes)
    return ba.lower() + ba

def asciiStrCaseCmp(ba1, ba2):
    """
        ba1 and ba2 are instances of bytes
        imitate g_ascii_strcasecmp function of glib library gstrfuncs.c file
    """
    commonLen = min(len(ba1), len(ba2))
    for i in range(commonLen):
        c1 = asciiLower(ba1[i])
        c2 = asciiLower(ba2[i])
        if c1 != c2:
            return c1 - c2
    return len(ba1) - len(ba2)

def strCmp(ba1, ba2):
    """
        ba1 and ba2 are instances of bytes
        imitate strcmp of standard C library

        Attention! You may have a temptation to replace this function with built-in cmp() function.
        Hold on! Most probably these two function behave identically now, but cmp does not
        document how it compares strings. There is no guaranty it will not be changed in future.
        Since we need predictable sorting order in StarDict dictionary, we need to preserve
        this function despite the fact there are other ways to implement it.
    """
    commonLen = min(len(ba1), len(ba2))
    for i in range(commonLen):
        c1 = ba1[i]
        c2 = ba2[i]
        if c1 != c2:
            return c1 - c2
    return len(ba1) - len(ba2)

def stardictStrCmp(s1, s2):
    """
        use this function to sort index items in StarDict dictionary
        s1 and s2 must be utf-8 encoded strings
    """
    s1 = toBytes(s1)
    s2 = toBytes(s2)
    a = asciiStrCaseCmp(s1, s2)
    if a == 0:
        return strCmp(s1, s2)
    else:
        return a

def stardictStrCmpMy(s1, s2):
    """
        For testing key function stardictStrKey
        and making sure it's exactly the same as stardictStrCmp
        
        s1 and s2 must be utf-8 encoded strings
    """
    s1 = toBytes(s1)
    s2 = toBytes(s2)
    return cmp(
        stardictStrKeyMy(s1),
        stardictStrKeyMy(s2),
    )

## using my key function `stardictStrKeyMy` might not be safe
## the safest way in Python 3 is using functools.cmp_to_key
stardictStrKey = cmp_to_key(stardictStrCmp)



def newlinesToSpace(text):
    return re.sub('[\n\r]+', ' ', text)

def newlinesToBr(text):
    return re.sub('\n\r?|\r\n?', '<br>', text)



class StarDictReader(object):
    def __init__(self, glos, filename):
        self.glos = glos
        if splitext(filename)[1].lower() == '.ifo':
            self.fileBasePath = splitext(filename)[0]
        else:
            self.fileBasePath = filename
        self.fileBasePath = os.path.realpath(self.fileBasePath)

    def run(self):
        self.readIfoFile()
        sametypesequence = self.glos.getInfo('sametypesequence')
        if not verifySameTypeSequence(sametypesequence):
            return
        """
            indexData format
            indexData[i] - i-th record in index file
            indexData[i][0] - word (string)
            indexData[i][1] - definition block offset in dict file
            indexData[i][2] - definition block size in dict file
            
            REMOVE:
            indexData[i][3] - list of definitions
            indexData[i][3][j][0] - definition data
            indexData[i][3][j][1] - definition type - 'h', 'm' or 'x'
            indexData[i][4] - list of synonyms (strings)
        """
        indexData = self.readIdxFile()
        synData = self.readSynFile(len(indexData))
        self.readDictFile(indexData, synData, sametypesequence)

        self.readResources()

    def readIfoFile(self):
        """
            .ifo file is a text file in utf-8 encoding
        """
        with open(self.fileBasePath+'.ifo', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line == "StarDict's dict ifo file":
                    continue
                key, eq, value = line.partition('=')
                if not (key and value):
                    log.warning('Invalid ifo file line: {0}'.format(line))
                    continue
                self.glos.setInfo(key, value)

    def readIdxFile(self):
        if isfile(self.fileBasePath+'.idx.gz'):
            import gzip
            with gzip.open(self.fileBasePath+'.idx.gz') as f:
                idxStr = f.read()
        else:
            with open(self.fileBasePath+'.idx', 'rb') as f:
                idxStr = f.read()
        indexData = []
        i = 0
        while i < len(idxStr):
            beg = i
            i = idxStr.find(b'\x00', beg)
            if i < 0:
                log.error("Index file is corrupted.")
                break
            word = idxStr[beg:i]
            i += 1
            if i + 8 > len(idxStr):
                log.error("Index file is corrupted")
                break
            offset = binStrToInt(idxStr[i:i+4])
            i += 4
            size = binStrToInt(idxStr[i:i+4])
            i += 4
            indexData.append([word, offset, size])

        return indexData

    def readDictFile(self, indexData, synData, sametypesequence):
        #from collections import Counter
        if isfile(self.fileBasePath+'.dict.dz'):
            import gzip
            dictFd = gzip.open(self.fileBasePath+'.dict.dz')
        else:
            dictFd = open(self.fileBasePath+'.dict', 'rb')

        for index, (word, defiOffset, defiSize) in enumerate(indexData):
            if not word:
                continue

            dictFd.seek(defiOffset)
            if dictFd.tell() != defiOffset:
                log.error("Unable to read definition for word \"{0}\"".format(word))
                continue

            data = dictFd.read(defiSize)

            if len(data) != defiSize:
                log.error("Unable to read definition for word \"{0}\"".format(word))
                continue

            if sametypesequence:
                rawDefis = self.parseDefiBlockCompact(data, sametypesequence, word)
            else:
                rawDefis = self.parseDefiBlockGeneral(data, word)

            if not rawDefis:
                continue

            defis = []
            defiFormats = []
            for rawDefi in rawDefis:
                _type = chr(rawDefi[1])
                defis.append(toStr(rawDefi[0]))
                defiFormats.append(
                    {
                        'm': 'm',
                        't': 'm',
                        'y': 'm',
                        'g': 'h',
                        'h': 'h',
                        'x': 'x',
                    }.get(_type, '')
                )

            ## FIXME
            defiFormat = defiFormats[0]
            #defiFormat = Counter(defiFormats).most_common(1)[0][0]
            
            if not defiFormat:
                log.warning("Definition format %s is not supported"%defiFormat)
            
            word = toStr(word)

            self.glos.addEntry(
                [word] + synData.get(index, []),
                defis,
                defiFormat=defiFormat,
            )


        dictFd.close()

    def readSynFile(self, indexCount):
        """
            returns synData, a dict { wordIndex -> synWordsList }
        """
        if not isfile(self.fileBasePath+'.syn'):
            return {}
        with open(self.fileBasePath+'.syn', 'rb') as synFile:
            synStr = synFile.read()
        synStrLen = len(synStr)
        synData = {}
        i = 0
        while i < synStrLen:
            beg = i
            i = synStr.find(b'\x00', beg)
            if i < 0:
                log.error("Synonym file is corrupted.")
                break
            word = synStr[beg:i]
            i += 1
            if i + 4 > len(synStr):
                log.error("Synonym file is corrupted.")
                break
            index = binStrToInt(synStr[i:i+4])
            i += 4
            if index >= indexCount:
                log.error("Corrupted synonym file. Word \"{0}\" references invalid item.".format(word))
                continue
            
            word = toStr(word)
            try:
                synData[index].append(word)
            except KeyError:
                synData[index] = [word]

        return synData


    def parseDefiBlockCompact(self, data, sametypesequence, word):
        """
            Parse definition block when sametypesequence option is specified.
        """
        sametypesequence = toBytes(sametypesequence)
        assert len(sametypesequence) > 0
        dataFileCorruptedError = "Data file is corrupted. Word \"{0}\"".format(word)
        res = []
        i = 0
        for t in sametypesequence[:-1]:
            if i >= len(data):
                log.error(dataFileCorruptedError)
                return None
            if isAsciiLower(t):
                beg = i
                i = data.find('\x00', beg)
                if i < 0:
                    log.error(dataFileCorruptedError)
                    return None
                res.append((data[beg:i], t))
                i += 1
            else:
                assert isAsciiUpper(t)
                if i + 4 > len(data):
                    log.error(dataFileCorruptedError)
                    return None
                size = binStrToInt(data[i:i+4])
                i += 4
                if i + size > len(data):
                    log.error(dataFileCorruptedError)
                    return None
                res.append((data[i:i+size], t))
                i += size

        if i >= len(data):
            log.error(dataFileCorruptedError)
            return None
        t = sametypesequence[-1]
        if isAsciiLower(t):
            i2 = data.find('\x00', i)
            if i2 >= 0:
                log.error(dataFileCorruptedError)
                return None
            res.append((data[i:], t))
        else:
            assert isAsciiUpper(t)
            res.append((data[i:], t))

        return res

    def parseDefiBlockGeneral(self, data, word):
        """
            Parse definition block when sametypesequence option is not specified.
        """
        dataFileCorruptedError = "Data file is corrupted. Word \"{0}\"".format(word)
        res = []
        i = 0
        while i < len(data):
            t = data[i]
            if not isAsciiAlpha(t):
                log.error(dataFileCorruptedError)
                return None
            i += 1
            if isAsciiLower(t):
                beg = i
                i = data.find(b'\x00', beg)
                if i < 0:
                    log.error(dataFileCorruptedError)
                    return None
                res.append((data[beg:i], t))
                i += 1
            else:
                assert isAsciiUpper(t)
                if i + 4 > len(data):
                    log.error(dataFileCorruptedError)
                    return None
                size = binStrToInt(data[i:i+4])
                i += 4
                if i + size > len(data):
                    log.error(dataFileCorruptedError)
                    return None
                res.append((data[i:i+size], t))
                i += size
        return res

    def readResources(self):
        baseDirPath = os.path.dirname(self.fileBasePath)
        resDirPath = join(baseDirPath, 'res')
        if isdir(resDirPath):
            self.glos.resPath = resDirPath
        else:
            resDbFilePath = join(baseDirPath, 'res.rifo')
            if isfile(resDbFilePath):
                log.warning("StarDict resource database is not supported. Skipping.")

class StarDictWriter(object):
    def __init__(self, glos, filename):
        self.glos = glos.copy()
        fileBasePath = ''
        ###
        if splitext(filename)[1].lower() == '.ifo':
            fileBasePath = splitext(filename)[0]
        elif filename.endswith(os.sep):
            if not isdir(filename):
                os.makedirs(filename)
            fileBasePath = join(filename, split(filename[:-1])[-1])
        elif isdir(filename):
            fileBasePath = join(filename, split(filename)[-1])
        ###
        if fileBasePath:
            fileBasePath = os.path.realpath(fileBasePath)
        self.fileBasePath = fileBasePath

    def run(self, dictZip, resOverwrite):
        ## no more direct access to glos.data, must use glos.sortWords for sorting
        ## no support for cmp argument because it's not supported in Python 3
        ## key function's argument is a str (word)
        self.glos.sortWords(
            key = stardictStrKey,
        )

        self.writeGeneral()
        #if self.glossaryHasAdditionalDefinitions():
        #    self.writeGeneral()
        #else:
        #    defiFormat = self.detectMainDefinitionFormat()
        #    if defiFormat == None:
        #        self.writeGeneral()
        #    else:
        #        self.writeCompact(defiFormat)

        if dictZip:
            runDictzip(self.fileBasePath)
        self.copyResources(
            self.glos.resPath,
            join(os.path.dirname(self.fileBasePath), 'res'),
            resOverwrite
        )

#    def writeCompact(self, defiFormat):
#        """
#            Build StarDict dictionary with sametypesequence option specified.
#            Every item definition consists of a single article.
#            All articles have the same format, specified in defiFormat parameter.
#
#            Parameters:
#            defiFormat - format of article definition: h - html, m - plain text
#        """
#        dictMark = 0
#        idxStr = ''
#        dictStr = ''
#        alternates = [] # contains tuples ('alternate', index-of-word)
#        for i, entry in enumerate(self.glos):
#            words = entry.getWords()
#            defi = entry.getDefi()
#            for altWord in words[1:]:
#                alternates.append((altWord, i))
#            dictStr += defi
#            defiLen = len(defi)
#            idxStr += words[0] + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(defiLen, 4)
#            dictMark += defiLen
#        wordCount = i + 1
#        with open(self.fileBasePath+'.dict', 'wb') as f:
#            f.write(dictStr)
#        with open(self.fileBasePath+'.idx', 'wb') as f:
#            f.write(idxStr)
#        indexFileSize = len(idxStr)
#        del idxStr, dictStr
#
#        self.writeSynFile(alternates)
#        self.writeIfoFile(wordCount, indexFileSize, len(alternates), defiFormat)

    def writeGeneral(self):
        """
            Build StarDict dictionary in general case.
            Every item definition may consist of an arbitrary number of articles.
            sametypesequence option is not used.
        """
        dictMark = 0
        #idxStr = ''
        #dictStr = ''
        alternates = [] # contains tuples ('alternate', index-of-word)

        dictFp = open(self.fileBasePath+'.dict', 'wb')
        idxFp = open(self.fileBasePath+'.idx', 'wb')
        indexFileSize = 0

        for i, entry in enumerate(self.glos):

            words = entry.getWords()## list
            word = words[0]
            defis = entry.getDefis()## list

            defiFormat = entry.getDefiFormat()
            if defiFormat not in ('m', 'h'):
                defiFormat = 'm'
            #assert isinstance(defiFormat, str) and len(defiFormat) == 1

            dictBlock = b''
            
            for altWord in words[1:]:
                alternates.append((altWord, i))

            dictBlock += toBytes(defiFormat + defis[0]) + b'\x00'

            for altDefi in defis[1:]:
                dictBlock += toBytes(defiFormat + altDefi) + b'\x00'
            
            dictFp.write(dictBlock)
            
            dataLen = len(dictBlock)
            idxBlock = toBytes(word) + b'\x00' + intToBinStr(dictMark, 4) + intToBinStr(dataLen, 4)
            idxFp.write(toBytes(idxBlock))
            
            dictMark += dataLen
            indexFileSize += len(idxBlock)

        wordCount = i + 1
        dictFp.close()
        idxFp.close()

        self.writeSynFile(alternates)
        self.writeIfoFile(wordCount, indexFileSize, len(alternates))

    def writeSynFile(self, alternates):
        """
            Build .syn file
        """
        if len(alternates) > 0:
            alternates.sort(key=lambda x: stardictStrKey(x[0]))
            synBytes = b''
            for item in alternates:
                synBytes += toBytes(item[0]) + b'\x00' + intToBinStr(item[1], 4)
            with open(self.fileBasePath+'.syn', 'wb') as f:
                f.write(synBytes)
            del synBytes

    def writeIfoFile(self, wordCount, indexFileSize, synwordcount, sametypesequence=None):
        """
            Build .ifo file
        """
        ifoStr = "StarDict's dict ifo file\n" \
            + "version=3.0.0\n" \
            + "bookname={0}\n".format(newlinesToSpace(self.glos.getInfo('name'))) \
            + "wordcount={0}\n".format(wordCount) \
            + "idxfilesize={0}\n".format(indexFileSize)
        if sametypesequence != None:
            ifoStr += "sametypesequence={0}\n".format(sametypesequence)
        if synwordcount > 0:
            ifoStr += 'synwordcount={0}\n'.format(synwordcount)
        for key in infoKeys:
            if key in ('bookname', 'wordcount', 'idxfilesize', 'sametypesequence'):
                continue
            value = self.glos.getInfo(key)
            if value == '':
                continue
            if key == 'description':
                ifoStr += '{0}={1}\n'.format(key, newlinesToBr(value))
            else:
                ifoStr += '{0}={1}\n'.format(key, newlinesToSpace(value))
        with open(self.fileBasePath+'.ifo', 'wb') as f:
            f.write(toBytes(ifoStr))
        del ifoStr

    def copyResources(self, fromPath, toPath, overwrite):
        """
            Copy resource files from fromPath to toPath.
        """
        import shutil
        if not fromPath:
            return
        fromPath = os.path.abspath(fromPath)
        toPath = os.path.abspath(toPath)
        if fromPath == toPath:
            return
        if not isdir(fromPath):
            return
        if len(os.listdir(fromPath))==0:
            return
        if overwrite and os.path.exists(toPath):
            shutil.rmtree(toPath)
        if os.path.exists(toPath):
            if len(os.listdir(toPath)) > 0:
                log.error(
'''Output resource directory is not empty: "{0}". Resources will not be copied!
Clean the output directory before running the converter or pass option: --write-options=res-overwrite=True.'''\
.format(toPath)
                )
                return
            os.rmdir(toPath)
        shutil.copytree(fromPath, toPath)

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
            Scan main definitions of the glossary. Return format common to all definitions: h or m.
            If definitions has different formats return None.
        """
        self.glos.setDefaultDefiFormat('m')
        formatsCount = self.glos.getMostUsedDefiFormats()
        if not formatsCount:
            return None
        if len(formatsCount) > 1:## FIXME
            return None
        
        return formatsCount[0]
        

def verifySameTypeSequence(s):
    if not s:
        return True
    for t in s:
        if not isAsciiAlpha(t):
            log.error("Invalid sametypesequence option")
            return False
    return True

def read(glos, filename):
    reader = StarDictReader(glos, filename)
    reader.run()

def write(glos, filename, dictZip=True, resOverwrite=False):
    writer = StarDictWriter(glos, filename)
    writer.run(dictZip, resOverwrite)


