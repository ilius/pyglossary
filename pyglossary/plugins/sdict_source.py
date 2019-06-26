# -*- coding: utf-8 -*-
# Source Glossary for "Sdictionary" (http://sdict.org)
# It has extension '.sdct'

from formats_common import *

enable = True
format = 'SdictSource'
description = 'Sdictionary Source (sdct)'
extensions = ['.sdct']
optionsProp = {
	"writeInfo": BoolOption(),
	"newline": NewlineOption(),
	"resources": BoolOption(),
}
depends = {}


def write(
	glos,
	filename,
	writeInfo=True,
	newline='\n',
	resources=True,
):
	head = ''
	if writeInfo:
		head += '<header>\n'
		head += 'title = %s\n' % glos.getInfo('name')
		head += 'author = %s\n' % glos.getInfo('author')
		head += 'description = %s\n' % glos.getInfo('description')
		head += 'w_lang = %s\n' % glos.getInfo('inputlang')
		head += 'a_lang = %s\n' % glos.getInfo('outputlang')
		head += '</header>\n#\n#\n#\n'
	glos.writeTxt(
		'___',
		'\n',
		filename,
		writeInfo=False,
		rplList=(
			('\n', '<BR>'),
		),
		ext='.sdct',
		head=head,
		newline=newline,
		resources=resources,
	)
