# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Xfardic'
description = 'xFarDic (xdb)'
extentions = ['.xdb', '.xml']
readOptions = []
writeOptions = []

from pyglossary.text_utils import escape, unescape

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
    xdb = XML(open(filename, 'rb').read())
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
            word = toStr(word)
            defi = toStr(defi)
            glos.addEntry(word, defi)
        else:
            log.error('unknown tag %s'%elem.tag)


def write(glos, filename):
    fp = open(filename, 'wb')
    fp.write('<?xml version="1.0" encoding="utf-8" ?>\n<words>\n<xfardic>')
    for item in infoKeys:
        fp.write('<'+item+'>'+str(glos.getInfo(item))+'</'+item+'>')
    fp.write('</xfardic>\n')
    for entry in glos:
        words = entry.getWords()
        word, alts = words[0], words[1:]
        defi = entry.getDefi()
        #fp.write("<word><in>"+word+"</in><out>"+ defi+"</out></word>\n")
        fp.write('<word>\n    <in>%s</in>\n'%escape(word))
        for alt in alts:
            fp.write('    <alt>%s</alt>\n'%escape(alt))
        fp.write('    <out>%s</out>\n</word>\n'%escape(defi))
    fp.write("</words>\n")
    fp.close()


def write_2(glos, filename):
    from xml.sax.saxutils import XMLGenerator
    from xml.sax.xmlreader import AttributesNSImpl
    xdbFp = open(filename, 'wb')
    fp = XMLGenerator(xdbFp, 'utf-8')
    attrs = AttributesNSImpl({}, {})
    fp.startElement(u'xfardic', attrs)
    for t in glos.info:
        fp.startElement(unicode(t[0]), attrs)
        fp.characters(unicode(t[1]))
        fp.endElement(unicode(t[0]))
    fp.endElement(u'xfardic')
    fp.startElement(u'words', attrs)
    for entry in glos:
        word = entry.getWord()
        defi = entry.getDefi()
        try:
            tmpXmlFile.characters(defi)
        except:
            log.exception('While writing xdb file, an error on word "%s":'%word)
            continue
        fp.startElement(u'word', attrs)
        fp.startElement(u'in', attrs)
        fp.characters(unicode(word))
        fp.endElement(u'in')
        fp.startElement(u'out', attrs)
        fp.characters(unicode(defi))
        fp.endElement(u'out')
    fp.endElement(u'words')
    fp.endDocument()
    xdbFp.close()

