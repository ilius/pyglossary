#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Dicformids'
description = 'DictionaryForMIDs'
extentions = ('.mids',)
readOptions = ()
writeOptions = ('writeInfo',)


def write(glos, filename, writeInfo=True):
  initCwd = os.getcwd()
  #'DictionaryForMIDs'
  indexFileMaxSize=30000
  language1FilePostfix='Eng'
  if not os.path.isdir(filename):
    os.mkdir(filename)
  os.chdir(filename)
  n=len(glos.data)
  index=[None]*n
  dicMaxSize=0
  k = 1
  indFp = open('index%s1.csv'%language1FilePostfix, 'wb')
  dicFp = open('directory%s1.csv'%language1FilePostfix, 'wb')
  for i in xrange(n):
    if i%200==0 and i>0:
      #dicFp.close()
      dicSize=dicFp.tell()
      if dicSize > dicMaxSize:
        dicMaxSize = dicSize
      dicFp = open('directory%s%d.csv'%(language1FilePostfix, i/200), 'wb')
    [w,m]=glos.data[i][0:2]
    dicLine='%s\t%s\n'%(w,m)
    dicFp.write(dicLine)
    if i%200==0:
      index[i] = 0
    else:
      index[i] = index[i-1] + len(dicLine)
    indLine = '%s\t%d-%d-B\n'%(w,(i/200+1),index[i])
    size = indFp.tell()
    if size + len(indLine) > indexFileMaxSize-10 :
      k += 1
      #indFp.close()
      indFp = open('index%s%d.csv'%(language1FilePostfix, k) , 'wb')
    indFp.write(indLine)
  dicFp.close()
  indFp.close()
  propFp = open('DictionaryForMIDs.properties', 'wb')
  propStr='#DictionaryForMIDs property file\n' +\
          'infoText=%s, author: %s\n'%(glos.getInfo('name'),glos.getInfo('author'))+\
          'indexFileMaxSize=%s\n'%indexFileMaxSize +\
          'language1IndexNumberOfSourceEntries=%d\n'%n +\
          'language1DictionaryUpdateClassName=de.kugihan.dictionaryformids.dictgen.DictionaryUpdate\n'+\
          'indexCharEncoding=ISO-8859-1\n'+\
          "dictionaryFileSeparationCharacter='\\t'\n"+\
          'language2NormationClassName=de.kugihan.dictionaryformids.translation.Normation\n'+\
          'language2DictionaryUpdateClassName=de.kugihan.dictionaryformids.dictgen.DictionaryUpdate\n'+\
          'logLevel=0\n'+\
          'language1FilePostfix=%s\n'%language1FilePostfix +\
          'dictionaryCharEncoding=UTF-8\n'+\
          'numberOfAvailableLanguages=2\n'+\
          'language1IsSearchable=true\n' +\
          'language2GenerateIndex=false\n' +\
          'dictionaryFileMaxSize=%d\n'%(dicMaxSize+1) +\
          'language2FilePostfix=fa\n' +\
          'searchListFileMaxSize=20000\n' +\
          'language2IsSearchable=false\n' +\
          'fileEncodingFormat=plain_format1\n' +\
          'language1HasSeparateDictionaryFile=true\n' +\
          'searchListCharEncoding=ISO-8859-1\n' +\
          "searchListFileSeparationCharacter='\t'\n" +\
          "indexFileSeparationCharacter='\t'\n" +\
          'language1DisplayText=English\n' +\
          'language2HasSeparateDictionaryFile=false\n' +\
          'dictionaryGenerationInputCharEncoding=UTF-8\n' +\
          'language1GenerateIndex=true\n' +\
          'language2DisplayText=farsi\n' +\
          'language1NormationClassName=de.kugihan.dictionaryformids.translation.NormationEng\n' +\
  open('searchlist%s.csv'%language1FilePostfix, 'wb') ### ??????????????????????????????????????
  os.chdir(initCwd)



