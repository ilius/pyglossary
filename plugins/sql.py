#!/usr/bin/python
# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Sql'
description = 'SQL'
extentions = ['.sql']
readOptions = []
writeOptions = []

def write(glos, filename):
  from xml.sax.saxutils import XMLGenerator
  from xml.sax.xmlreader import AttributesNSImpl
  open(filename, 'wb').write('\n'.join(glos.getSqlLines()))



