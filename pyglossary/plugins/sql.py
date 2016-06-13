# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Sql'
description = 'SQL'
extentions = ['.sql']
readOptions = []
writeOptions = []


def write(glos, filename):
    with open(filename, 'w', encoding='utf-8') as fp:
        for line in glos.iterSqlLines(
            transaction=False,
        ):
            fp.write(line + '\n')
