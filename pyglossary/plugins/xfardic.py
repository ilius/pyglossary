# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Xfardic'
description = 'xFarDic (xdb)'
extentions = ['.xdb', '.xml']
readOptions = []
writeOptions = []


infoKeys = (
    'dbname',
    'author',
    'inputlang',
    'version',
    'outputlang',
    'copyright',
    'description',
)

def read(glos, filename):
    from xml.etree.ElementTree import XML, tostring
    from pyglossary.xml_utils import xml_unescape
    with open(filename, 'r') as fp:
        xdb = XML(fp.read())
    for elem in xdb:
        if elem.tag == 'xfardic':## first element
            for infoElem in elem:
                if infoElem.text:
                    glos.setInfo(infoElem.tag, infoElem.text)
        elif elem.tag == 'word':
            word = elem[0].text
            defi = elem[1].text
            if not word:
                continue
            word = xml_unescape(word)
            defi = xml_unescape(defi)
            glos.addEntry(word, defi)
        else:
            log.error('unknown tag %s'%elem.tag)


def write(glos, filename):
    from pyglossary.xml_utils import xml_escape
    fp = open(filename, 'w')
    fp.write('<?xml version="1.0" encoding="utf-8" ?>\n<words>\n<xfardic>')
    for item in infoKeys:
        fp.write('<'+item+'>'+str(glos.getInfo(item))+'</'+item+'>')
    fp.write('</xfardic>\n')
    for entry in glos:
        words = entry.getWords()
        word, alts = words[0], words[1:]
        defi = entry.getDefi()
        #fp.write("<word><in>"+word+"</in><out>"+ defi+"</out></word>\n")
        fp.write('<word>\n    <in>%s</in>\n'%xml_escape(word))
        for alt in alts:
            fp.write('    <alt>%s</alt>\n'%xml_escape(alt))
        fp.write('    <out>%s</out>\n</word>\n'%xml_escape(defi))
    fp.write("</words>\n")
    fp.close()


def write_2(glos, filename):
    from xml.sax.saxutils import XMLGenerator
    from xml.sax.xmlreader import AttributesNSImpl
    xdbFp = open(filename, 'wb')
    fp = XMLGenerator(xdbFp, 'utf-8')
    attrs = AttributesNSImpl({}, {})
    fp.startElement('xfardic', attrs)
    for t in glos.info:
        fp.startElement(str(t[0]), attrs)
        fp.characters(str(t[1]))
        fp.endElement(str(t[0]))
    fp.endElement('xfardic')
    fp.startElement('words', attrs)
    for entry in glos:
        word = entry.getWord()
        defi = entry.getDefi()
        try:
            tmpXmlFile.characters(defi)
        except:
            log.exception('While writing xdb file, an error on word "%s":'%word)
            continue
        fp.startElement('word', attrs)
        fp.startElement('in', attrs)
        fp.characters(str(word))
        fp.endElement('in')
        fp.startElement('out', attrs)
        fp.characters(str(defi))
        fp.endElement('out')
    fp.endElement('words')
    fp.endDocument()
    xdbFp.close()

