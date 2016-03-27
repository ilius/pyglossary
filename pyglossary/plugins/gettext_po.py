# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'GettextPo'
description = 'Gettext Source (po)'
extentions = ['.po',]
readOptions = []
writeOptions = []

from polib import escape as po_escape
from polib import unescape as po_unescape



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
            word = po_unescape(line[6:])
            msgstr = False
        elif line.startswith('msgstr '):
            if msgstr:
                log.error('msgid omitted!')
            defi = po_unescape(line[7:])
            msgstr = True
        else:
            if msgstr:
                defi += po_unescape(line)
            else:
                word += po_unescape(line)
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
            po_escape(word),
            po_escape(defi),
        ))
    fp.close()

