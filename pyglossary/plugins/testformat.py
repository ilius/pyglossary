# -*- coding: utf-8 -*-

enable = False
format = 'Test'
description = 'Test Format File(.test)'
extentions = ['.test', '.tst']
readOptions = []
writeOptions = []

def read(glos, filename): ## glos is a Glossary object, filename is a string
    print('reading from format %s using plugin'%format)
    glos.data = []
    count = 100 ## get number of entries from input file(depending on your format)
    for i in range(count):
        ## here get word and meaning from file(depending on your format)
        word = 'word_%s'%i
        mean = 'meaning %s'%i
        glos.data.append([word,mean])
    ## here read info from file and set to Glossary object
    glos.setInfo('name', 'Test')
    glos.setInfo('descriptin', 'Test glossary craeted by a PyGlossary plugin')
    glos.setInfo('author', 'Me')
    glos.setInfo('copyright', 'GPL')
    return True ## reading input file was succesfull


def write(glos, filename): ## glos is a Glossary object, filename is a string
    print('writing to format %s using plugin'%format)
    count = len(glos.data)
    for i in range(count):
        word = glos.data[i][0]
        mean = glos.data[i][1]
        ## here write word and mean to the output file (depending on your format)
    ## here read info from Glossaey object
    name = glos.getInfo('name')
    descriptin = glos.getInfo('descriptin')
    author = glos.getInfo('author')
    copyright = glos.getInfo('copyright')
    ## if an info key doesn't exist, getInfo returns empty string
    ## now write info to the output file (depending on your output format)
    return True ## writing output file was succesfull


