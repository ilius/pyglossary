# -*- coding: utf-8 -*-
from formats_common import *

enable = True
format = 'Stardict'
description = 'StarDict (ifo)'
extentions = ['.ifo']
readOptions = []
writeOptions = ['resOverwrite']
supportsAlternates = True

import sys
sys.path.append('/usr/share/pyglossary/src')

import os, re, shutil
import os.path
from os.path import join, split, splitext, isfile, isdir

from pyglossary.text_utils import intToBinStr, binStrToInt, runDictzip

infoKeys = ('bookname', 'author', 'email', 'website', 'description', 'date')

class StarDictReader:
    def __init__(self, glos, filename):
        self.glos = glos
        if splitext(filename)[1].lower() == '.ifo':
            self.fileBasePath = splitext(filename)[0]
        else:
            self.fileBasePath = filename
        self.fileBasePath = os.path.realpath(self.fileBasePath)
    
    def run(self):
        self.glos.data = []
        self.readIfoFile()
        sametypesequence = self.glos.getInfo('sametypesequence')
        if not verifySameTypeSequence(sametypesequence):
            return
        """indexData format
        indexData[i] - i-th record in index file
        indexData[i][0] - word (string)
        indexData[i][1] - definition block offset in dict file
        indexData[i][2] - definition block size in dict file
        indexData[i][3] - list of definitions
        indexData[i][3][0] - definition data
        indexData[i][3][1] - definition type - 'h' or 'm'
        indexData[i][4] - list of synonyms (strings)
        """
        self.readIdxFile()
        self.readDictFile(sametypesequence)
        self.readSynFile()
        self.assignGlossaryData()
        self.readResources()
        
    def readIfoFile(self):
        """.ifo file is a text file in utf-8 encoding
        """
        with open(self.fileBasePath+'.ifo', 'rb') as f:
            ifoStr = f.read()
        for line in splitStringIntoLines(ifoStr):
            line = line.strip()
            if not line:
                continue
            ind = line.find('=')
            if ind==-1:
                #log.error('Invalid ifo file line: {0}'.format(line))
                continue
            self.glos.setInfo(line[:ind].strip(), line[ind+1:].strip())
    
    def readIdxFile(self):
        if isfile(self.fileBasePath+'.idx.gz'):
            import gzip
            with gzip.open(self.fileBasePath+'.idx.gz') as f:
                idxStr = f.read()
        else:
            with open(self.fileBasePath+'.idx', 'rb') as f:
                idxStr = f.read()
        self.indexData = []
        i = 0
        while i < len(idxStr):
            beg = i
            i = idxStr.find('\x00', beg)
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
            self.indexData.append([word, offset, size, [], []])
        
    def readDictFile(self, sametypesequence):
        if isfile(self.fileBasePath+'.dict.dz'):
            import gzip
            dictFd = gzip.open(self.fileBasePath+'.dict.dz')
        else:
            dictFd = open(self.fileBasePath+'.dict', 'rb')
        
        for rec in self.indexData:
            dictFd.seek(rec[1])
            if dictFd.tell() != rec[1]:
                log.error("Unable to read definition for word \"{0}\"".format(rec[0]))
                rec[0] = None
                continue
            data = dictFd.read(rec[2])
            if len(data) != rec[2]:
                log.error("Unable to read definition for word \"{0}\"".format(rec[0]))
                rec[0] = None
                continue
            if sametypesequence:
                res = self.parseDefiBlockCompact(data, sametypesequence, rec[0])
            else:
                res = self.parseDefiBlockGeneral(data, rec[0])
            if res == None:
                rec[0] = None
                continue
            res = self.convertDefinitionsToPyglossaryFormat(res)
            if len(res) == 0:
                rec[0] = None
                continue
            rec[3] = res
            
        dictFd.close()

    def readSynFile(self):
        if not isfile(self.fileBasePath+'.syn'):
            return
        with open(self.fileBasePath+'.syn', 'rb') as f:
            synStr = f.read()
        i = 0
        while i < len(synStr):
            beg = i
            i = synStr.find('\x00', beg)
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
            if index >= len(self.indexData):
                log.error("Corrupted synonym file. Word \"{0}\" references invalid item.".format(word))
                continue
            self.indexData[index][4].append(word)

    def parseDefiBlockCompact(self, data, sametypesequence, word):
        """Parse definition block when sametypesequence option is specified.
        """
        assert isinstance(sametypesequence, str)
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
        """Parse definition block when sametypesequence option is not specified.
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
        return res

    def convertDefinitionsToPyglossaryFormat(self, defis):
        """Convert definitions extracted from StarDict dictionary to format supported by pyglossary.
        Skip unsupported definition.
        """
        res = []
        for rec in defis:
            if rec[1] in 'mty':
                res.append((rec[0], 'm'))
            elif rec[1] in 'gh':
                res.append((rec[0], 'h'))
            else:
                log.warn("Definition format {0} is not supported. Skipping.".format(rec[1]))
        return res
        
    def assignGlossaryData(self):
        '''Fill glos.data array with data extracted from StarDict dictionary
        '''
        self.glos.data = []
        for rec in self.indexData:
            if not rec[0]:
                continue
            if len(rec[3]) == 0:
                continue
            d = { 'defiFormat': rec[3][0][1] }
            if len(rec[3]) > 1:
                d['defis'] = rec[3][1:]
            if len(rec[4]) > 0:
                d['alts'] = rec[4]
            self.glos.data.append((rec[0], rec[3][0][0], d))
    
    def readResources(self):
        baseDirPath = os.path.dirname(self.fileBasePath)
        resDirPath = join(baseDirPath, 'res')
        if isdir(resDirPath):
            self.glos.resPath = resDirPath
        else:
            resDbFilePath = join(baseDirPath, 'res.rifo')
            if isfile(resDbFilePath):
                log.warn("StarDict resource database is not supported. Skipping.")
    
class StarDictWriter:
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
        self.glos.data.sort(stardict_strcmp, lambda x: x[0])
        
        if self.GlossaryHasAdditionalDefinitions():
            self.writeGeneral()
        else:
            articleFormat = self.DetectMainDefinitionFormat()
            if articleFormat == None:
                self.writeGeneral()
            else:
                self.writeCompact(articleFormat)
        
        if dictZip:
            runDictzip(self.fileBasePath)
        self.copyResources(
            self.glos.resPath,
            join(os.path.dirname(self.fileBasePath), 'res'),
            resOverwrite
        )

    def writeCompact(self, articleFormat):
        """Build StarDict dictionary with sametypesequence option specified.
        Every item definition consists of a single article.
        All articles have the same format, specified in articleFormat parameter.
        
        Parameters:
        articleFormat - format of article definition: h - html, m - plain text
        """
        dictMark = 0
        idxStr = ''
        dictStr = ''
        alternates = [] # contains tuples ('alternate', index-of-word)
        for i in xrange(len(self.glos.data)):
            item = self.glos.data[i]
            word, defi = item[:2]
            if len(item) > 2 and 'alts' in item[2]:
                alternates += [(x, i) for x in item[2]['alts']]
            dictStr += defi
            defiLen = len(defi)
            idxStr += word + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(defiLen, 4)
            dictMark += defiLen
        with open(self.fileBasePath+'.dict', 'wb') as f:
            f.write(dictStr)
        with open(self.fileBasePath+'.idx', 'wb') as f:
            f.write(idxStr)
        indexFileSize = len(idxStr)
        del idxStr, dictStr
        
        self.writeSynFile(alternates)
        self.writeIfoFile(indexFileSize, len(alternates), articleFormat)

    def writeGeneral(self):
        """Build StarDict dictionary in general case.
        Every item definition may consist of an arbitrary number of articles.
        sametypesequence option is not used.
        """
        dictMark = 0
        idxStr = ''
        dictStr = ''
        alternates = [] # contains tuples ('alternate', index-of-word)
        for i in xrange(len(self.glos.data)):
            item = self.glos.data[i]
            word, defi = item[:2]
            if len(item) > 2 and 'alts' in item[2]:
                alternates += [(x, i) for x in item[2]['alts']]
            if len(item) > 2 and 'defiFormat' in item[2]:
                articleFormat = item[2]['defiFormat']
                if articleFormat not in 'mh':
                    articleFormat = 'm'
            else:
                articleFormat = 'm'
            assert isinstance(articleFormat, str) and len(articleFormat) == 1
            dictStr += articleFormat
            dictStr += defi + '\x00'
            dataLen = 1 + len(defi) + 1
            if len(item) > 2 and 'defis' in item[2]:
                for rec in item[2]['defis']:
                    defi, t = rec[:2]
                    assert isinstance(t, str) and len(t) == 1
                    dictStr += t
                    dictStr += defi + '\x00'
                    dataLen += 1 + len(defi) + 1
            idxStr += word + '\x00' + intToBinStr(dictMark, 4) + intToBinStr(dataLen, 4)
            dictMark += dataLen
        with open(self.fileBasePath+'.dict', 'wb') as f:
            f.write(dictStr)
        with open(self.fileBasePath+'.idx', 'wb') as f:
            f.write(idxStr)
        indexFileSize = len(idxStr)
        del idxStr, dictStr
        
        self.writeSynFile(alternates)
        self.writeIfoFile(indexFileSize, len(alternates))

    def writeSynFile(self, alternates):
        """Build .syn file
        """
        if len(alternates) > 0:
            alternates.sort(stardict_strcmp, lambda x: x[0])
            synStr = ''
            for item in alternates:
                synStr += item[0] + '\x00' + intToBinStr(item[1], 4)
            with open(self.fileBasePath+'.syn', 'wb') as f:
                f.write(synStr)
            del synStr

    def writeIfoFile(self, indexFileSize, synwordcount, sametypesequence = None):
        """Build .ifo file
        """
        ifoStr = "StarDict's dict ifo file\n" \
            + "version=3.0.0\n" \
            + "bookname={0}\n".format(new_lines_2_space(self.glos.getInfo('name'))) \
            + "wordcount={0}\n".format(len(self.glos.data)) \
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
                ifoStr += '{0}={1}\n'.format(key, new_line_2_br(value))
            else:
                ifoStr += '{0}={1}\n'.format(key, new_lines_2_space(value))
        with open(self.fileBasePath+'.ifo', 'wb') as f:
            f.write(ifoStr)
        del ifoStr
        
    def copyResources(self, fromPath, toPath, overwrite):
        '''Copy resource files from fromPath to toPath.
        '''
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

    def GlossaryHasAdditionalDefinitions(self):
        """Search for additional definitions in the glossary.
        We need to know if the glossary contains additional definitions 
        to make the decision on the format of the StarDict dictionary.
        """
        for rec in self.glos.data:
            if len(rec) > 2 and 'defis' in rec[2]:
                return True
        return False
        
    def DetectMainDefinitionFormat(self):
        """Scan main definitions of the glossary. Return format common to all definitions: h or m.
        If definitions has different formats return None.
        """
        articleFormat = None
        for rec in self.glos.data:
            if len(rec) > 2 and 'defiFormat' in rec[2]:
                f = rec[2]['defiFormat']
                if f not in 'hm':
                    f = 'm'
            else:
                f = 'm'
            if articleFormat == None:
                articleFormat = f
            if articleFormat != f:
                return None
        return articleFormat
        

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

def read_ext(glos, filename):
    ## This method uses module provided by dictconv, but dictconv is very slow for reading from stardict db!
    ## therefore this method in not used by GUI now.
    ## and binary module "_stardict" is deleted.
    ## If you want to use it, compile it yourglos, or get it from an older version of PyGlossary (version 2008.08.30)
    glos.data = []
    import _stardict
    db = _stardict.new_StarDict(filename)
    _stardict.PySwigIterator_swigregister(db)
    glos.setInfo('title', _stardict.StarDict_bookname(db))
    glos.setInfo('author', _stardict.StarDict_bookname(db))
    glos.setInfo('title', _stardict.StarDict_bookname(db))
    ## geting words:
    idxStr = open(filename[:-4]+'.idx').read()
    words=[]
    #''' # get words list by python codes.
    word=''
    i=0
    while i < len(idxStr):
        if idxStr[i]=='\x00':
            if word!='':
                words.append(word)
                word = ''
            i += 9
        else:
            word += idxStr[i]
            i += 1
    ''' # get words list using _stardict module.
    lst = _stardict.StarDict_dump(db) ## don't know how to get std::vector items
    _stardict.PySwigIterator_swigregister(lst)
    num = _stardict.StarDict_vector_get_size(db, lst)
    _stardict.PySwigIterator_swigregister(num)
    for i in xrange(num):
        word = _stardict.StarDict_vector_get_item(db, lst, i)
        words.append(word)
        if i%100==0:
            log.debug(i)
            while gtk.events_pending():
                gtk.main_iteration_do(False)
    '''
    ui = glos.ui
    n = len(words)
    i=0
    if ui==None:
        for word in words:
            defi = _stardict.StarDict_search(db, word).replace('<BR>', '\n')
            glos.data.append((word, defi))
    else:
        ui.progressStart()
        k = 1000
        for i in xrange(n):
            word = words[i]
            defi = _stardict.StarDict_search(db, word).replace('<BR>', '\n')
            glos.data.append((word, defi))
            if i%k==0:
                rat = float(i)/n
                ui.progress(rat)
        #ui.progress(1.0, 'Loading Completed')
        ui.progressEnd()


def write_ext(glos, filename, sort=True, dictZip=True):
    if sort:
        g = glos.copy()
        g.data.sort()
    else:
        g = glos
    try:
        import _stardictbuilder
    except ImportError:
        log.error('Binary module "_stardictbuilder" can not be imported! '+\
            'Using internal StarDict builder')
        return g.writeStardict(filename, sort=False)
    db = _stardictbuilder.new_StarDictBuilder(filename)
    _stardictbuilder.StarDictBuilder_swigregister(db)
    for item in g.data:
        _stardictbuilder.StarDictBuilder_addHeadword(db, item[0], item[1], '')
    _stardictbuilder.StarDictBuilder_setTitle(db, g.getInfo('name'))
    _stardictbuilder.StarDictBuilder_setAuthor(db, g.getInfo('author'))
    _stardictbuilder.StarDictBuilder_setLicense(db, g.getInfo('license'))
    _stardictbuilder.StarDictBuilder_setOrigLang(db, g.getInfo('origLang'))
    _stardictbuilder.StarDictBuilder_setDestLang(db, g.getInfo('destLang'))
    _stardictbuilder.StarDictBuilder_setDescription(db, g.getInfo('description'))
    _stardictbuilder.StarDictBuilder_setComments(db, g.getInfo('comments'))
    _stardictbuilder.StarDictBuilder_setEmail(db, g.getInfo('email'))
    _stardictbuilder.StarDictBuilder_setWebsite(db, g.getInfo('website'))
    _stardictbuilder.StarDictBuilder_setVersion(db, g.getInfo('version'))
    _stardictbuilder.StarDictBuilder_setcreationTime(db, '')
    _stardictbuilder.StarDictBuilder_setLastUpdate(db, '')
    _stardictbuilder.StarDictBuilder_finish(db)
    if dictZip:
        if filename[-4:]=='.ifo':
            filename = filename[:-4]
            runDictzip(filename)

def splitStringIntoLines(s):
    """Split string s into lines.
    Accept any line separator: '\r\n', '\r', '\n'
    """
    res = []
    beg = 0
    end = 0
    while end < len(s):
        while end < len(s) and s[end] != '\r' and s[end] != '\n':
            end += 1
        res.append(s[beg:end])
        if end+1 < len(s) and s[end] == '\r' and s[end+1] == '\n':
            end += 1
        beg = end = end + 1
    return res

def isAsciiAlpha(c):
    return (ord(c) >= ord('A') and ord(c) <= ord('Z')) or (ord(c) >= ord('a') and ord(c) <= ord('z'))

def isAsciiLower(c):
    return ord(c) >= ord('a') and ord(c) <= ord('z')
    
def isAsciiUpper(c):
    'imitate ISUPPER macro of glib library gstrfuncs.c file'
    return ord(c) >= ord('A') and ord(c) <= ord('Z')

def asciiLower(c):
    '''imitate TOLOWER macro of glib library gstrfuncs.c file

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
    '''
    if isAsciiUpper(c):
        return chr((ord(c) - ord('A')) + ord('a'))
    else:
        return c

def ascii_strcasecmp(s1, s2):
    'imitate g_ascii_strcasecmp function of glib library gstrfuncs.c file'
    commonLen = min(len(s1), len(s2))
    for i in xrange(commonLen):
        c1 = ord(asciiLower(s1[i]))
        c2 = ord(asciiLower(s2[i]))
        if c1 != c2:
            return c1 - c2
    return len(s1) - len(s2)

def strcmp(s1, s2):
    '''imitate strcmp of standard C library

    Attention! You may have a temptation to replace this function with built-in cmp() function.
    Hold on! Most probably these two function behave identically now, but cmp does not
    document how it compares strings. There is no guaranty it will not be changed in future.
    Since we need predictable sorting order in StarDict dictionary, we need to preserve
    this function despite the fact there are other ways to implement it.
    '''
    commonLen = min(len(s1), len(s2))
    for i in xrange(commonLen):
        c1 = ord(s1[i])
        c2 = ord(s2[i])
        if c1 != c2:
            return c1 - c2
    return len(s1) - len(s2)

def stardict_strcmp(s1, s2):
    '''
        use this function to sort index items in StarDict dictionary
        s1 and s2 must be utf-8 encoded strings
    '''
    a = ascii_strcasecmp(s1, s2)
    if a == 0:
        return strcmp(s1, s2)
    else:
        return a

def new_lines_2_space(text):
    return re.sub('[\n\r]+', ' ', text)

def new_line_2_br(text):
    return re.sub('\n\r?|\r\n?', '<br>', text)

