#!/usr/bin/python
# -*- coding: utf-8 -*-
##  bgl.py 
##
##  Copyright © 2008-2010 Saeed Rasooli <saeed.gnu@gmail.com>  (ilius)
##  This file is part of PyGlossary project, http://sourceforge.net/projects/pyglossary/
##  Thanks to Raul Fernandes <rgfbr@yahoo.com.br> and Karl Grill for reverse enginearing
##
##  This program is a free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3, or (at your option)
##  any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
##  If not, see <http://www.gnu.org/licenses/gpl.txt>.

from formats_common import *

enable = True
format = 'Bgl'
description = 'Babylon (bgl)'
extentions = ('.bgl')
readOptions = ()
writeOptions = ()

import gzip, re
from text_utils import printAsError, myRaise, binStrToInt, removeTextTags
import pyglossary_gregorian as gregorian


if os.sep=='/': ## Operating system is Unix-like
  tmpDir  = '/tmp'
elif os.sep=='\\': ## Operating system is ms-windows
  tmpDir  = os.getenv('TEMP')
else:
  raise RuntimeError('Unknown path seperator(os.sep=="%s") ! What is your operating system?'%os.sep)


str_decode_map = lambda st: eval(repr(st.decode('utf8'))[1:])
str_encode_map = lambda st: eval('u'+repr(st)).encode('utf8')


class BGL:
  class Block:
    def __init__(self):
      self.length=0
      self.data=''
      self.Type=''
    def __str__(self):
      return 'Block Type=%s, length=%s, len(data)=%s'%(self.Type, self.length, len(self.data))
  class Entry:
    def __init__(self):
      self.word=''
      self.defi=''
      self.alts=[]
  class FileOffS(file):## a file class with an offset
    def seek(self, i, w=0):## position, whence
      if w==0:## relative to start of file
        file.seek(self, i+self.of, 0)
      elif w==1:## relative to current position
        file.seek(self, i, 1)
      elif w==2:## relative to end of file
        file.seek(self, i-self.of, 2)
      else:
        raise ValueError('FileOffS.seek: bad whence==%s'%w)
    def tell(self):
      return file.tell(self)-self.of
    def __init__(self, filename, offset=0):
      file.__init__(self, filename, 'rb')
      self.of = offset
      file.seek(self, offset) ## OR self.seek(0)      
  partOfSpeech = (
    'n.',           # Noun
    'adj.',         # Adjective
    'v.',           # Verb
    'adv.',         # Adverb
    'interj.',      # Interject ??
    'pron.',        # Pronoun
    'prep.',        # Preposition
    'conj.',        # Conjunction
    'suff.',        # Suffix
    'pref.',        # Prefix
    'art.'          # ?????
  )
  partOfSpeechColor = '007000'
  charsets = (
    'ISO-8859-1',   # Default, Western European, (Windows-1252 ???)
    'ISO-8859-1',   # Latin
    'ISO-8859-2',   # Eastern European
    'ISO-8859-5',   # Cyriilic
    'ISO-8859-14',  # Japanese
    'ISO-8859-14',  # Traditional Chinese
    'ISO-8859-15',  # Simplified Chinese
    'CP1257',       # Baltic
    'CP1253',       # Greek
    'ISO-8859-15',  # Korean
    'ISO-8859-9',   # Turkish
    'ISO-8859-9',   # Hebrew
    'CP1256',       # Arabic
    'CP874'         # Thai
  )
  language = (
    'English', ## ISO-8859-1
    'French', ## ISO-8859-1 ## FIXME
    'Italian', ## ISO-8859-1
    'Spanish', ## ISO-8859-1
    'Dutch',
    'Portuguese', ## ISO-8859-1
    'German', ## ISO-8859-1 ## ISO-8859-2
    'Russian',
    'Japanese', ## ISO-8859-14
    'Traditional Chinese', ## ISO-8859-14
    'Simplified Chinese', ## ISO-8859-15
    'Greek', ## CP1253
    'Korean', ## ISO-8859-15
    'Turkish', ## ISO-8859-9
    'Hebrew', ## ISO-8859-9
    'Arabic', ## CP1256
    'Thai', ## CP874
    'Other',
    'Other Simplified Chinese dialects', ## ISO-8859-15
    'Other Traditional Chinese dialects', ## ISO-8859-14
    'Other Eastern-European languages',
    'Other Western-European languages',
    'Other Russian languages',
    'Other Japanese languages', ## ISO-8859-14
    'Other Baltic languages', ## CP1257
    'Other Greek languages', ## CP1253
    'Other Korean dialects', ## ISO-8859-15
    'Other Turkish dialects', ## ISO-8859-9
    'Other Thai dialects', ## CP874
    'Polish', ## ISO-8859-2
    'Hungarian', ## ISO-8859-2
    'Czech', ## ISO-8859-2
    'Lithuanian',
    'Latvian',
    'Catalan', ## ISO-8859-1
    'Croatian', ## ISO-8859-2
    'Serbian', ## ISO-8859-2
    'Slovak', ## ISO-8859-2
    'Albanian', ## ISO-8859-1
    'Urdu', ## CP1256
    'Slovenian',
    'Estonian',
    'Bulgarian',
    'Danish', ## ISO-8859-1 ## FIXME
    'Finnish', ## ISO-8859-1 ## FIXME
    'Icelandic', ## ISO-8859-1
    'Norwegian', ## ISO-8859-1
    'Romanian', ## ISO-8859-2
    'Swedish', ## ISO-8859-1
    'Ukrainian',## ISO-8859-5 ## FIXME
    'Belarusian',
    'Farsi', ## CP1256
    'Basque', ## ISO-8859-1
    'Macedonian',
    'Afrikaans', ## ISO-8859-1
    'Faroese', ## ISO-8859-1
    'Latin', ## ISO-8859-1
    'Esperanto',
    'Tamazight',
    'Armenian'
  )

  charsetsLangs = { ## FIXME
    'ISO-8859-1':('English', 'French', 'Italian', 'Spanish', 'Portuguese', 'Catalan',
                  'German', 'Albanian', 'Finnish', 'Icelandic', 'Norwegian',
                  'Swedish', 'Danish', 'Basque', 'Afrikaans', 'Faroese', 'Latin'),
    'ISO-8859-2':('German', 'Polish', 'Hungarian', 'Czech', 'Croatian', 'Serbian',
                  'Slovak', 'Romanian'),
    'ISO-8859-5':('Ukrainian'),
    'CP1256':('Farsi', 'Arabic', 'Urdu')
  }
  
  def checkLanguage(self, text, lang):## FIXME
    uni = text.decode('utf8', 'replace')
    if lang in ('Farsi', 'Arabic', 'Urdu'):
      for uc in uni:
        if 1575<=ord(uc)<1609:##????????
          #print text, 'farsi char:', ord(uc), uc
          return True
    return False
  def recodeWord(self, text):
    #return text ## FIXME
    if self.sourceCharset in ('', 'UTF-8'):
      return text
    #if self.checkLanguage(text, self.sourceLang):
    #  #self.sourceCharset = 'UTF-8'
    #  return text
    return text.decode(self.sourceCharset, 'replace').encode('utf8').replace('\r', '')
  def recodeDefi(self, text):
    #return text ## FIXME
    if self.targetCharset in ('', 'UTF-8'):
      return text
    #if self.checkLanguage(text, self.targetLang): ## FIXME
    #  #self.targetCharset = 'UTF-8'
    #  return text
    return text.decode(self.targetCharset, 'replace').encode('utf8')
  def recodeInfo(self, text):
    #return text ## FIXME
    if self.defaultCharset in ('', 'UTF-8'):
      return text
    #if self.checkLanguage(text, self.defaultCharset): ## FIXME
    #  #self.targetCharset = 'UTF-8'
    #  return text
    #return text.decode('CP1256', 'replace').encode('utf8') ## Farsi ## FIXME
    return text.decode(self.defaultCharset, 'replace').encode('utf8')
  def __init__(self, filename, resPath=None, verbose=1, spiltSep=' | ', richText=True):
    self.verbose = verbose
    ## 0: print nothing
    ## 1: minimal info (for user)
    ## 2: extra info (for user)
    ## 3: debugging (for developer)
    self.spiltSep = spiltSep
    self.richText = richText
    ###################
    self.filename = filename
    self.title = 'Untitled'
    self.author = ''
    self.email = ''
    self.description = ''
    self.copyright = ''
    self.sourceLang = ''
    self.targetLang = ''
    self.defaultCharset = '' ## 'ISO-8859-1' ## FIXME
    self.sourceCharset = ''
    self.targetCharset = ''
    self.bgl_numEntries = 0
    self.creationTime = ''
    self.middleUpdated = ''
    self.lastUpdated = ''
    ############
    self.wordLenMax = 0
    self.defiLenMax = 0
    self.used_special_chars = []
    ############
    if resPath==None:
      #if self.filename.endswith('.bgl') or self.filename.endswith('.BGL'):
      resPath = self.filename + '_files' + os.sep
      if os.path.exists(resPath):
        if not os.path.isdir(resPath):
          i = 0
          while os.path.exists(resPath):
            resPath = '%s_files_%s%s'%(self.filename, i, os.sep)
            i += 1
          try:
            os.mkdir(resPath)
          except IOError:
            myRaise(__file__)
            resPath = tmpDir + os.sep + os.path.split(self.filename) + '_files' + os.sep
            if not os.path.isdir(resPath):
              os.mkdir(resPath)
      else:
        try:
          os.mkdir(resPath)
        except IOError:
            myRaise(__file__)
            resPath = tmpDir + os.sep + os.path.split(self.filename) + '_files' + os.sep
            if not os.path.isdir(resPath):
              os.mkdir(resPath)
    self.resPath = resPath
    dbdir = os.path.dirname(self.filename) + os.sep
    if resPath.startswith(os.sep) and resPath.startswith(dbdir):
      self.resPathRel = resPath[:len(dbdir)]
    else:
      self.resPathRel = resPath
    self.resFiles = []
  def open(self, writeGz=False):
    if '--bgl-write-gz' in sys.argv:## FIXME
      writeGz = True
    f = open(self.filename, 'rb')
    if f==None:
      return False
    buf = f.read(6)
    if len(buf)<6 or not buf[:4] in ('\x12\x34\x00\x01','\x12\x34\x00\x02'):
      return False
    i = ord(buf[4]) << 8 | ord(buf[5])
    if self.verbose>3:
      print 'Position of gz header: i=%s'%i
    if i<6:
      return False
    self.writeGz = writeGz
    if writeGz:
      self.dataFile = self.filename+'-data.gz'
      try:
        f2 = open(self.dataFile, 'wb')
      except IOError:
        myRaise(__file__)
        self.dataFile = tmpDir + os.sep + os.path.split(self.m_filename)[-1] + '-data.gz'
        f2 = open(self.dataFile, 'wb')
      f.seek(i)
      f2.write(f.read())
      f.close()
      f2.close()
      self.file = gzip.open(self.dataFile, 'rb')
    else:
      f.close()
      f = self.FileOffS(self.filename, i)
      self.file = gzip.GzipFile(fileobj=f)
    return True
  def close(self):
    print 'used_special_chars:',
    for ch in self.used_special_chars:
      print ch,
    print
    self.file.close()
  def readBlock(self, block):
    block.length = self.readBytes(1)
    if block.length==-1:
      return False
    block.Type = block.length & 0xf
    if block.Type == 4:## OK (Good end of file)
      #printAsError('End of file: block.Type==4')
      return False
    block.length >>= 4
    if block.length < 4:
      block.length = self.readBytes(block.length+1)
    else:
      block.length -= 4
    #print 'length1 =', block.length, '\ttell =', self.file.tell()
    #if block.length>=2240:
    #  printAsError('block.length=%s\tnumBlocks=%s'%(block.length,self.numBlocks))
    self.file.flush()
    if block.length:
      try:
        block.data = self.file.read(block.length)
      except:#??????????????????
        ##???????? struct.error: unpack requires a string argument of length 4
        myRaise(__file__)
        print self.numBlocks, block.length, self.file.tell()
        block.data = ''
        block.length = 0
        #block.data = self.file.read(4)
        #block.length = 4
        #return False
        #print 'end of file.'
        #sys.exit(0)
      #else:
        #if len(block.data) != block.length:
          #print 'len(block.data)=%s\tblock.length=%s'%(len(block.data), block.length)
      #if self.numBlocks>=102666:
      #  print self.numBlocks, block.length, len(block.data)
    return True
  def readBytes(self, bytes):
    val=0
    if bytes<1 or bytes>4:
      return 0
    self.file.flush()
    buf = self.file.read(bytes)
    if len(buf)==0:#####??????????????????????????????????
      self.file.seek(self.file.tell())
      buf = self.file.read(bytes)
      if len(buf)==0:
        printAsError('End of file: readBytes: len(buf)==0')
        return -1
    if len(buf)!=bytes:
       printAsError('bytes=%s , len(buf)=%s'%(bytes, len(buf)))
       return False
    for i in xrange(bytes):
      val = (val << 8) | ord(buf[i])
    return val

  def prepareWord(self, word):
    word = word.replace('\n', '')\
               .replace('\r', '')\
               .replace('<BR>', '')\
               .replace('<br>', '')
    ## Removing $INDEX$
    d0 = word.find('$')
    if d0!=-1:
      d1 = word.find('$', d0+1)
      if d1!=-1:
        try:
          int(word[d0+1:d1])
        except:
          pass
        else:
          word = word[:d0]
    #if word[0] in ('\x06', '\x08', '\x0c'):## ????
    #  word = word[1:]
    return removeTextTags(word, {
      'font':False,
      'FONT':False,
      'b':False,
      'B':False,
      'i':False,
      'I':False
    }).replace('\x96','&ldash;')


  def replaceBasic(self, defi):
    return defi.replace('<BR>','\n')\
               .replace('<br>','\n')\
               .replace('<HR>','\n')\
               .replace('<hr>','\n')\
               .replace('\x96','&ldash;')\
               .replace('\x0b','\n')\
               .replace('\x0a','\n')\
               .replace('\n\n\n', '\n\n')\
               .replace('\n\n\n', '\n\n')\
               .replace('\n\n\n', '\n\n')\
               .replace('\n\n\n', '\n\n')\
               .replace('  ', ' ')\
               .replace('\xa0', '')\
               .replace('\n ', '\n')\
               .replace('\x14\x02\x30', '')
#               .replace('\r\n','\n')\


  def replaceSpecial(self, st):
    for ch in ('♦', '●', 'é', 'è', 'ī', 'ʽ', 'ū'):
      ch1 = str_encode_map(ch)
      if ch1 in st:
        if not ch in self.used_special_chars:
          self.used_special_chars.append(ch)
      #print ch, repr(str_encode_map(ch)), str_encode_map(ch)
      st = st.replace(ch1, ch)

    st = st.replace('\n\n\n', '\n\n')\
           .strip()\
           .replace('\x00', '')\
           .replace('&ldash;', '–')\
           .replace('&quot;', '"')\
           .replace('&lt;', '<')\
           .replace('&gt;', '>')\
           .replace('&amp;', '&')\
           .replace('&nbsp;', '')\
           .replace('&#9632', '&#25fe')\
           .replace('&#9830', '&#2666')\
           .replace('\xe9\x98\xb2', '◾')\
           .replace('\xc3\xa2\xc2\x89', '≠')\
           .replace('\xc2\x80', '€')\
           .replace('\xc3\x83', 'à')\
           .replace('&acirc;', 'â')\
           .replace('&ecirc;', 'ê')\
           .replace('&icirc;', 'î')\
           .replace('&ocirc;', 'ô')\
           .replace('&ucirc;', 'û')\
           .replace('&ycirc;', 'ŷ')\
           .replace('&agrave;', 'à')\
           .replace('&egrave;', 'è')\
           .replace('&igrave;', 'ì')\
           .replace('&ograve;', 'ò')\
           .replace('&ugrave;', 'ù')\
           .replace('&ygrave;', 'ỳ')\
           .replace('&atilde;', 'ã')\
           .replace('&etilde;', 'ẽ')\
           .replace('&itilde;', 'ĩ')\
           .replace('&otilde;', 'õ')\
           .replace('&utilde;', 'ũ')\
           .replace('&ytilde;', 'ỹ')\
           .replace('&auml;', 'ӓ')\
           .replace('&euml;', 'ë')\
           .replace('&iuml;', 'ï')\
           .replace('&ouml;', 'ö')\
           .replace('&uuml;', 'ü')\
           .replace('&yuml;', 'ÿ')\
           .replace('&aring;', 'å')\
           .replace('&uring;', 'ů')\
           .replace('&wring;', 'ẘ')\
           .replace('&yring;', 'ẙ')\
           .replace('&ccedil;', 'ç')\
           .replace('&aelig;', 'æ')\
           .replace('&eth;', 'ð')\
           .replace('&pound;', '£')\
           .replace('&deg;', '°')\
           .replace('&divide;', '÷')\
           .replace('&frac12;', '½')\
           .replace('&frac13;', '⅓')\
           .replace('&frac14;', '¼')\
           .replace('&frac23;', '⅔')\
           .replace('&frac34;', '¾')\
           .replace('&xFrac13;', '⅓')\
           .replace('&hearts;', '♥')\
           .replace('&diams;', '♦')\
           .replace('&spades;', '♠')\
           .replace('&clubs;', '♣')\
           .replace('&deg', '° ')\
           .replace('&quot', '"')\
           #.replace('\x0c', '')\
           #.replace('\x08', '')\
    ####################################
    ## <charset c=T>026A;</charset>
    #pat = re.compile('<charset c\=.*>[0-9a-fA-F]{4};</charset>')
    pat = re.compile('<charset c\=t>[0-9a-fA-F]{4};</charset>', re.I)
    while True:
      s = re.search(pat, st)
      if s==None:
        break
      (i0, i1) = s.span()
      ch = unichr(int(st[i0+13:i0+17], 16)).encode('utf8')
      st = st[:i0] + ch + st[i1:]
    ## <charset c="T">026A;</charset>   (; is optional and will removed if exists)
    pat = re.compile('<charset c\=\"t\">[0-9a-fA-F]{4};?</charset>', re.I)
    while True:
      s = re.search(pat, st)
      if s==None:
        break
      (i0, i1) = s.span()
      ch = unichr(int(st[i0+15:i0+19], 16)).encode('utf8')
      st = st[:i0] + ch + st[i1:]
    ## &#0130;  (; is optional and will removed if exists)
    pat = re.compile('&#[0-9a-fA-F]{4};?')
    while True:
      s = re.search(pat, st)
      if s==None:
        break
      (i0, i1) = s.span()
      ch = unichr(int(st[i0+2:i0+6], 16)).encode('utf8')
      st = st[:i0] + ch + st[i1:]
    ## &#x0130;  (; is optional and will removed if exists)
    pat = re.compile('&#x[0-9a-fA-F]{4};?')
    while True:
      s = re.search(pat, st)
      if s==None:
        break
      (i0, i1) = s.span()
      ch = unichr(int(st[i0+3:i0+7], 16)).encode('utf8')
      st = st[:i0] + ch + st[i1:]
    ###################
    return st

  def replaceImgLinks(self, st):
    #for name in self.resFiles:
    #  defi = defi.replace('\x1e'+name+'\x1f', self.resPathRel+name)
    i = 0
    while True:
      i = st.find('<IMG ', i)
      if i==-1:
        break
      i1 = st.find('src="\x1e')
      if i1==-1:
        i = i1
        continue
      i2 = st.find('\x1f', i1) ## \x1f" OR \x1f'
      if i2==-1:
        i = i2
        continue
      i = st.find('>', i2)
      if i==-1:
        continue
      st = st[:i1+5] + self.resPath + st[i1+6:i2] + st[i2+1:]
    return st

  processWord = lambda self, word: self.replaceSpecial(self.recodeWord(self.prepareWord(word)))

  processDefi = lambda self, defi: self.replaceImgLinks(self.replaceSpecial(self.recodeDefi(self.replaceBasic(defi))))
  
  processInfo = lambda self, info: self.replaceSpecial(self.recodeInfo(info))

  def read(self):
    self.numEntries = 0
    self.numBlocks = 0
    block = self.Block()
    while self.readBlock(block):
      self.numBlocks += 1
      if block.length==0:
        continue
      word = ''
      defi = ''
      if block.Type==0:
        if ord(block.data[0])==8:
          try:
            Type = ord(block.data[1])
          except:
            myRaise(__file__)
            for c in block.data:
              printAsError(ord(c))
          else:
            if Type > 64:
              Type -= 65
            self.defaultCharset = self.charsets[Type]
      elif block.Type in (1,10,13):
        self.numEntries += 1
      elif block.Type==3:
        pos=2
        x = ord(block.data[1])
        if x==1:
          for a in xrange(block.length-2):
            word += block.data[pos]
            pos += 1
          self.title = word
        elif x==2:
          for a in xrange(block.length-2):
            word += block.data[pos]
            pos += 1
          self.author = word
        elif x==3:
          for a in xrange(block.length-2):
            word += block.data[pos]
            pos += 1
          self.email = word
        elif x==4:
          for a in xrange(block.length-2):
            word += block.data[pos]
            pos += 1
          self.copyright = word
        elif x==7:
          self.sourceLang = self.language[ord(block.data[5])]
        elif x==8:
          self.targetLang = self.language[ord(block.data[5])]
        elif x==9:
          for a in xrange(block.length-2):
            word += block.data[pos]
            pos += 1
          self.description = word
        elif x==12:
          self.bgl_numEntries = binStrToInt(block.data[2:])
        elif x==26:
          value = ord(block.data[2])
          if value > 64:
            value -= 65;
          word = self.charsets[value];
          self.sourceCharset = word
        elif x==27:
          value = ord(block.data[2])
          if value > 64:
            value -= 65;
          word = self.charsets[value];
          self.targetCharset = word
        elif x==20:## Creation Time
          jd1970 = gregorian.to_jd(1970, 1, 1)
          (djd, hm) = divmod(binStrToInt(block.data[2:]), (24*60))
          (year, month, day) = gregorian.jd_to(djd+jd1970)
          (hour, minute) = divmod(hm, 60)
          self.creationTime = '%.2d/%.2d/%.2d, %.2d:%.2d'%(year, month, day, hour, minute)
        elif x==28:## Middle Updated ## ???????????????
          jd1970 = gregorian.to_jd(1970, 1, 1)
          (djd, hm) = divmod(binStrToInt(block.data[2:]), 24*60)
          (year, month, day) = gregorian.jd_to(djd+jd1970)
          (hour, minute) = divmod(hm, 60)
          self.middleUpdated = '%.2d/%.2d/%.2d, %.2d:%.2d'%(year, month, day, hour, minute)
        elif x==51:## Last Updated
          jd1970 = gregorian.to_jd(1970, 1, 1)
          (djd, hm) = divmod(binStrToInt(block.data[2:]), 24*60)
          (year, month, day) = gregorian.jd_to(djd+jd1970)
          (hour, minute) = divmod(hm, 60)
          self.lastUpdated = '%.2d/%.2d/%.2d, %.2d:%.2d'%(year, month, day, hour, minute)
        elif self.verbose>3:
          print 'Unknown info type x=%s,  block.Type=%s,  block.length=%s'%\
            (x, block.Type, block.length)
          #if block.length>50:
          #  open('info-i%.3d-t%d'%(self.numBlocks, x), 'wb').write(block.data)
      elif block.Type==2:## Embedded File (mostly Image or HTML)
        name='' ## Embedded file name
        cont='' ## Embedded file content
        pos = 0
        ## name:
        Len = ord(block.data[pos]) ; pos+=1
        if Len >= len(block.data):
          continue
        name += block.data[pos:pos+Len] ; pos += Len
        if name in ('C2EEF3F6.html', '8EAF66FD.bmp'):
          if self.verbose>1:
            print 'Skiping non-usefull file "%s"'%name
          continue
        name = self.recodeWord(name)
        ## cont:
        cont = block.data[pos:]
        path = self.resPath + name
        open(path, 'wb').write(cont)
        self.resFiles.append(name)
        #if self.verbose>1:
        #  print 'File "%s" saved'%path
      else:## Unknown block.Type
        if self.verbose>2:
          print 'Block: type=%s,  length=%s,  data_length=%s,  number=%s'\
            %(block.Type, block.length, len(block.data), self.numBlocks)
        #open('block-i%s-t%s'%(self.numBlocks, block.Type), 'wb').write(block.data)
    self.file.seek(0)
    ################
    self.numBlocks = 0
    #######
    #if self.sourceCharset=='' and self.sourceLang in ('Arabic', 'Farsi'):
    #  self.sourceCharset = "CP1256"
    #  printAsError('No source charset defined! Setting "CP1256" because of language "%s"'%self.sourceLang)
    #if self.targetCharset=='' and self.targetLang in ('Arabic', 'Farsi'):
    #  self.targetCharset = "CP1256"
    #  printAsError('No target charset defined! Setting "CP1256" because of language "%s"'%self.targetLang)
    if self.defaultCharset=='':
      if self.sourceCharset=='':
        if self.targetCharset=='':
          printAsError('No charset defined!')
        else:
          self.defaultCharset = self.sourceCharset = self.targetCharset
      else:
        self.defaultCharset = self.sourceCharset
    elif self.sourceCharset=='':
      printAsError('No sourceCharset is defined in BGL, setting to defaultCharset==%s'%self.defaultCharset)
      self.sourceCharset = self.defaultCharset
    elif self.targetCharset=='':
      printAsError('No targetCharset is defined in BGL, setting to defaultCharset==%s'%self.defaultCharset)
      self.targetCharset = self.defaultCharset
    ######################################
    self.title = self.processInfo(self.title)
    self.author = self.processInfo(self.author)
    self.email = self.processInfo(self.email)
    self.copyright = self.processInfo(self.copyright)
    self.description = self.processInfo(self.description)
    if self.verbose>0:
      print 'numEntries = %s'%self.numEntries
      if self.bgl_numEntries!=self.numEntries:
        print 'bgl_numEntries = %s (!!!!!!!!!)'%self.bgl_numEntries
      if self.verbose>1:
        print 'numBlocks = %s'%self.numBlocks
      print 'defaultCharset = %s'%self.defaultCharset
      print 'sourceCharset = %s'%self.sourceCharset
      print 'targettCharset = %s'%self.targetCharset
      print
      print 'sourceLang = %s'%self.sourceLang
      print 'targetLang = %s'%self.targetLang
      print
      print 'creationTime = %s'%self.creationTime
      print 'middleUpdated = %s'%self.middleUpdated ## ???????????????
      print 'lastUpdated = %s'%self.lastUpdated
    ###################################
    if len(os.listdir(self.resPath))==0:
      try:
        os.rmdir(self.resPath)
      except:
        myRaise(__file__)
    return True

  def readEntry(self, entry):
    if self.file==None:
      return False
    block = self.Block()
    while self.readBlock(block):
      if block.length and block.Type in (1, 10, 13):
        word = ''
        defi = ''
        alts = []
        pos = 0
        ## word:
        Len = ord(block.data[pos]) ; pos+=1
        if Len >= len(block.data):
          #print Len, len(block.data)
          sys.exit(1)
        word = self.processWord(word+block.data[pos:pos+Len])
        pos += Len
        parts = word.split(self.spiltSep)
        if len(parts)>1:
          word = parts[0]
          for p in parts[1:]:
            if p!=word and not p in alts:
              alts.append(p)
        self.wordLenMax = max(self.wordLenMax, len(word))
        ## defi:
        Len = ord(block.data[pos]) << 8  ; pos += 1
        Len |= ord(block.data[pos])  ; pos += 1
        """
        for a in xrange(Len):
          try:
            block.data[pos]
          except:
            break
          if block.data[pos]=='\x0a':
            defi += '\n'
            pos += 1
          #elif block.data[pos]<'\x20':
          #  if a<Len-3 and block.data[pos]=='\x14' and block.data[pos+1]=='\x02':
          #    defi = self.partOfSpeech[ord(block.data[pos+2]) - 0x30] + " " + defi
          #  pos += Len - a
          else:
            defi += block.data[pos]
            pos += 1
        """
        defi = block.data[pos:pos+Len]
        self.defiLenMax = max(self.defiLenMax, len(defi))
        #pos += Len
        ############################ partOfSpeech ?????????????????????????
        i = defi.find('\x14\x02')
        if i!=-1:
          try:
            c = block.data[pos+i+2]
          except:
            if self.verbose>2:
              print 'partOfSpeech error:', len(block.data), pos+i+2
          else:
            index = ord(c) - 0x30
            if index<11:
              if self.richText:
                defi = '<font color="#%s">%s</font> %s'%(
                  self.partOfSpeechColor,
                  self.partOfSpeech[index],
                  defi[:i]+defi[i+2:]
                )
              else:
                defi = self.partOfSpeech[index] + " " + defi[:i]+defi[i+2:]
            elif self.verbose>2:
              print 'partOfSpeech error: ord(block.data[pos+i+2])-0x30 =', ord(c)- 0x30
        ####################################################
        pos += Len
        
        #    .replace('\x03','\n')\
        #    .replace('\x04','\n')\
        #    .replace('\x06','\n')\
        #    .replace('0\x06','')\
        
        #################### Removing trashy characters!
        ## Only Phonetics maybe usefull (that not shown in Bablyon(Ltd) Dictionary itself)
        ## How to extract only Phonetics ???????????????????????????
        i = defi.rfind('\x06')
        if i>0:
          defi = defi[:i-1]
        i = defi.rfind('\x1b')
        if i>1:
          defi = defi[:i-2]
        ####################################
        #defi = self.replaceBasic(defi) ## FIXME
        ####################################
        if defi.endswith('\x18'):
          defi = defi[:-1]
        i = defi.rfind('\x18')
        if i>0 and i<len(defi)-2:## FIXME
          #if defi[i+1] in ('#', '\x02', '\x03', '\x04', '\x05', '\x07', '\x08',
          #'\x0c', '\x0e', '\x0f', '\x13', '\x16'):## ??????
          if ord(defi[i+1])<32:
            alt = defi[i+2:]
          else:
            alt = defi[i+1:]
          alt = self.processWord(alt)
          if defi[i-1]=='\x18':
            defi = defi[:i-1]
          else:
            defi = defi[:i]
          if alt!=word and not alt in alts:
            alts.append(alt)
            defi = '\n%s\n\n%s'%(alt, defi)
        else:
          i = defi.rfind('(\x01\x07') ## ???? FIXME
          if i>0:
            alt = self.processWord(defi[i+3:])
            defi = defi[:i]
            if alt!=word and not alt in alts:
              alts.append(alt)
              defi = '<b>%s<b>\n%s'%(alt, defi)
        if defi.endswith('\x14'):
          #defi = defi[:-1] + '\n' + self.copyright
          defi = defi[:-1]
          appendCopyright = True
        else:
          appendCopyright = False
        while pos < block.length:
          Len = ord(block.data[pos]) ; pos += 1
          alt = self.processWord(block.data[pos:pos+Len])
          if alt!=word and not alt in alts:
            alts.append(alt)
          pos += Len

        defi = self.processDefi(defi)
        
        if appendCopyright:
          defi += ('\n' + self.copyright)

        entry.word = word
        entry.defi = defi
        entry.alts = alts        
        return True
      #else:
      #  if not block.Type in (0, 2, 3):
      #    print 'Block type=%s,\tdata_length=%s'%(block.Type, len(block.data))
    return False
  def __del__(self):
    if self.verbose>2:
      print 'wordLenMax = %s'%self.wordLenMax
      print 'defiLenMax = %s'%self.defiLenMax
    self.file.close()
    if self.writeGz:
      os.remove(self.dataFile)



def read_ext(glos, filename):
  try:
    import _babylon
    #from _babylon import Babylon_readEntry, bgl_entry_headword_get, bgl_entry_definition_get
    from _babylon import Babylon_readEntry as readEntry
    from _babylon import Babylon_swigregister as swigregister
    from _babylon import Babylon_bgl_entry_definition_get as entry_definition_get
    from _babylon import Babylon_bgl_entry_headword_get as entry_headword_get
    #from _babylon import Babylon_bgl_entry_alternates_get as entry_alternates_get
  except ImportError:
    myRaise(__file__)
    printAsError('Binary module "_babylon" can not be imported! Using internal BGL reader (this has not a good support)')
    return glos.readBgl(filename)
  glos.data = []
  db = _babylon.new_Babylon(filename)
  _babylon.Babylon_swigregister(db)
  if not _babylon.Babylon_open(db):
    raise 'can not open BGL file "%s"'%filename
  if not _babylon.Babylon_read(db):
    raise 'can not read BGL file "%s"'%filename
  n = _babylon.Babylon_numEntries(db)
  swigregister(n)
  ## could not determine numEntries as int when defined as "uint" in C++ codes
  ## I changed it to "int"
  ui = glos.ui
  if not isinstance(n, int):
    ui = None
  if ui==None:
    while True:
      entry = readEntry(db)
      swigregister(entry)
      w = entry_headword_get(db, entry)
      m = entry_definition_get(db, entry).replace('<BR>', '\n')\
                                         .replace('<br>', '\n')
      if w=='' and m=='':
        break
      else:
        glos.data.append([w,m])
  else:
    ui.progressStart()
    k = 2000
    for i in xrange(n):
      entry = readEntry(db)
      swigregister(entry)
      w = entry_headword_get(db, entry)
      m = entry_definition_get(db, entry).replace('<BR>', '\n')\
                                         .replace('<br>', '\n')
      glos.data.append([w,m])
      if i%k==0:
        rat = float(i)/n
        ui.progress(rat)
    #ui.progress(1.0, 'Loading Completed')
    ui.progressEnd()
  glos.setInfo('title'       ,_babylon.Babylon_title(db)      )
  glos.setInfo('author'      ,_babylon.Babylon_author(db)     )
  glos.setInfo('email'       ,_babylon.Babylon_email(db)      )
  glos.setInfo('description' ,_babylon.Babylon_description(db))
  glos.setInfo('copyright'   ,_babylon.Babylon_copyright(db)  )
  glos.setInfo('sourceLang'  ,_babylon.Babylon_sourceLang(db) )
  glos.setInfo('targetLang'  ,_babylon.Babylon_targetLang(db) )
  glos.setInfo('charset'     ,_babylon.Babylon_charset(db)    )


def read(glos, filename, appendAlternatives=True):
  glos.data = []
  db = BGL(filename)
  if not db.open():
    raise 'can not open BGL file "%s"'%filename
  if not db.read():
    raise 'can not read BGL file "%s"'%filename
  n = db.numEntries
  ui = glos.ui
  if not isinstance(n, int):
    ui = None
  entry = BGL.Entry()
  #altd = {} ## alternates dict #@2
  if ui==None:
    for i in xrange(n):
      if not db.readEntry(entry):
        printAsError('No enough entries found!')
        break
      if appendAlternatives:
        for alt in entry.alts:####??????????????? What do with alternates?
          entry.word += ' | '+alt #@3
      glos.data.append((entry.word, entry.defi))
  else:
    ui.progressStart()
    k = 2000
    for i in xrange(n):
      if not db.readEntry(entry):
        printAsError('No enough entries found!')
        break
      if appendAlternatives:
        for alt in entry.alts:####??????????????? What do with alternates?
          #glos.data.append(('~'+alt, 'See "%s"'%entry.word)) ## method @1
          #try: #@2
          #  altd[alt] += '\n%s'%entry.word #@2
          #except KeyError: #@2
          #  altd[alt] = 'See:\n%s'%entry.word #@2
          entry.word += ' | '+alt #@3
      glos.data.append((entry.word, entry.defi))
      if i%k==0:
        rat = float(i)/n
        ui.progress(rat)
    ui.progressEnd()
  db.close()
  ## Merge repeted alternates ???????????????????????????
  #for word in altd.keys(): #@2
  #  glos.data.append(('~'+word, altd[word])) #@2
  ##############################################
  glos.setInfo('title'                ,db.title)
  glos.setInfo('author'               ,db.author)
  glos.setInfo('email'                ,db.email)
  glos.setInfo('description'          ,db.description)
  glos.setInfo('copyright'            ,db.copyright)
  glos.setInfo('sourceLang'           ,db.sourceLang)
  glos.setInfo('targetLang'           ,db.targetLang)
  glos.setInfo('bgl_defaultCharset'   ,db.defaultCharset)
  glos.setInfo('bgl_sourceCharset'    ,db.sourceCharset)
  glos.setInfo('bgl_targetCharset'    ,db.targetCharset)
  glos.setInfo('bgl_creationTime'     ,db.creationTime)
  glos.setInfo('bgl_middleUpdated'    ,db.middleUpdated) ## ??????????
  glos.setInfo('bgl_lastUpdated'      ,db.lastUpdated) ## probably empty
  glos.setInfo('sourceCharset'        ,'UTF-8')
  glos.setInfo('targetCharset'        ,'UTF-8')
  glos.resPath = db.resPath


def createBglBlock(word, mean, btype=1): ## btype is 1 or 10
  bdata=''
  n = len(word)
  if n>255:
    printAsError('word length is too long: %s'%n)
    word = word[:255]
    n = 255
  bdata+=chr(n)
  bdata+=word
  n = len(mean)
  if n>=256**2:
    printAsError('too long word, len(word)=%s'%n)
    return ''
  bdata+=intToBinStr(n, 2)
  bdata+=mean
  if len(bdata)<12:
    block = chr((len(bdata)+4)*16+btype) + bdata
  else:
    blen = intToBinStr(len(bdata))
    ll = len(blen)
    if ll>16:
      printAsError('too long mean, len(blen)=%s'%ll)
      return ''
    block = chr((ll-1)*16+btype) + blen + bdata
  return block

def createBglInfoBlock(num, value):
  bdata='\x00'+chr(num)+value
  if len(bdata)<12:
    block = chr((len(bdata)+4)*16+3) + bdata
  else:
    blen = intToBinStr(len(bdata))
    ll = len(blen)
    if ll>16:
      printAsError('too long mean, len(blen)=%s'%ll)
      return ''
    block = chr((ll-1)*16+3) + blen + bdata
  return block


def write(glos, filename, writeInfo=True):## output BGL file can't be opened with Babylon! 
  import gzip
  f = open(filename, 'wb')
  gz_pos = 71 ## position of gz header
  ### whats before gz header ?!!!
  f.write('\x12\x34\x00\x01\x00'+chr(gz_pos)+'\x00'*(gz_pos-6))
  f.close()
  f = gzip.open(filename, 'ab')
  n = len(glos.data)
  for i in xrange(n):
    f.write(createBglBlock(glos.data[i][0], glos.data[i][1]))
  if writeInfo:
    bglInfo={
      'title'           :1,
      'author'          :2,
      'email'           :3,
      'copyright'       :4,
      'description'     :9}
    for key in bglInfo.keys():
      value = glos.getInfo(key)
      if value=='':
        value='Unknown'
      num = bglInfo[key]
      f.write(createBglInfoBlock(num, value))
    ########## ?????????????????????????????????????????????????????????????
    f.write('\x00\x07\x00\x00\x00\x00') ## setting sourceLang to English(0)  
    f.write('\x00\x08\x00\x00\x00\x33') ## setting targetLang to Farsi(51)
    f.write('\x00\x1a\x41') ## setting sourceCharset to Default(0, 65)  ## has not UTF-8  !!!!!!!
    f.write('\x00\x1b\x4d') ## setting targetCharset to Arabic(12, 77)  ## has not UTF-8  !!!!!!!
  f.close()

try:
  import psyco
except:
  pass
else:
  psyco.bind(BGL)
