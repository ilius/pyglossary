# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Freedict'
description = 'FreeDict (tei)'
extentions = ['.tei']
readOptions = []


def write(glos, filename):
    fp = open(filename, 'w')

    fp.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE TEI.2 PUBLIC "-//TEI P3//DTD Main Document Type//EN"
"/usr/share/sgml/tei-3/tei2.dtd" [
<!ENTITY %% TEI.dictionaries "INCLUDE" > ]>
<tei.2>
<teiHeader>
<fileDesc>
<titleStmt>
    <title>%s</title>
    <respStmt><resp>converted with</resp><name>PyGlossary</name></respStmt>
</titleStmt>
<publicationStmt><p>freedict.de</p></publicationStmt>
<sourceDesc><p>%s</p></sourceDesc>
</fileDesc>
</teiHeader>
<text><body>''' % (glos.getInfo('title'), filename))

    for entry in glos:
        word = entry.getWord()
        defi = entry.getDefi()
        fp.write('''<entry>
<form><orth>%s</orth></form>
<gramgrp><pos>n</pos></gramgrp>
<trans><tr>%s</tr></trans>
</entry>''' % (word, defi))
    fp.write('</body></text></tei.2>')
    fp.close()
