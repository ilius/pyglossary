#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Xdxf'
description = 'XDXF'
extentions = ['.xdxf', '.xml']
readOptions = []
writeOptions = []

def read(glos, filename):
  ##<!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">
  from xml.etree.ElementTree import XML, tostring
  fp = open(filename, 'rb')
  xdxf = XML(fp.read())
  fp.close()
  full_name = tostring(xdxf[0]).replace('<full_name>', '')\
                                 .replace('</full_name>', '')
  description = tostring(xdxf[1]).replace('<description>', '')\
                                 .replace('</description>', '')
  while full_name[-1]=='\n':
    full_name=full_name[:-1]
  while description[-1]=='\n':
    description=description[:-1]
  glos.setInfo('name', full_name)
  glos.setInfo('description',description)
  maxWordLen=0
  for item in xdxf[2:]:
    if len(item)==2:
      defi = tostring(item[1]).replace('<tr>', '').replace('</tr>', '\n')
      word = tostring(item[0]).replace('<k>', '').replace('</k>', '')
    elif len(item)==1:
      itemStr=tostring(item[0])
      ki = itemStr.find('</k>')
      defi = itemStr[ki+4:]
      word = itemStr[:ki].replace('<k>', '')
    #else:
    #  print(word, len(item))
    while word[-1]=='\n':
      word=word[:-1]
    if defi!='':
      while defi[-1]=='\n':
        defi=defi[:-1]
      while defi[0]=='\n':
        defi=defi[1:]
    wordLen=len(word)
    if maxWordLen<len(word):
      maxWordLen=len(word)
    glos.data.append((word, defi))


