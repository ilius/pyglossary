#!/usr/bin/python
# -*- coding: utf-8 -*-
##   sdict.py
##   Loader engine for AXMASoft's open dictionary format
##
##   Copyright (C) 2010 Saeed Rasooli <saeed.gnu@gmail.com>  (ilius)
##   Copyright (C) 2006-2008 Igor Tkach
##         Was part of SDict Viewer (http://sdictviewer.sf.net)
##
##   This program is a free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation, version 3 of the License.
##
##   You can get a copy of GNU General Public License along this program
##   But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

#from __future__ import with_statement ## FIXME
from formats_common import *

enable = True
format = 'Sdict'
description = 'Sdictionary (dct)'
extentions = ('.dct',)
readOptions = ('encoding',)
writeOptions = ()

import zlib, bz2, time, marshal, os, os.path
from struct import unpack
#from sdictviewer.dictutil import SkippedWord, WordLookup

settings_dir  = ".sdictviewer"
index_cache_dir = os.path.join(os.path.expanduser("~"),  settings_dir, "index_cache")
INDEXING_THRESHOLD = 1000


class GzipCompression:
  def __str__(self):
    return 'gzip'
  def decompress(self, string):
    return zlib.decompress(string)

class Bzip2Compression:
  def __str__(self):
    return "bzip2"
  def decompress(self, string):
    return bz2.decompress(string)

class NoCompression:
  def __str__(self):
    return "no compression"
  def decompress(self, string):
    return string

compressions = [
  NoCompression(),
  GzipCompression(),
  Bzip2Compression()
]

read_raw = lambda s, fe: s[fe.offset:fe.offset + fe.length]

read_str = lambda s, fe: read_raw(s, fe).replace('\x00', '');

read_int = lambda s, fe=None: unpack('<I', read_raw(s, fe) if fe else s)[0]

read_short = lambda raw: unpack('<H', raw)[0]

read_byte = lambda raw: unpack('<B', raw)[0]

class FormatElement:
  def __init__(self, offset, length, elementType=None):
    self.offset = offset
    self.length = length
    self.elementType = elementType

class Header:
  f_signature = FormatElement(0x0, 4)
  f_input_lang = FormatElement(0x4, 3)
  f_output_lang = FormatElement(0x7, 3)
  f_compression = FormatElement(0xa, 1)
  f_num_of_words = FormatElement(0xb, 4)
  f_length_of_short_index=FormatElement(0xf, 4)
  f_title=FormatElement(0x13, 4)
  f_copyright=FormatElement(0x17, 4)
  f_version=FormatElement(0x1b, 4)
  f_short_index=FormatElement(0x1f, 4)
  f_full_index=FormatElement(0x23, 4)
  f_articles=FormatElement(0x27, 4)
   
  def parse(self, str):
    self.signature = read_str(str, self.f_signature)
    if self.signature != 'sdct':
      raise DictFormatError, "Not a valid sdict dictionary"
    self.word_lang = read_str(str, self.f_input_lang)
    self.article_lang = read_str(str, self.f_output_lang)
    self.short_index_length = read_int(str, self.f_length_of_short_index)
    comp_and_index_levels_byte = read_byte(read_raw(str, self.f_compression))
    self.compressionType = comp_and_index_levels_byte & int("00001111", 2)
    self.short_index_depth = comp_and_index_levels_byte >> 4
    self.num_of_words = read_int(str, self.f_num_of_words)
    self.title_offset = read_int(str, self.f_title)
    self.copyright_offset = read_int(str, self.f_copyright)
    self.version_offset = read_int(str, self.f_version)
    self.articles_offset = read_int(str, self.f_articles)
    self.short_index_offset = read_int(str, self.f_short_index)
    self.full_index_offset = read_int(str, self.f_full_index)


class SDictionary:
  def __init__(self, filename, encoding="utf-8"):
    self.encoding = encoding
    self.filename = filename
    self.file = open(filename, "rb");
    self.header = Header()
    self.header.parse(self.file.read(43))
    self.compression = compressions[self.header.compressionType]
    self.title = self.read_unit(self.header.title_offset)
    self.version = self.read_unit(self.header.version_offset)
    self.copyright = self.read_unit(self.header.copyright_offset)

  def read_unit(self, pos):
    f = self.file
    f.seek(pos);
    record_length= read_int(f.read(4))
    s = f.read(record_length)
    s = self.compression.decompress(s)
    return s

  def load(self):
    self.short_index = self.read_short_index()

  def read_short_index(self):
    self.file.seek(self.header.short_index_offset)
    s_index_depth = self.header.short_index_depth
    index_entry_len = (s_index_depth+1)*4
    short_index_str = self.file.read(index_entry_len*self.header.short_index_length)
    short_index_str = self.compression.decompress(short_index_str)
    index_length = self.header.short_index_length
    short_index = [{} for i in xrange(s_index_depth+2)]
    depth_range = xrange(s_index_depth)
    for i in xrange(index_length):
      entry_start = start_index = i*index_entry_len
      short_word = u''
      try:
        for j in depth_range:
          #inlined unpack yields ~20% performance gain compared to calling read_int()
          uchar_code =  unpack('<I',short_index_str[start_index:start_index+4])[0]
          start_index+=4
          if uchar_code == 0:
            break
          short_word += unichr(uchar_code)
      except ValueError, ve:
        # If Python is built without wide unicode support (which is the case on Maemo)
        # it may not be possible to use some unicode chars. It seems best to ignore such index items
        # The rest of the dictionary should be usable.
        print 'Failed to decode short index item %s, will ignore: %s'%(i, ve)
        continue
      pointer_start = entry_start+s_index_depth*4
      pointer = unpack('<I',short_index_str[pointer_start:pointer_start+4])[0]
      short_index[len(short_word)][short_word] = pointer
    return short_index

  def __iter__(self):
    pos = self.header.full_index_offset
    read_item = self.read_full_index_item
    next_ptr = 0
    while True:
      pos += next_ptr
      item = read_item(pos)
      if item==None:
        break
      (next_ptr, word, ptr) = item
      if word==None:
        break
      else:
        yield (word, self.read_unit(self.header.articles_offset+ptr)\
                     .replace('<BR>', '\n')\
                     .replace('<br>', '\n'))

  def read_full_index_item(self, pointer):
    try:
      f = self.file
      f.seek(pointer)
      s = f.read(8)
      next_word = unpack('<H', s[:2])[0]
      article_pointer = unpack('<I', s[4:])[0]
      word = f.read(next_word - 8) if next_word else None
      return next_word, word, article_pointer
    except Exception, e:
      if pointer >= self.header.articles_offset:
        print 'Warning: attempt to read word from illegal position in dict file'
        return None
      print e

  def read_article(self, pointer):
    return self.read_unit(self.header.articles_offset + pointer)


def read(glos, filename, encoding='utf-8'):
  ## Binary Glossary for "Sdictionary" (http://sdict.org)
  ## It has extention '.dct' 
  sd = SDictionary(filename, encoding)
  sd.load()
  ##########
  glos.setInfo('name', sd.title)
  glos.setInfo('version', sd.version)
  glos.setInfo('copyright', sd.copyright)
  ##########
  glos.data = list(sd.__iter__())

   
