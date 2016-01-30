# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Xdxf'
description = 'XDXF'
extentions = ['.xdxf', '.xml']
readOptions = []
writeOptions = []

XML = None
tostring = None


def read(glos, filename):
    ##<!DOCTYPE xdxf SYSTEM "http://xdxf.sourceforge.net/xdxf_lousy.dtd">
    from xml.etree.ElementTree import XML as _XML, tostring as _tostring
    global XML, tostring
    XML = _XML
    tostring = _tostring

    with open(filename, 'rb') as f:
        xdxf = XML(f.read())

    read_metadata(glos, xdxf)
    read_xdxf(glos, xdxf)


def read_metadata(glos, xdxf):
    full_name = tostring(xdxf[0]).replace('<full_name>', '')\
                                 .replace('</full_name>', '')
    description = tostring(xdxf[1]).replace('<description>', '')\
                                   .replace('</description>', '')
    full_name = full_name.strip()
    description = description.strip()
    glos.setInfo('name', full_name)
    glos.setInfo('description', description)


def read_xdxf(glos, xdxf):
    for item in xdxf[2:]:
        word, defi = xdxf_title_defi(item)
        glos.data.append((word, defi))


def xdxf_title_defi(item):
    if len(item) == 2:
        defi = tostring(item[1]).replace('<tr>', '').replace('</tr>', '\n')
        word = tostring(item[0]).replace('<k>', '').replace('</k>', '')
    elif len(item) == 1:
        itemStr = tostring(item[0])
        ki = itemStr.find('</k>')
        defi = itemStr[ki + 4:]
        word = itemStr[:ki].replace('<k>', '')
    word = word.strip()
    defi = defi.strip()
    return word, defi
