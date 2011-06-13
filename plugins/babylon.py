#!/usr/bin/python
# -*- coding: utf-8 -*-
enable = True
format = 'Babylon'
description = 'Babylon Source (gls)'
extentions = ('.gls', '.babylon')
readOptions = ()
writeOptions = ('writeInfo', 'newline', 'encoding')

from text_utils import recodeToWinArabic

def write(glos, filename, writeInfo=True, newline='', encoding='utf8'):
  ## Source Glossary for "Babylon Builder".
  ## It has extention '.gls' or '.babylon'. But not '.bgl'.
  ## It is a (unicode) text file. Not binary like bgl files.
  winArabic=['windows-1256', 'windows-arabic', 'arabic-windows',
             'arabic windows', 'windows arabic']
  g = glos
  encoding = encoding.lower()
  if not encoding in ('utf8', ''):
    g = glos.copy()
    if encoding in winArabic:
      for i in xrange(len(g.data)):
        g.data[i] = (recodeToWinArabic(g.data[i][0]), recodeToWinArabic(g.data[i][1])) + tuple(g.data[i][2:])
      if newline=='':
        newline='\r\n'
    else:
      for i in xrange(len(g.data)):
        g.data[i]=(g.data[i][0].decode('utf8').encode(encoding), g.data[i][1].decode('utf8').encode(encoding)) + g.data[i][2:]
  if newline=='':
    newline='\n'
  head=''
  if writeInfo:
    head += '### Glossary title:%s%s' %(g.getInfo('name'),newline)
    head += '### Author:%s%s'         %(g.getInfo('author'),newline)
    head += '### Description:%s%s'    %(g.getInfo('description'),newline)
    head += '### Source language:%s%s'%(g.getInfo('inputlang'),newline)
    if encoding in winArabic:
      head += '### Source alphabet:Arabic%s'%newline
    else:
      head += '### Source alphabet:%s%s'%(encoding,newline)
    head += '### Target language:%s%s'%(g.getInfo('outputlang'),newline)
    if encoding in winArabic:
      head += '### Target alphabet:Arabic%s'%newline
    else:
      head += '### Target alphabet:%s%s'%(encoding,newline)
    head += '### Browsing enabled?Yes%s'%newline
    head += '### Type of glossary:00000000%s'%newline
    head += '### Case sensitive words?0%s'%newline
    head += '\n### Glossary section:%s'%newline
  g.writeTxt((newline, newline*2), filename=filename, writeInfo=False,
             rplList=(('\n', '<BR>'),), ext='.gls', head=head)

