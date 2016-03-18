# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'GettextPo'
description = 'Gettext Source (po)'
extentions = ['.po',]
readOptions = []
writeOptions = []

from polib import escape, unescape



def read(glos, filename):
    fp = open(filename, 'rb')
    word = ''
    defi = ''
    msgstr = False
    for line in fp:
        if not line:
            if word:
                glos.addEntry(word, defi)
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
                glos.addEntry(word, defi)
                word = ''
                defi = ''
            word = unescape(line[6:])
            msgstr = False
        elif line.startswith('msgstr '):
            if msgstr:
                log.error('msgid omitted!')
            defi = unescape(line[7:])
            msgstr = True
        else:
            if msgstr:
                defi += unescape(line)
            else:
                word += unescape(line)
    if word:
        glos.addEntry(word, defi)


def write(glos, filename):
    fp = open(filename, 'wb')
    fp.write('#\nmsgid ""\nmsgstr ""\n')
    for inf in glos.infoKeys():
        fp.write('"%s: %s\\n"\n'%(inf, glos.getInfo(inf)))
    for entry in glos:
        word = entry.getWord()
        defi = entry.getDefi()
        fp.write('msgid %s\nmsgstr %s\n\n'%(
            escape(word),
            escape(defi),
        ))
    fp.close()

