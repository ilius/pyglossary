# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = 'Pmd'
description = 'PMD'
extentions = ['.pmd']
readOptions = []
writeOptions = []

import sys, os

faSubs = {
    u'،': (u'،', 1, 'fa_colon', 0x22),
    u'ـ': (u'ـ', 1, 'fa_underline', 0xde), ## 0xde
    u'‌': (u'‌', 1, 'virtual space', None), ## None
    u'ی': (u'ﯼ', 4, 'fa_yeh', 0xd6),
    u'ى': (u'ﯼ', 4, 'fa_yeh2', 0xd6), ## u'\u0649' (arabic yeh, but without dots!)
    u'ا': (u'ﺍ', 2, 'alif', 0x66),
    u'إ': (u'ﺇ', 2, 'alif_down_hamzeh', 0xdc), ## 0x66 0xdc
    u'آ': (u'ﺁ', 2, 'alif_madi', 0x68),
    u'أ': (u'ﺃ', 2, 'alif_up_hamzeh', 0xda), ## 0x66 0xda
    u'ب': (u'ﺏ', 4, 'beh', 0x6a),
    u'پ': (u'ﭖ', 4, 'peh', 0x6e),
    u'ة': (u'ﺓ', 2, 'teh_tanith', 0xe4), ## None 0xe4
    u'ت': (u'ﺕ', 4, 'teh', 0x72),
    u'ث': (u'ﺙ', 4, 'theh', 0x76),
    u'ج': (u'ﺝ', 4, 'jeh', 0x7a),
    u'چ': (u'ﭺ', 4, 'cheh', 0x7e),
    u'ح': (u'ﺡ', 4, 'heh_jim', 0x82),
    u'خ': (u'ﺥ', 4, 'kheh', 0x86),
    u'د': (u'ﺩ', 2, 'dal', 0x8a),
    u'ذ': (u'ﺫ', 2, 'zal', 0x8c),
    u'ر': (u'ﺭ', 2, 'reh', 0x8e),
    u'ز': (u'ﺯ', 2, 'zeh', 0x90),
    u'ژ': (u'ﮊ', 2, 'zheh', 0x92),
    u'س': (u'ﺱ', 4, 'sin', 0x94),
    u'ش': (u'ﺵ', 4, 'shin', 0x98),
    u'ص': (u'ﺹ', 4, 'sad', 0x9c),
    u'ض': (u'ﺽ', 4, 'zad', 0xa0),
    u'ط': (u'ﻁ', 4, 'ta', 0xa4),
    u'ظ': (u'ﻅ', 4, 'za', 0xa8),
    u'ع': (u'ﻉ', 4, 'ein', 0xac),
    u'غ': (u'ﻍ', 4, 'ghein', 0xb0),
    u'ف': (u'ﻑ', 4, 'feh', 0xb4),
    u'ق': (u'ﻕ', 4, 'ghaf', 0xb8),
    u'ك': (u'ﻙ', 4, 'ar_kaf', 0xda), ## 0xbc 0xda
    u'ک': (u'ﮎ', 4, 'fa_kaf', 0xbc),
    u'گ': (u'ﮒ', 4, 'gaf', 0xc0),
    u'ل': (u'ﻝ', 4, 'lam', 0xc4),
    u'م': (u'ﻡ', 4, 'mim', 0xc8),
    u'ن': (u'ﻥ', 4, 'noon', 0xcc),
    u'ه': (u'ﻩ', 4, 'heh', 0xd2),
    u'و': (u'ﻭ', 2, 'vav', 0xd0),
    u'ؤ': (u'ﺅ', 2, 'vav_up_hamzeh', 0xde), ## 0xd0 0xde
    u'ي': (u'ﻱ', 4, 'ar_yeh', 0xe0), ## 0xd6 0xe0
    u'ئ': (u'ﺉ', 4, 'yeh_up_hamzeh', 0x62),
    u'»': (u'»', 1, 'fa_quote_1', 0xd8),
    u'«': (u'«', 1, 'fa_quote_2', 0xd9), ## None 0xd9
}

faHarakat = [u'ّ', u'َ', u'ِ', u'ُ', u'ً', u'ٍ', u'ٌ', u'ْ', u'ٔ', u'ٓ']

def pmdCompile(uni):
    for h in faHarakat:
        uni = uni.replace(h, u'')
    missing = []
    pmd = ''
    en = False
    enStack = u''
    n = len(uni)
    for i in xrange(n):
        ch = uni[i]
        if u'A' <= ch <= u'z' or u'0'<= ch <=u'9':
            enStack = ch + enStack
            continue
        if enStack!=u'':
            pmd += pmdEnConv(enStack)
            enStack = u''
        if not ch in faSubs:
            pmd += pmdEnConv(ch)
            continue
        stickPrev = False
        stickNext = False
        if uni[i] in faSubs:
            if i>0 and uni[i-1] in faSubs and faSubs[uni[i]][1]>1:
                if faSubs[uni[i-1]][1]>3:
                    stickPrev = True
            if i<n-1:
                if uni[i+1] in faSubs and faSubs[uni[i]][1]>3:
                    if faSubs[uni[i+1]][1]>1:
                        stickNext=True
        first = faSubs[ch][3]
        if first==None:
            missing.append(ch)
            continue
        if stickPrev and stickNext:## medial -> substitution 3
            pmd += chr(first+3)
        elif stickPrev and not stickNext:## final -> substitution 1
            pmd += chr(first+1)
        elif not stickPrev and stickNext:## initial -> substitution 2
            pmd += chr(first+2)
        elif not stickPrev and not stickNext:## isolated -> substitution 0
            pmd += chr(first)
        del stickPrev, stickNext, first
    """
    if missing!=[]:
        fp = open(join(homeDir, 'missing.txt'), 'a')
        for ch in missing:
            log.debug(ch.encode('utf-8'))
            #fp.write('%s\n'%ch.encode('utf-8'))
    """
    return pmd

#pmdChars=[None, ' ', '~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '-', '_', '+', '=', '\\', '|', '/', '?', ')', '(', ']', '[', '}', '{', '>', '<', ', ', '.', ': ', ';', '\'', '"', '“', '،', '?']

pmdChars = {
    0: '',
    1: ' ',
    2: '~',
    3: '`',
    4: '!',
    5: '@',
    6: '#',
    7: '$',
    8: '%',
    9: '^',
    10: '&',
    11: '*',
    12: '-',
    13: '_',
    14: '+',
    15: '=',
    16: '\\',
    17: '|',
    18: '/',
    19: '?',
    20: ')',
    21: '(',
    22: ']',
    23: '[',
    24: '}',
    25: '{',
    26: '>',
    27: '<',
    28: ',',
    29: '.',
    30: ': ',
    31: ';',
    32: '\'',
    33: '"',
    34: '،',
    35: '?',
    234: 'ŋ',
    235: 'ɑ',
    236: 'ɒ',
    237: 'ɔ',
    238: 'ə',
    239: 'ɚ',
    240: 'ɛ',
    241: 'ɜ',
    242: 'ɝ',
    243: 'ɪ',
    244: 'ʃ',
    245: 'ʊ',
    246: 'ʌ',
    247: 'ʒ',
    248: 'ˇ',
    249: 'ˌ',
    250: 'ː',
    251: '̃',
    252: 'θ',
    253: 'ᴜ',
    254: 'æ',
    255: 'ð',
}


def pmdEnConv(uni): #gets an unicode(utf-16) string
    pmd=''
    #s = uni.encode('utf-8')
    for uc in uni:
        c = uc.encode('utf-8')
        if c in ('\t', '\n'):
            pmd += '\x01'*2
        elif 'a'<=c<='z':
            pmd += chr(ord(c)-35)
        elif 'A'<=c<='Z':
            pmd += chr(ord(c)-29)
        elif '0'<=c<='9':
            pmd += chr(ord(c)+40)
        else:
            for i in pmdChars.keys():
                if pmdChars[i]==c:
                    pmd += chr(i)
                    break
            else:
                log.debug('no PMD coding for "%s"'%c)
    return pmd

def pmdDecomile(pmd):
    uni = u''
    for c in pmd:
        for sub in list(faSubs):
            if sub[1][3] <= ord(c) < sub[1][3]+sub[1][1]:
                uni+=sub[0]
                break

def read(glos, filename):## not tested ## FIXME
    initCwd = os.getcwd()
    os.chdir(filename)
    indLines = open('index').read().split('\n')[3:]
    n = len(indLines)-1
    for i in xrange(n):
        pmd = open(str(i)).read()
        for part in pmd.split('\x00'):
            sepInd = part.find('\x09')
            if sepInd==-1:
                log.error('error on reading PMD database part %s'%i)
                continue
            word = part[:sepInd]
            defi = part[sepInd+1:]
            glos.addEntry(word, defi)
    os.chdir(initCwd)

def write(glos, filename):
    ## FIXME must be migrated to Glossary structure
    ## no more glos.data
    ## must use `for entry in glos`
    initCwd = os.getcwd()
    if not os.path.isdir(filename):
        os.mkdir(filename)
    os.chdir(filename)
    maxLen = max(
        len(
            entry.getWord() + entry.getDefi()
        ) for entry in glos
    )
    indexFp = open('index', 'wb')
    wordCount = len(glos)
    indexFp.write('%s\n'%wordCount)
    size = 200
    (d, m) = divmod(wordCount, size)
    if m > 0:
        k2 = d-1
    else:
        k2 = d
    indexFp.write('%s\n'%275) #???????
    indexFp.write('%s\n'%(d-1))
    ui = glos.ui
    for k in xrange(k2):
        i = k * size
        indexFp.write('%s\t%s\n'%(glos.data[i][0], i+1))
        fp = open(str(k), 'wb')
        for j in xrange(i, i+s):
            fp.write('%s\x09%s\x00'%(
                glos.data[j][0],
                pmdCompile(glos.data[j][1].decode('utf-8')),
            ))
        fp.close()
        if ui:
            rat = float(k)/(k2+1)
    indexFp.write(glos.data[-1][0])
    indexFp.close()
    fp = open(str(d), 'wb')
    for j in xrange(d*s, wordCount):
        fp.write('%s\x09%s\x00'%(
            glos.data[j][0],
            pmdCompile(glos.data[j][1].decode('utf-8')),
        ))
    fp.close()
    os.chdir(initCwd)

