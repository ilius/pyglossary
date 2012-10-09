#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'SdictSrc'
description = 'Sdictionary Source (sdct)'
extentions = ['.sdct']
readOptions = []
writeOptions = ['writeInfo', 'newline']

def write(glos, filename, writeInfo=True, newline='\n'):
  ## Source Glossary for "Sdictionary" (http://sdict.org)
  ## It has extention '.sdct'
  head=''
  if writeInfo:
    head += '<header>\n'
    head += 'title = %s\n' %glos.getInfo('name')
    head += 'author = %s\n'         %glos.getInfo('author')
    head += 'description = %s\n'    %glos.getInfo('description')
    head += 'w_lang = %s\n'%glos.getInfo('inputlang')
    head += 'a_lang = %s\n'%glos.getInfo('outputlang')
    head += '</header>\n#\n#\n#\n'
  glos.writeTxt(('___', newline), filename, False,
                (('\n', '<BR>'),), '.sdct', head)


