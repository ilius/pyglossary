# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Dicformids'
description = 'DictionaryForMIDs'
extentions = ['.mids']
readOptions = []
writeOptions = []

import re
from os.path import join
from tabfile import Reader as TabfileReader

class Reader(object):
    def __init__(self, glos):
        self._glos = glos
        self._tabFileNames = []
        self._tabFileReader = None
    def open(self, dirname):
        self._dirname = dirname
        dicFiles = []
        orderFileNames = []
        for fname in os.listdir(dirname):
            if not fname.startswith('directory'):
                continue
            try:
                num = re.findall('\d+', fname)[-1]
            except IndexError:
                pass
            else:
                orderFileNames.append((num, fname))
        orderFileNames.sort(
            key=lambda x: x[0],
            reverse=True,
        )
        self._tabFileNames = [x[1] for x in orderFileNames]
        self.nextTabFile()

    def __len__(self):## FIXME
        raise NotImplementedError

    __iter__ = lambda self: self
    def next(self):
        for _ in range(10):
            try:
                return self._tabFileReader.next()
            except StopIteration:
                self._tabFileReader.close()
                self.nextTabFile()
    def nextTabFile(self):
        try:
            tabFileName = self._tabFileNames.pop()
        except IndexError:
            raise StopIteration
        self._tabFileReader = TabfileReader(self._glos, hasInfo=False)
        self._tabFileReader.open(join(self._dirname, tabFileName))
    def close(self):
        if self._tabFileReader:
            try:
                self._tabFileReader.close()
            except:
                pass
        self._tabFileReader = None
        self._tabFileNames = []

def read(glos, filename):
    reader = Reader(glos)
    reader.open(filename)
    for entry in reader:
        if not entry:
            continue
        glos.addEntryObj(entry)
    reader.close()
    return True




def write(glos, filename):
    initCwd = os.getcwd()
    indexFileMaxSize = 30000
    language1FilePostfix = 'Eng'
    if not os.path.isdir(filename):
        os.mkdir(filename)
    os.chdir(filename)
    n = len(glos)
    index = [None]*n
    dicMaxSize = 0
    k = 1
    indFp = open('index%s1.csv'%language1FilePostfix, 'wb')
    dicFp = open('directory%s1.csv'%language1FilePostfix, 'wb')
    for i, entry in enumerate(glos):
        if i%200==0 and i>0:
            #dicFp.close()
            dicSize = dicFp.tell()
            if dicSize > dicMaxSize:
                dicMaxSize = dicSize
            dicFp = open('directory%s%d.csv'%(language1FilePostfix, i/200), 'wb')
        w, m = entry.getWord(), entry.getDefi()
        dicLine = '%s\t%s\n'%(w, m)
        dicFp.write(dicLine)
        if i%200==0:
            index[i] = 0
        else:
            index[i] = index[i-1] + len(dicLine)
        indLine = '%s\t%d-%d-B\n'%(
            w,
            i/200 + 1,
            index[i],
        )
        size = indFp.tell()
        if size + len(indLine) > indexFileMaxSize - 10 :
            k += 1
            #indFp.close()
            indFp = open('index%s%d.csv'%(language1FilePostfix, k), 'wb')
        indFp.write(indLine)
    dicFp.close()
    indFp.close()
    open('DictionaryForMIDs.properties', 'wb').write('\n'.join([
        '#DictionaryForMIDs property file',
        'infoText=%s, author: %s'%(glos.getInfo('name'), glos.getInfo('author')),
        'indexFileMaxSize=%s\n'%indexFileMaxSize,
        'language1IndexNumberOfSourceEntries=%d'%n,
        'language1DictionaryUpdateClassName=de.kugihan.dictionaryformids.dictgen.DictionaryUpdate',
        'indexCharEncoding=ISO-8859-1',
        "dictionaryFileSeparationCharacter='\\t'",
        'language2NormationClassName=de.kugihan.dictionaryformids.translation.Normation',
        'language2DictionaryUpdateClassName=de.kugihan.dictionaryformids.dictgen.DictionaryUpdate',
        'logLevel=0',
        'language1FilePostfix=%s'%language1FilePostfix,
        'dictionaryCharEncoding=UTF-8',
        'numberOfAvailableLanguages=2',
        'language1IsSearchable=true',
        'language2GenerateIndex=false',
        'dictionaryFileMaxSize=%d'%(dicMaxSize+1),
        'language2FilePostfix=fa',
        'searchListFileMaxSize=20000',
        'language2IsSearchable=false',
        'fileEncodingFormat=plain_format1',
        'language1HasSeparateDictionaryFile=true',
        'searchListCharEncoding=ISO-8859-1',
        "searchListFileSeparationCharacter='\t'",
        "indexFileSeparationCharacter='\t'",
        'language1DisplayText=%s'%glos.getInfo('inputlang'),
        'language2HasSeparateDictionaryFile=false',
        'dictionaryGenerationInputCharEncoding=UTF-8',
        'language1GenerateIndex=true',
        'language2DisplayText=%s'%glos.getInfo('outputlang'),
        'language1NormationClassName=de.kugihan.dictionaryformids.translation.NormationEng',
    ]))
    #open('searchlist%s.csv'%language1FilePostfix, 'wb') ### FIXME
    os.chdir(initCwd)



