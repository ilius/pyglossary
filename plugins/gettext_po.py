#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'GettextPo'
description = 'Gettext Source (po)'
extentions = ['.po',]
readOptions = []
writeOptions = []

def read(glos, filename):
  fp = open(filename, 'rb')
  word = ''
  defi = ''
  msgstr = False
  glos.data = []
  while True:
    line = fp.readline()
    if not line:
      if word:
        glos.data.append((word, defi))
        word = ''
        defi = ''
      break
    line = line.strip()
    if not line:
      continue
    if line.startswith('#'):
      continue
    if line.startswith('msgid '):
      if word:
        glos.data.append((word, defi))
        word = ''
        defi = ''
      word = eval(line[6:])
      msgstr = False
    elif line.startswith('msgstr '):
      if msgstr:
        printAsError('msgid omitted!')
      defi = eval(line[7:])
      msgstr = True
    else:
      if msgstr:
        defi += eval(line)
      else:
        word += eval(line)


def write(glos, filename):
  fp = open(filename, 'wb')
  fp.write('#\nmsgid ""\nmsgstr ""\n')
  for inf in glos.infoKeys():
    fp.write('"%s: %s\\n"'%(inf, glos.getInfo(inf)))
  for item in glos.data:
    fp.write('msgid "%s"\nmsgstr "%s"\n\n'%item[:2])
  fp.close()

"""
def read(glos, filename):## FIXME
  pass
"""
