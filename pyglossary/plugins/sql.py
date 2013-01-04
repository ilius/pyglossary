# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Sql'
description = 'SQL'
extentions = ['.sql']
readOptions = []
writeOptions = []

def write(glos, filename):
    open(filename, 'wb').write('\n'.join(glos.getSqlLines()))



