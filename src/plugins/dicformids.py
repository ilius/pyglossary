# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Dicformids'
description = 'DictionaryForMIDs'
extentions = ['.mids']
readOptions = []
writeOptions = []


def write(glos, filename):
    initCwd = os.getcwd()
    indexFileMaxSize = 30000
    language1FilePostfix = 'Eng'
    if not os.path.isdir(filename):
        os.mkdir(filename)
    os.chdir(filename)
    n = len(glos.data)
    index = [None]*n
    dicMaxSize = 0
    k = 1
    indFp = open('index%s1.csv'%language1FilePostfix, 'wb')
    dicFp = open('directory%s1.csv'%language1FilePostfix, 'wb')
    for i in xrange(n):
        if i%200==0 and i>0:
            #dicFp.close()
            dicSize = dicFp.tell()
            if dicSize > dicMaxSize:
                dicMaxSize = dicSize
            dicFp = open('directory%s%d.csv'%(language1FilePostfix, i/200), 'wb')
        w, m = glos.data[i][:2]
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



