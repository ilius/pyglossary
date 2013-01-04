# -*- coding: utf-8 -*-

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
    fp = open(filename, 'rb')
    glos.data = []
    xdbText = fp.read()
    i = 0
    for item in infoKeys:################## method should be changed
        inf0 = xdbText.find('<'+item+'>', i)
        if inf0==-1:
            continue
        inf0 += (len(item)+2)
        inf1 = xdbText.find('</'+item+'>', inf0)
        inf = unescape(xdbText[inf0:inf1])
        glos.setInfo(item, inf)
        i = inf1
    while True:######################################################
        i = xdbText.find('<word>', i)
        if i==-1:
            break
        in0 = xdbText.find('<in>', i) + 4
        in1 = xdbText.find('</in>', in0)
        out0= xdbText.find('<out>', in1) + 5
        out1= xdbText.find('</out>', out0)
        word = unescape(xdbText[in0:in1])
        defi = unescape(xdbText[out0:out1])
        glos.data.append((word, defi))
        #i = out1
        i = xdbText.find('</word>', out1) + 7



def read_2(glos, filename):
    from xml.etree.ElementTree import XML, tostring
    fp = open(filename, 'rb')
    glos.data = []
    glos.info = {}
    xdb = XML(fp.read())
    del fp
    for elem in xdb[0]:
        et = tostring(elem)
        i0 = et.find('<')
        i1 = et.find('>',i0+1)
        i2 = et.find('<',i1+1)
        glos.info[et[i0:i1]] = et[i1+1:i2]
    for elem in xdb[1:]:
        try:
            w, m = tostring(elem[0]), tostring(elem[1])
        except:
            myRaise(__file__)
            printAsError(tostring(elem))
            continue
        glos.data += [[ w[4:-5] , m[5:-6] ]]



def write(glos, filename):
    fp = open(filename, 'wb')
    fp.write('<?xml version="1.0" encoding="utf-8" ?>\n<words>\n<xfardic>')
    for item in infoKeys:
        fp.write('<'+item+'>'+str(glos.getInfo(item))+'</'+item+'>')
    fp.write('</xfardic>\n')
    for item in glos.data:
        #fp.write("<word><in>"+item[0]+"</in><out>"+ item[1]+"</out></word>\n")
        fp.write('<word>\n    <in>%s</in>\n'%escape(item[0]))
        try:
            alts = item[2]['alts']
        except:
            pass
        else:
            for alt in alts:
                fp.write('    <alt>%s</alt>\n'%escape(alt))
        fp.write('    <out>%s</out>\n</word>\n'%escape(item[1]))
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
    for item in glos.data:
        try:
            tmpXmlFile.characters(item[1])
        except:
            myRaise(__file__)
            printAsError('While writing xdb file, an error on word "%s"'%item[0])
            continue
        fp.startElement(u'word', attrs)
        fp.startElement(u'in', attrs)
        fp.characters(unicode(item[0]))
        fp.endElement(u'in')
        fp.startElement(u'out', attrs)
        fp.characters(unicode(item[1]))
        fp.endElement(u'out')
    fp.endElement(u'words')
    fp.endDocument()
    xdbFp.close()

