# -*- coding: utf-8 -*-

from formats_common import *

enable = False
format = 'Test'
description = 'Test Format File(.test)'
extentions = ['.test', '.tst']
readOptions = []
writeOptions = []


def read(glos, filename):  # glos is a Glossary object, filename is a string
    log.info('reading from format %s using plugin' % format)
    count = 100
    # get number of entries from input file(depending on your format)
    for i in range(count):
        # here get word and definition from file(depending on your format)
        word = 'word_%s' % i
        defi = 'definition %s' % i
        glos.addEntry(word, defi)
    # here read info from file and set to Glossary object
    glos.setInfo('name', 'Test')
    glos.setInfo('descriptin', 'Test glossary craeted by a PyGlossary plugin')
    glos.setInfo('author', 'Me')
    glos.setInfo('copyright', 'GPL')
    return True  # reading input file was succesfull


def write(glos, filename):  # glos is a Glossary object, filename is a string
    log.info('writing to format %s using plugin' % format)
    for entry in glos:
        word = entry.getWord()
        defi = entry.getDefi()
        # here write word and defi to the output file (depending on
        # your format)
    # here read info from Glossaey object
    name = glos.getInfo('name')
    descriptin = glos.getInfo('descriptin')
    author = glos.getInfo('author')
    copyright = glos.getInfo('copyright')
    # if an info key doesn't exist, getInfo returns empty string
    # now write info to the output file (depending on your output format)
    return True  # writing output file was succesfull
