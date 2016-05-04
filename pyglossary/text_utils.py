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


