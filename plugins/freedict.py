#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Freedict'
description = 'FreeDict (tei)'
extentions = ('.tei',)
readOptions = ()

def write(glos, filename):
  fp = open(filename, 'wb')
  fp.write('<?xml version="1.0" encoding="UTF-8"?>\n'+
  '<!DOCTYPE TEI.2 PUBLIC "-//TEI P3//DTD Main Document Type//EN"\n'
  '"/usr/share/sgml/tei-3/tei2.dtd" [\n<!ENTITY % TEI.dictionaries "INCLUDE" > ]>\n'+
  '<tei.2>\n<teiHeader>\n<fileDesc>\n  <titleStmt>\n    <title>%s</title>\n'%glos.getInfo('title')+
  '    <respStmt><resp>converted with</resp><name>PyGlossary</name></respStmt>\n  </titleStmt>\n'+
  '  <publicationStmt><p>freedict.de</p></publicationStmt>\n'+
  '  <sourceDesc><p>%s</p></sourceDesc>\n</fileDesc>\n</teiHeader>\n<text><body>'%filename)


  fp.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE TEI.2 PUBLIC "-//TEI P3//DTD Main Document Type//EN"
"/usr/share/sgml/tei-3/tei2.dtd" [
<!ENTITY % TEI.dictionaries "INCLUDE" > ]>
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
<text><body>'''%(glos.getInfo('title'), filename))

  for item in glos.data:
    fp.write('''<entry>
<form><orth>%s</orth></form>
<gramgrp><pos>n</pos></gramgrp>
<trans><tr>%s</tr></trans>
</entry>'''%item[:2])
  fp.write('</body></text></tei.2>')
  fp.close()

