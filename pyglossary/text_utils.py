# -*- coding: utf-8 -*-
## text_utils.py
##
## Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3, or (at your option)
## any later version.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

import string
import sys
import os
import time
import re

import subprocess

import html.entities
##from xml.etree.ElementTree import XML, tostring ## used for xml2dict

import logging
log = logging.getLogger('root')


from . import core


startRed = '\x1b[31m'
endFormat = '\x1b[0;0;0m' ## len=8

## ascii spacial characters.
schAs = [
    "\n",
    ",", ".", ':', ';',
    "[", "]",
    "(", ")",
    '-', '+', '=',
    '/',
    '\\',
    "'", '"', '`',
    '_',
    '!', '?',
    '*', '@', '#',
]

digitsFa = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

## persian spacial characters.
schFa = [
    '\xd8\x9b',
    '\xd8\x9f',
    '\xe2\x80\xa6',
    '\xc2\xab',
    '\xc2\xbb',
    '\xd9\x80',
    '\xd9\x94',
    '\xd8\x8c',
    '\xe2\x80\x93',
    '\xe2\x80\x9c',
    '\xe2\x80\x9d',
    '\xe2\x80\x8c',
]
commaFa = '\xd8\x8c'

## other unicode spacial characters.
schUn = ['\xee\x80\x8a', '\xee\x80\x8c']

sch = schAs + schFa + schUn + list(string.whitespace) + list(string.digits) + digitsFa

toBytes = lambda s: bytes(s, 'utf8') if isinstance(s, str) else bytes(s)
toStr = lambda s: str(s, 'utf8') if isinstance(s, bytes) else str(s)

fixUtf8 = lambda st: toBytes(st).replace(b'\x00', b'').decode('utf-8', 'replace')

pattern_n_us = re.compile(r'((?<!\\)(?:\\\\)*)\\n')
pattern_t_us = re.compile(r'((?<!\\)(?:\\\\)*)\\t')
pattern_bar_us = re.compile(r'((?<!\\)(?:\\\\)*)\\\|')
pattern_bar_sp = re.compile(r'(?:(?<!\\)(?:\\\\)*)\|')

def escapeNTB(st, bar=True):
    """
        scapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)
    """
    st = st.replace(r'\\', r'\\\\')
    st = st.replace('\t', r'\t')
    st = st.replace('\n', r'\n')
    if bar:
        st = st.replace('|', r'\|')
    return st

def unescapeNTB(st, bar=False):
    """
        unscapes Newline, Tab, Baskslash, and vertical Bar (if bar=True)
    """
    st = re.sub(pattern_n_us, '\\1\n', st)
    st = re.sub(pattern_t_us, '\\1\t', st)
    if bar:
        st = re.sub(pattern_bar_us, r'\1\|', st)
    #st = re.sub(r'\\\\', r'\\', st)
    st = st.replace('\\\\', '\\')## probably faster than re.sub
    return st

def splitByBarUnescapeNTB(st):
    """
        splits by '|' (and not '\\|') then unescapes Newline (\\n), Tab (\\t), Baskslash (\\) and Bar (\\|) in each part
        returns a list
    """
    return [
        unescapeNTB(part, bar=True)
        for part in re.split(pattern_bar_sp, st)
    ]



# return a message string describing the current exception
def excMessage():
    i = sys.exc_info()
    return '{0}: {1}'.format(i[0].__name__, i[1])

def formatHMS(h, m, s):
    if h==0:
        if m==0:
            return '%.2d'%s
        else:
            return '%.2d:%.2d'%(m, s)
    else:
        return '%.2d:%.2d:%.2d'%(h, m, s)

def timeHMS(seconds):
    (h, m, s) = time.gmtime(int(seconds))[3:6]
    return formatHMS(h, m, s)

def relTimeHMS(seconds):
    (days, s) = divmod(int(seconds), 24*3600)
    (m, s) = divmod(s, 60)
    (h, m) = divmod(m, 60)
    return formatHMS(h, m, s)

def addDefaultOptions(opt, defOpt, escapeList=None):
    if escapeList is None:
        escapeList = [None, 'Unknown', 'unknown']
    # Two varable opt(meaning options) and defOpt(meaning defaults options) have dict type.
    # this function sets options to defaults if they have not defined
    # or have special values (in escapeList)
    # modifies opt variable an reuturns nothing
    for item in defOpt.keys():
        if item in opt:
            if not opt[item] in escapeList:
                continue
        opt[item] = defOpt[item]

def mergeLists(lists):
    if not isinstance(lists, (list, tuple)):
        raise TypeError('bad type given to mergeLists: %s'%type(lists))
    """
    for i in xrange(len(lists)):
        item = lists[i]
        if not isinstance(item, (list, tuple)):
            raise TypeError('argument give to mergeLists() at index %d is: \'%s\' ,bad type: \'%s\'' % (i, item, type(item)))
    """
    if len(lists)==0:
        return []
    elif len(lists)==1:
        if isinstance(lists[0], (list, tuple)):
            return lists[0][:]
        else:
            return lists[0]
    else:
        return lists[0] + mergeLists(lists[1:])

def findAll(st, sub):
    ind = []
    if isinstance(sub, str):
        i = 0
        sbl = len(sub)
        while True:
            i = st.find(sub, i)
            if i==-1:
                break
            ind.append(i)
            i += sbl
    elif isinstance(sub, (list, tuple)):
        for item in sub:
            ind += findAll(st, item)
        ind.sort()
    else:
        log.error('Invailed second argument to function findAll!')
        return []
    return ind

def checkOrder(lst):
    wrong = []
    for i in range(len(lst)-1):
        if lst[i] == lst[i+1]:
            wrong.append(i)
    return wrong

def removeRepeats(lst):
    ## gets a sorted list and removes any reapeated member. returns result.
    n = len(lst)
    if n==0:
        return []
    lstR=[lst[0]]
    for i in range(1, n):
        if lst[i] != lst[i-1]:
            lstR.append(lst[i])
    return lstR

def addWord(word, allWords):
        if len(allWords)==0:
            return [word]
        i = locate(allWords, word)
        ii = int(i+1)
        if ii-i == 0.5:
            allWords.insert(ii, word)
        return allWords

def findWords(st0, opt=None):
    if opt is None:
        opt = {}
    # take all words of a text
    # and returns their indexes as a list.
    defOpt = {'minLen':3, 'noEn':True}
    addDefaultOptions(opt, defOpt)
    st = st0[:]
    ind = []
    for ch in sch:
        st = st.replace(ch, ' '*len(ch))
    if len(st)!=len(st0):
        log.error('Error in function text_utlis.findWord. string length has been changed!')
        return []
    si = [-1] + findAll(st, ' ') + [len(st)] # separatior indexes
    for i in range(len(si)-1):
        word = st[si[i]+1:si[i+1]]
        if word.strip()=='':
            continue
        if 'word' in opt:
            if word != opt['word']:
                continue
        if len(word) < opt['minLen']:
            continue
        if opt['noEn']:
            en = False
            for c in word:
                if c in string.printable:
                    en = True
            if en:
                continue
        ind.append((si[i]+1, si[i+1]))
    return ind

def takeStrWords(st, opt=None):
    if opt is None:
        opt = {}
    ## take all words of a text
    ## and returns them as a list of strings.
    defOpt = {'minLen':3, 'noEn':True, 'sort':True, 'noRepeat':True}
    addDefaultOptions(opt, defOpt)
    words = [st[i:j] for i, j in findWords(st, opt)]
    ## 'sort' and 'noRepeat' options will not be used in findWords()
    if opt['sort']:
        words.sort()
    if opt['noRepeat']:
        words = removeRepeats(words)
    return words

def takeFileWords(filePath, opt=None):
    if opt is None:
        opt = {
            'minLen': 3,
            'sort': True,
            'noRepeat': True,
        }
    try:
        fp = open(filePath, 'rb')
    except:
        log.exception('error while opening file "%s"'%filePath)
    return takeStrWords(fp.read(), opt)



def relation(word, phrase, opt=None):## FIXME
    if opt is None:
        opt = {}
    defOpt={'sep':commaFa, 'matchWord':True}
    addDefaultOptions(opt, defOpt)
    if phrase.find(word)==-1:
        return 0.0
    phraseParts = phrase.split(opt['sep'])
    rel = 0.0 ## relation value of word to pharse(as a float number between 0 and 1
    for part0 in phraseParts:
        for ch in sch:
            part = part0.replace(ch, ' ')
        pRel = 0 ## part relation
        if opt['matchWord']:
            pNum = 0
            partWords = takeStrWords(part)
            pLen = len(partWords)
            if pLen==0:
                continue
            for pw in partWords:
                if pw==word:
                    pNum += 1
            pRel = float(pNum)/pLen ## part relation
        else:
            pLen = len(part.replace(' ', ''))
            if pLen==0:
                continue
            pNum = len(findAll(part, st)*len(st))
            pRel = float(pNum)/pLen ## part relation
        if pRel > rel:
            rel = pRel
        #del pRel
    return rel

###############################################

## Python 3.x:
def intToBinStr(n, stLen=0):
    bs = []
    while n>0:
        bs.insert(0, n & 0xff)
        n >>= 8
    return bytes(bs).rjust(stLen, b'\x00')

## Python 3.x:
def binStrToInt(bs):
    bs = toBytes(bs)
    n = 0
    for c in bs:
        n = (n << 8) + c
    return n



###############################################

def chBaseIntToList(number, base):
    result = []
    if number < 0:
        raise ValueError('number must be posotive integer')
    while True:
        number, rdigit = divmod(number, base)
        result = [rdigit] + result
        if number == 0:
            return result


def recodeToWinArabic(s):
    u = s.decode('utf8', 'replace')
    replaceList = [
        ('ی', 'ي'),
        ('ک', 'ك'),
        ('ٔ', 'ء'),
        ('\xef\xbf\xbd', ''),
    ] + [(chr(i), chr(i+144)) for i in range(1632, 1642)]
    for item in replaceList:
        u = u.replace(item[0], item[1])
    return u.encode('windows-1256', 'replace')



def urlToPath(url):
    if not url.startswith('file://'):
        return url
    path = url[7:]
    if path[-2:]=='\r\n':
        path = path[:-2]
    elif path[-1]=='\r':
        path = path[:-1]
    ## here convert html unicode symbols to utf8 string:
    if not '%' in path:
        return path
    path2 = ''
    n = len(path)
    i = 0
    while i<n:
        if path[i]=='%' and i<n-2:
            path2 += chr(eval('0x%s'%path[i+1:i+3]))
            i += 3
        else:
            path2 += path[i]
            i += 1
    return path2



replacePostSpaceChar = lambda st, ch: st.replace(' '+ch, ch).replace(ch, ch+' ').replace(ch+'  ', ch+' ')


def my_url_show(link):
    for path in (
        '/usr/bin/gnome-www-browser',
        '/usr/bin/firefox',
        '/usr/bin/iceweasel',
        '/usr/bin/konqueror',
    ):
        if os.path.isfile(path):
            subprocess.call([path, link])
            break
"""
try:
    from gnome import url_show
except:
    try:
        from gnomevfs import url_show
    except:
        url_show = my_url_show
"""
def click_website(widget, link):
    my_url_show(link)

def runDictzip(filename):
    dictzipCmd = '/usr/bin/dictzip' ## Save in pref ## FIXME
    if not os.path.isfile(dictzipCmd):
        return False
    if filename[-4:]=='.ifo':
        filename = filename[:-4]
    (out, err) = subprocess.Popen(
        [dictzipCmd, filename+'.dict'],
        stdout=subprocess.PIPE
    ).communicate()
    #out = p3[1].read()
    #err = p3[2].read()
    #log.debug('dictzip command: "%s"'%dictzipCmd)
    #if err:
    #    log.error('dictzip error: %s'%err.replace('\n', ' '))
    #if out!='':
    #    log.error('dictzip error: %s'%out.replace('\n', ' '))


def isControlChar(y):
    ## y: char code
    if y < 32 and chr(y) not in '\t\n\r\v':
        return True
    ## according to ISO-8859-1
    if 128 <= y <= 159:
        return True
    return False

def isASCII(data, exclude=None):
    if exclude is None:
        exclude = []
    for c in data:
        co = ord(c)
        if co >= 128 and co not in exclude:
            return False
    return True

def formatByteStr(text):
    out = ''
    for c in text:
        out += '{0:0>2x}'.format(ord(c)) + ' '
    return out

html_entity2str = {
    'ldash': '–',
    'acirc': 'â',
    'ecirc': 'ê',
    'icirc': 'î',
    'ocirc': 'ô',
    'ucirc': 'û',
    'ycirc': 'ŷ',
    'uring': 'ů',
    'wring': 'ẘ',
    'yring': 'ẙ',
    'agrave': 'à',
    'egrave': 'è',
    'igrave': 'ì',
    'ograve': 'ò',
    'ugrave': 'ù',
    'ygrave': 'ỳ',
    'atilde': 'ã',
    'etilde': 'ẽ',
    'itilde': 'ĩ',
    'otilde': 'õ',
    'utilde': 'ũ',
    'ytilde': 'ỹ',
    'auml': 'ӓ',
    'euml': 'ë',
    'iuml': 'ï',
    'ouml': 'ö',
    'uuml': 'ü',
    'yuml': 'ÿ',
    'ccedil': 'ç',
    'aelig': 'æ',
    'eth': 'ð',
    'pound': '£',
    'deg': '°',
    'divide': '÷',
    'frac12': '½',
    'frac13': '⅓',
    'frac14': '¼',
    'frac23': '⅔',
    'frac34': '¾',
    'xfrac13': '⅓',
    'hearts': '♥',
    'diams': '♦',
    'spades': '♠',
    'clubs': '♣'
}

## Use build_name2codepoint_dict function to update this dictionary
name2codepoint = {
    'aring': 0x00c5, # Å
    'gt': 0x003e, # >
    'sup': 0x2283, # ⊃
    'ge': 0x2265, # ≥
    'upsih': 0x03d2, # ϒ
    'asymp': 0x2248, # ≈
    'radic': 0x221a, # √
    'otimes': 0x2297, # ⊗
    'aelig': 0x00c6, # Æ
    'sigmaf': 0x03c2, # ς
    'lrm': 0x200e, # ‎
    'cedil': 0x00b8, # ¸
    'kappa': 0x03ba, # κ
    'wring': 0x1e98, # ẘ
    'prime': 0x2032, # ′
    'lceil': 0x2308, # ⌈
    'iquest': 0x00bf, # ¿
    'shy': 0x00ad, # ­
    'sdot': 0x22c5, # ⋅
    'lfloor': 0x230a, # ⌊
    'brvbar': 0x00a6, # ¦
    'egrave': 0x00c8, # È
    'sub': 0x2282, # ⊂
    'iexcl': 0x00a1, # ¡
    'ordf': 0x00aa, # ª
    'sum': 0x2211, # ∑
    'ntilde': 0x00f1, # ñ
    'atilde': 0x00e3, # ã
    'theta': 0x03b8, # θ
    'equiv': 0x2261, # ≡
    'nsub': 0x2284, # ⊄
    'omicron': 0x039f, # Ο
    'yuml': 0x0178, # Ÿ
    'thinsp': 0x2009, #  
    'ecirc': 0x00ca, # Ê
    'bdquo': 0x201e, # „
    'frac23': 0x2154, # ⅔
    'emsp': 0x2003, #  
    'permil': 0x2030, # ‰
    'eta': 0x0397, # Η
    'forall': 0x2200, # ∀
    'eth': 0x00d0, # Ð
    'rceil': 0x2309, # ⌉
    'ldash': 0x2013, # –
    'divide': 0x00f7, # ÷
    'igrave': 0x00cc, # Ì
    'pound': 0x00a3, # £
    'frasl': 0x2044, # ⁄
    'zeta': 0x03b6, # ζ
    'lowast': 0x2217, # ∗
    'chi': 0x03a7, # Χ
    'cent': 0x00a2, # ¢
    'perp': 0x22a5, # ⊥
    'there4': 0x2234, # ∴
    'pi': 0x03c0, # π
    'empty': 0x2205, # ∅
    'euml': 0x00cb, # Ë
    'notin': 0x2209, # ∉
    'uuml': 0x00fc, # ü
    'icirc': 0x00ee, # î
    'bull': 0x2022, # •
    'upsilon': 0x03a5, # Υ
    'ensp': 0x2002, #  
    'ccedil': 0x00c7, # Ç
    'cap': 0x2229, # ∩
    'mu': 0x03bc, # μ
    'deg': 0x00b0, # °
    'tau': 0x03c4, # τ
    'nabla': 0x2207, # ∇
    'ucirc': 0x00db, # Û
    'ugrave': 0x00f9, # ù
    'cong': 0x2245, # ≅
    'quot': 0x0022, # "
    'uacute': 0x00da, # Ú
    'acirc': 0x00c2, # Â
    'sim': 0x223c, # ∼
    'phi': 0x03a6, # Φ
    'diams': 0x2666, # ♦
    'minus': 0x2212, # −
    'euro': 0x20ac, # €
    'thetasym': 0x03d1, # ϑ
    'iuml': 0x00cf, # Ï
    'sect': 0x00a7, # §
    'ldquo': 0x201c, # “
    'hearts': 0x2665, # ♥
    'oacute': 0x00f3, # ó
    'zwnj': 0x200c, # ‌
    'yen': 0x00a5, # ¥
    'ograve': 0x00d2, # Ò
    'uring': 0x016f, # ů
    'trade': 0x2122, # ™
    'nbsp': 0x00a0, #  
    'tilde': 0x02dc, # ˜
    'itilde': 0x0129, # ĩ
    'oelig': 0x0153, # œ
    'xfrac13': 0x2153, # ⅓
    'le': 0x2264, # ≤
    'auml': 0x00e4, # ä
    'cup': 0x222a, # ∪
    'otilde': 0x00f5, # õ
    'lt': 0x003c, # <
    'ndash': 0x2013, # –
    'sbquo': 0x201a, # ‚
    'real': 0x211c, # ℜ
    'psi': 0x03c8, # ψ
    'rsaquo': 0x203a, # ›
    'darr': 0x2193, # ↓
    'not': 0x00ac, # ¬
    'amp': 0x0026, # &
    'oslash': 0x00f8, # ø
    'acute': 0x00b4, # ´
    'zwj': 0x200d, # ‍
    'alefsym': 0x2135, # ℵ
    'sup3': 0x00b3, # ³
    'rdquo': 0x201d, # ”
    'laquo': 0x00ab, # «
    'micro': 0x00b5, # µ
    'ygrave': 0x1ef3, # ỳ
    'szlig': 0x00df, # ß
    'clubs': 0x2663, # ♣
    'agrave': 0x00e0, # à
    'harr': 0x2194, # ↔
    'frac14': 0x00bc, # ¼
    'frac13': 0x2153, # ⅓
    'frac12': 0x00bd, # ½
    'utilde': 0x0169, # ũ
    'prop': 0x221d, # ∝
    'circ': 0x02c6, # ˆ
    'ocirc': 0x00f4, # ô
    'uml': 0x00a8, # ¨
    'prod': 0x220f, # ∏
    'reg': 0x00ae, # ®
    'rlm': 0x200f, # ‏
    'ycirc': 0x0177, # ŷ
    'infin': 0x221e, # ∞
    'etilde': 0x1ebd, # ẽ
    'mdash': 0x2014, # —
    'uarr': 0x21d1, # ⇑
    'times': 0x00d7, # ×
    'rarr': 0x21d2, # ⇒
    'yring': 0x1e99, # ẙ
    'or': 0x2228, # ∨
    'gamma': 0x03b3, # γ
    'lambda': 0x03bb, # λ
    'rang': 0x232a, # 〉
    'xi': 0x039e, # Ξ
    'dagger': 0x2021, # ‡
    'image': 0x2111, # ℑ
    'hellip': 0x2026, # …
    'sube': 0x2286, # ⊆
    'alpha': 0x03b1, # α
    'plusmn': 0x00b1, # ±
    'sup1': 0x00b9, # ¹
    'sup2': 0x00b2, # ²
    'frac34': 0x00be, # ¾
    'oline': 0x203e, # ‾
    'loz': 0x25ca, # ◊
    'iota': 0x03b9, # ι
    'iacute': 0x00cd, # Í
    'para': 0x00b6, # ¶
    'ordm': 0x00ba, # º
    'epsilon': 0x03b5, # ε
    'weierp': 0x2118, # ℘
    'part': 0x2202, # ∂
    'delta': 0x03b4, # δ
    'copy': 0x00a9, # ©
    'scaron': 0x0161, # š
    'lsquo': 0x2018, # ‘
    'isin': 0x2208, # ∈
    'supe': 0x2287, # ⊇
    'and': 0x2227, # ∧
    'ang': 0x2220, # ∠
    'curren': 0x00a4, # ¤
    'int': 0x222b, # ∫
    'rfloor': 0x230b, # ⌋
    'crarr': 0x21b5, # ↵
    'exist': 0x2203, # ∃
    'oplus': 0x2295, # ⊕
    'piv': 0x03d6, # ϖ
    'ni': 0x220b, # ∋
    'ne': 0x2260, # ≠
    'lsaquo': 0x2039, # ‹
    'yacute': 0x00fd, # ý
    'nu': 0x03bd, # ν
    'macr': 0x00af, # ¯
    'larr': 0x2190, # ←
    'aacute': 0x00e1, # á
    'beta': 0x03b2, # β
    'fnof': 0x0192, # ƒ
    'rho': 0x03c1, # ρ
    'eacute': 0x00e9, # é
    'omega': 0x03c9, # ω
    'middot': 0x00b7, # ·
    'lang': 0x2329, # 〈
    'spades': 0x2660, # ♠
    'rsquo': 0x2019, # ’
    'thorn': 0x00fe, # þ
    'ouml': 0x00f6, # ö
    'raquo': 0x00bb, # »
    'sigma': 0x03c3, # σ
    'ytilde': 0x1ef9, # ỹ
}

def build_name2codepoint_dict():
    """
        Builds name to codepoint dictionary
        copy and paste the output to the name2codepoint dictionary
        name2str - name to utf-8 string dictionary
    """
    name2str = html_entity2str
    for k, v in html.entities.name2codepoint.items():
        name2str[k.lower()] = chr(v).encode('utf-8')
    for key in sorted(name2str.keys()):
        value = name2str[key]
        log.info("    '{0}': 0x{1:0>4x}, # {2}".format(
            key,
            ord(value.decode('utf-8')),
            value,
        ))

if __name__=='__main__':
    build_name2codepoint_dict()

