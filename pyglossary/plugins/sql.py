# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Sql'
description = 'SQL'
extentions = ['.sql']
readOptions = []
writeOptions = [
	'encoding',  # str
]


def write(
	glos,
	filename,
	encoding='utf-8',
):
	with open(filename, 'w', encoding=encoding) as fp:
		for line in glos.iterSqlLines(
			transaction=False,
		):
			fp.write(line + '\n')
