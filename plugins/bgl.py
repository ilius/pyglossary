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

import gzip, re, htmlentitydefs, xml.sax.saxutils, pickle

from text_utils import printAsError, printAsWarning, myRaise, binStrToInt, ExcMessage, \
  isASCII, isControlChar, name2codepoint
import pyglossary_gregorian as gregorian

# use this variable to vary verbosity of output for non-class members
# see verbose parameter of BGL.__init__
gVerbose = 0

if os.sep=='/': ## Operating system is Unix-like
  tmpDir  = '/tmp'
elif os.sep=='\\': ## Operating system is ms-windows
  tmpDir  = os.getenv('TEMP')
else:
  raise RuntimeError('Unknown path seperator(os.sep=="%s") ! What is your operating system?'%os.sep)


class MetaData:
  def __init__(self):
    self.blocks = []
    self.numEntries = None
    self.numBlocks = None
    self.numFiles = None
    self.gzip_beg_offset = None
    self.gzip_end_offset = None
    self.file_size = None
    self.bgl_header = None # data before gzip header

class MetaDataBlock:
  def __init__(self, data, Type):
    self.data = data
    self.Type = Type

class MetaDataStub:
  def __init__(self, length, Type):
    self.length = length
    self.Type = Type

class MetaDataRange:
  def __init__(self, Type, count):
    self.Type = Type
    self.count = count

class MetaData2:
  """Second pass metadata.
  
  We need to scan all definitions in order to collect these statistical data.
  """
  def __init__(self):
    # defiTrailingFields[i] - number of fields with code i found
    self.defiTrailingFields = [ 0 ] * 256
    self.isDefiASCII = True # true if all definitions contain only ASCII chars
    """
    We apply a number of tests to each definition, excluding those with 
    overwritten encoding (they start with <charset c=U>).
    DefiProcessedCnt - total number of definitions processed
    DefiUtf8Cnt - number of definitions in utf8 encoding
    DefiASCIICnt - number of definitions containing only ASCII chars    
    """
    self.DefiProcessedCnt = 0
    self.DefiUtf8Cnt = 0
    self.DefiASCIICnt = 0

class BGLGzipFile(gzip.GzipFile):
  """gzip.GzipFile class without CRC check.
  
  We redefined one method - _read_eof. 
  It prints a warning when CRC code does not match.
  The original method raises an exception in this case.
  Some dictionaries do not use CRC code, it is set to 0.
  """
  def _read_eof(self):
    from gzip import read32
    # We've read to the end of the file, so we have to rewind in order
    # to reread the 8 bytes containing the CRC and the file size.
    # We check the that the computed CRC and size of the
    # uncompressed data matches the stored values.  Note that the size
    # stored is the true file size mod 2**32.
    self.fileobj.seek(-8, 1)
    crc32 = read32(self.fileobj)
    isize = read32(self.fileobj)  # may exceed 2GB
    if crc32 != self.crc:
      if gVerbose >= 2:
        print "CRC check failed %s != %s" % (hex(crc32), hex(self.crc))
    elif isize != (self.size & 0xffffffffL):
      raise IOError, "Incorrect length of data produced"

  def isNewMember(self):
    # self.extrasize == 0 iff read buffer is empty
    # self.tell() != 0 - this is not begining of the file, nothing is read yet.
    if self.extrasize == 0 and self.tell() != 0:
      # We've read the previous member completely.
      if self._new_member:
        return True
      # It is possible that we've read all data of the current member, 
      # but have not tried to read further. Thus end of member has not beed encountered.
      # Read one byte further and check if we encounter end of the member.
      else:
        buf = self.read(1)
        self._unread(buf)
        return self._new_member
    else:
      return False


class BabylonLanguage:
  """Babylon language properties.
  
  language - bab:SourceLanguage, bab:TargetLanguage .gpr tags 
    (English, French, Japanese)
  charset - bab:SourceCharset, bab:TargetCharset .gpr tags 
    (Latin, Arabic, Cyrillic)
  encoding - Windows code page
    (cp1250, cp1251, cp1252)
  code - value of the type 3, code  in .bgl file
  """
  def __init__(self, language, charset, encoding, code):
    self.language = language
    self.charset = charset
    self.encoding = encoding
    self.code = code

class ArgumentError(Exception):
  pass

def replace_html_entry(m):
  """Replace character entity with the corresponding character
  
  Return the original string if conversion fails.
  Escape the result string again. Only <, >, & characters are escaped.
  Use this as a replace function of re.sub.
  """
  text = m.group(0)
  name = m.group(1)
  res = None
  if text[:2] == "&#":
    # character reference
    try:
      if text[:3].lower() == "&#x":
        code = int(name, 16)
      else:
        code = int(name)
      if code <= 0:
        raise ValueError()
      res = unichr(code).encode('utf-8')
    except (ValueError, OverflowError):
      res = unichr(0xFFFD).encode('utf-8') # replacement character
  elif text[0] == "&":
    # named entity
    try:
      res = unichr(htmlentitydefs.name2codepoint[name]).encode('utf-8')
    except KeyError:
      try:
        res = unichr(name2codepoint[name.lower()]).encode('utf-8')
      except KeyError:
        """Babylon dictionaries contain a lot of non-standard entity references,
        for example, csdot, fllig, nsm, cancer, thlig, tsdot, upslur...
        This not just a typo. These entries repeat over and over again.
        Perhaps they had meaning in the source dictionary that was converted to Babylon,
        but now the meaning is lost. Babylon does render them as is, that is, for example,
        &csdot; despite other references like &amp; are replaced with corresponding 
        characters.
        """
        if gVerbose >= 2:
          printAsWarning("unknown html entity {0}".format(text))
        res = text
  else:
    raise ArgumentError()
  return xml.sax.saxutils.escape(res)

def replace_babylon_char_ref(m):
  """Replace the charset tag with the corresponding character
  
  for <charset c="t">0a2;</charset> input text
  m.group(1) = 0a2
  Escape the result string again. Only <, >, & characters are escaped.
  Use this as a replace function of re.sub.
  """
  #text = m.group(0)
  scode = m.group(1)
  res = None
  try:
    code = int(scode, 16)
    if code <= 0:
      raise ValueError()
    res = unichr(code).encode('utf-8')
  except (ValueError, OverflowError):
    res = unichr(0xFFFD).encode('utf-8') # replacement character
  return xml.sax.saxutils.escape(res)

def replace_dingbat(m):
  """replace chars \u008c-\u0095 with \u2776-\u277f
  """
  ch = m.group(0)
  code = ord(ch) + (0x2776-0x8c)
  return unichr(code)
  
class BGL:
  class Block:
    def __init__(self):
      self.data=''
      self.Type=''
      # block offset in the gzip stream, for debugging
      self.offset=-1
    def __str__(self):
      return 'Block Type=%s, length=%s, len(data)=%s'%(self.Type, self.length, len(self.data))
  
  class Entry:
    def __init__(self):
      self.word=''
      self.defi=''
      self.alts=[]
  
  class FileOffS(file):
    """A file class with an offset.
    
    This class provides an interface to a part of a file starting at specified offset and
    ending at the end of the file, making it appear an independent file.
    offset parameter of the constructor specifies the offset of the first byte of the
    modeled file.
    """
    def __init__(self, filename, offset=0):
      file.__init__(self, filename, 'rb')
      self.of = offset
      self.filesize = os.path.getsize(filename)
      file.seek(self, offset) ## OR self.seek(0)
    def seek(self, i, w=0):## position, whence
      if w==0:## relative to start of file
        if i < 0:
          i = 0
        file.seek(self, i+self.of, 0)
      elif w==1:## relative to current position
        if i < 0:
          pos = file.tell(self)
          if pos + i < self.of:
            i = pos - self.of
        file.seek(self, i, 1)
      elif w==2:## relative to end of file
        file.seek(self, i, 2)
      else:
        raise ValueError('FileOffS.seek: bad whence=={0}'.format(w))
    def tell(self):
      return file.tell(self)-self.of
  
  class DefinitionFields:
    """Fields of entry definition
    
    Entry definition consists of a number of fields.
    The most important of them are:
    defi - the main definition, mandatory, comes first.
    part of speech
    title
    """
    def __init__(self):
      self.defi = None # main definition part of defi, raw
      self.u_defi = None # main part of definition, unicode
      self.utf8_defi = None
      self.part_of_speech = None # part of speech code
      self.part_of_speech_str = None # string representation of the part of speech, utf-8
      self.title = None
      self.u_title = None
      self.utf8_title = None
      self.encoding = None # encoding of the definition
      self.singleEncoding = True # true if the definition was encoded with a single encoding
      self.type_6 = None
        
  class GzipWithCheck:
    """gzip.GzipFile with check. It checks that unpacked data match what was packed.
    """
    def __init__(self, gzipFile, unpackedPath, db):
      """constructor
      
      gzipFile - gzip file - archive
      unpackedPath - path of a file containing original data, for testing.
      db - reference to BGL class instance, used for logging.
      """
      self.file = BGLGzipFile(fileobj=gzipFile)
      self.unpacked_file = open(unpackedPath, 'rb')
      self.db = db
    def __del__(self):
      self.close()
    def close(self):
      if self.file != None:
        self.file.close()
        self.file = None
      if self.unpacked_file != None:
        self.unpacked_file.close()
        self.unpacked_file = None
    def read(self, size=-1):
      buf1 = self.file.read(size)
      buf2 = self.unpacked_file.read(size)
      if buf1 != buf2:
        self.db.msg_log_file_write('GzipWithCheck.read: !=: size = {2}, ({0}) ({1})'.format(buf1, buf2, size))
      #else:
        #self.db.msg_log_file_write('GzipWithCheck.read: ==: size = {2}, ({0}) ({1})'.format(buf1, buf2, size))
      return buf1
    def seek(self, offset, whence=os.SEEK_SET):
      self.file.seek(offset, whence)
      self.unpacked_file.seek(offset, whence)
      #self.db.msg_log_file_write('GzipWithCheck.seek: offset = {0}, whence = {1}'.format(offset, whence))
    def tell(self):
      pos1 = self.file.tell()
      pos2 = self.unpacked_file.tell()
      if pos1 != pos2:
        self.db.msg_log_file_write('GzipWithCheck.tell: !=: {0} {1}'.format(pos1, pos2))
      #else:
        #self.db.msg_log_file_write('GzipWithCheck.tell: ==: {0} {1}'.format(pos1, pos2))
      return pos1
    def flush(self):
      if os.sep=='\\':
        pass # A bug in Windows, after file.flush, file.read returns garbage
      else:
        self.file.flush()
        self.unpacked_file.flush()
  
  ##############################################################################
  """language properties
  
  In this short note we describe how Babylon select encoding for key words, 
  alternates and definitions.
  There are source and target encodings. The source encoding is used to encode
  keys and alternates, the target encoding is used to encode definitions.
  The source encoding is selected based on the source language of the
  dictionary, the target encoding is tied to the target language. 
  Babylon Glossary Builder allows you to specify source and target languages. 
  If you open a Builder project (a file with .gpr extension) in a text editor, 
  you should find the following elements:
  <bab:SourceCharset>Latin</bab:SourceCharset>
  <bab:SourceLanguage>English</bab:SourceLanguage>
  <bab:TargetCharset>Latin</bab:TargetCharset>
  <bab:TargetLanguage>English</bab:TargetLanguage>
  Here bab:SourceLanguage is the source language that you select in the builder
  wizard, bab:SourceCharset - is the corresponding charset. 
  bab:TargetLanguage - target language, bab:TargetCharset - corresponding
  charset.
  Unfortunately, builder does not tell us what encoding corresponds to charset, 
  but we can detect it.
  
  A few words about how definitions are encoded. If all chars of the 
  definition fall into the target charset, Babylon use that charset to encode
  the definition. If at least one char does not fall into the target charset,
  Babylon use utf-8 encoding, wrapping the definition into <charset c=U> and
  </charset> tags.
  You can make Babylon use utf-8 encoding for the whole dictionary, in that case 
  all definitions, keys and alternates are encoded with utf-8. See Babylon 
  Glossary Builder wizard, Glossary Properties tab, Advanced button, Use UTF-8
  encoding check box. Definitions are not augmented with extra mackup in this
  case, that is you'll not find charset tags in definitions.
  
  How you can tell what encoding was used for the particular definition in 
  .bgl file? You need to check the following conditions.
  
  Block type 3, code 0x11. If 0x8000 bit is set, the whole dictionary use
  utf-8 encoding.
  
  If the definition starts with <charset c=U>, that definition uses utf-8
  encoding.
  
  Otherwise you need to consult the target encoding.
  
  Block type 3, code 0x1b. That field normally contains 1 byte code of the 
  target encoding. Codes fill the range of 0x41 to 0x4e. Babylon Builder
  generate codes 0x42 - 0x4e. How to generate code 0x41? 
  Occasionally you may encounter the field value is four zero bytes. In this 
  case, I guess, the default encoding for the target language is used.
  
  Block type 3, code 0x08. That field contains 4-bytes code of the target 
  language. The first three bytes are always zero, the last byte is the code.
  Playing with Babylon Glossary builder we can find language codes corresponding 
  to target language. The language codes fill the range of 0 to 0x3d.
  
  How to detect the target encoding? Here is the technique I've used.
  - Create a babylon glossary source file ( a file with .gls extension) with 
    the following contents. Start the file with utf-8 BOM for the builder
    to recognize the utf-8 encoding. Use unicode code point code as key,
    and a single unicode chars encoding in utf-8 as definition. Create keys 
    for all code points in the range 32 - 0x10000, or you may use wider range.
    We do not use code points in the range 0-31, since they are control chars.
    You should skip the following three chars: & < >. Since the definition
    is supposed to contain html, these chars are be replaced by &amp; &lt;
    &gt; respectively. You should skip the char $ as well, it has special 
    meaning in definitions (?). Skip all code point that cannot encoded in 
    utf-8 (not all code points in the range 32-0x10000 represent valid chars).
  - Now that you have a glossary source file, process it with builder selecting
    the desired target language. Make sure the "use utf-8" option is no set.
    You'll get a .bgl file.
  - Process the generated .bgl file with pyglossary. Skip all definitions that
    start with <charset c=U> tag. Try to decode definitions using different
    encodings and match the result with the real value (key - code point char 
    code). Thus you'll find the encoding having the best match.
    
    For example, you may do the following.
    Loop over all available encodings, loop over all definitions in the 
    dictionary. Count the number of definitions that does not start with
    charset tag - total. Among them count the number of definitions that were 
    correctly decoded - success. The encoding where total == success, is 
    the target encoding.
  
  There are a few problems I encountered. It looks like python does not 
  correctly implement cp932 and cp950 encodings. For Japanese charset I 
  got 99.12% match, and for Traditional Chinese charset I got even less -
  66.97%. To conform my guess that Japanese is cp932 and Traditional Chinese
  is cp950 I built a C++ utility that worked on the data extracted from .bgl
  dictionary. I used WideCharToMultiByte function for conversion. The C++
  utility confirmed the cp932 and cp950 encodings, I got 100% match.
  
  Dictionary properties
  =====================
  
  Dictionary (or glossary) properties are textual data like glossary name, 
  glossary author name, glossary author e-mail, copyright message and
  glossary description. Most of the dictionaries have these properties set.
  Since they contain textual data we need to know the encoding.
  There may be other properties not listed here. I've enumerated only those that
  are available in Babylon Glossary builder.
  
  Playing with Babylon builder allows us detect how encoding is selected.
  If global utf-8 flag is set, utf-8 encoding is used for all properties.
  Otherwise the target encoding is used, that is the encoding corresponding to
  the target language. The chars that cannot be represented in the target encoding 
  are replaced with question marks.
  
  Using this algorithm to decode dictionary properties you may encounter that
  some of them are decoded incorrectly. For example, it is clear that the property
  is in cp1251 encoding while the algorithm says we must use cp1252, and we get 
  garbage after decoding. That is OK, the algorithm is correct. You may install 
  that dictionary in Babylon and check dictionary properties. It shows the same
  garbage. Unfortunately, we cannot detect correct encoding in this case
  automatically. We may add a parameter the will overwrite the selected encoding,
  so the user may fix the encoding if needed.
  """
  languageProps = [
    BabylonLanguage(
      language = 'English', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x00
    ),
    BabylonLanguage(
      language = 'French', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x01
    ),
    BabylonLanguage(
      language = 'Italian', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x02
    ),
    BabylonLanguage(
      language = 'Spanish', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x03
    ),
    BabylonLanguage(
      language = 'Dutch', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x04
    ),
    BabylonLanguage(
      language = 'Portuguese', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x05
    ),
    BabylonLanguage(
      language = 'German', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x06
    ),
    BabylonLanguage(
      language = 'Russian', 
      charset = 'Cyrillic', 
      encoding = 'cp1251', 
      code = 0x07
    ),
    BabylonLanguage(
      language = 'Japanese', 
      charset = 'Japanese', 
      encoding = 'cp932', 
      code = 0x08
    ),
    BabylonLanguage(
      language = 'Chinese (T)', 
      charset = 'Traditional Chinese', 
      encoding = 'cp950', 
      code = 0x09
    ),
    BabylonLanguage(
      language = 'Chinese (S)', 
      charset = 'Simplified Chinese', 
      encoding = 'cp936', 
      code = 0x0a
    ),
    BabylonLanguage(
      language = 'Greek', 
      charset = 'Greek', 
      encoding = 'cp1253', 
      code = 0x0b
    ),
    BabylonLanguage(
      language = 'Korean', 
      charset = 'Korean', 
      encoding = 'cp949', 
      code = 0x0c
    ),
    BabylonLanguage(
      language = 'Turkish', 
      charset = 'Turkish', 
      encoding = 'cp1254', 
      code = 0x0d
    ),
    BabylonLanguage(
      language = 'Hebrew', 
      charset = 'Hebrew', 
      encoding = 'cp1255', 
      code = 0x0e
    ),
    BabylonLanguage(
      language = 'Arabic', 
      charset = 'Arabic', 
      encoding = 'cp1256', 
      code = 0x0f
    ),
    BabylonLanguage(
      language = 'Thai', 
      charset = 'Thai', 
      encoding = 'cp874', 
      code = 0x10
    ),
    BabylonLanguage(
      language = 'Other', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x11
    ),
    BabylonLanguage(
      language = 'Other Simplified Chinese dialects', 
      charset = 'Simplified Chinese', 
      encoding = 'cp936', 
      code = 0x12
    ),
    BabylonLanguage(
      language = 'Other Traditional Chinese dialects', 
      charset = 'Traditional Chinese', 
      encoding = 'cp950', 
      code = 0x13
    ),
    BabylonLanguage(
      language = 'Other Eastern-European languages', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x14
    ),
    BabylonLanguage(
      language = 'Other Western-European languages', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x15
    ),
    BabylonLanguage(
      language = 'Other Russian languages', 
      charset = 'Cyrillic', 
      encoding = 'cp1251', 
      code = 0x16
    ),
    BabylonLanguage(
      language = 'Other Japanese languages', 
      charset = 'Japanese', 
      encoding = 'cp932', 
      code = 0x17
    ),
    BabylonLanguage(
      language = 'Other Baltic languages', 
      charset = 'Baltic', 
      encoding = 'cp1257', 
      code = 0x18
    ),
    BabylonLanguage(
      language = 'Other Greek languages', 
      charset = 'Greek', 
      encoding = 'cp1253', 
      code = 0x19
    ),
    BabylonLanguage(
      language = 'Other Korean dialects', 
      charset = 'Korean', 
      encoding = 'cp949', 
      code = 0x1a
    ),
    BabylonLanguage(
      language = 'Other Turkish dialects', 
      charset = 'Turkish', 
      encoding = 'cp1254', 
      code = 0x1b
    ),
    BabylonLanguage(
      language = 'Other Thai dialects', 
      charset = 'Thai', 
      encoding = 'cp874', 
      code = 0x1c
    ),
    BabylonLanguage(
      language = 'Polish', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x1d
    ),
    BabylonLanguage(
      language = 'Hungarian', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x1e
    ),
    BabylonLanguage(
      language = 'Czech', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x1f
    ),
    BabylonLanguage(
      language = 'Lithuanian', 
      charset = 'Baltic', 
      encoding = 'cp1257', 
      code = 0x20
    ),
    BabylonLanguage(
      language = 'Latvian', 
      charset = 'Baltic', 
      encoding = 'cp1257', 
      code = 0x21
    ),
    BabylonLanguage(
      language = 'Catalan', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x22
    ),
    BabylonLanguage(
      language = 'Croatian', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x23
    ),
    BabylonLanguage(
      language = 'Serbian', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x24
    ),
    BabylonLanguage(
      language = 'Slovak', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x25
    ),
    BabylonLanguage(
      language = 'Albanian', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x26
    ),
    BabylonLanguage(
      language = 'Urdu', 
      charset = 'Arabic', 
      encoding = 'cp1256', 
      code = 0x27
    ),
    BabylonLanguage(
      language = 'Slovenian', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x28
    ),
    BabylonLanguage(
      language = 'Estonian', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x29
    ),
    BabylonLanguage(
      language = 'Bulgarian', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x2a
    ),
    BabylonLanguage(
      language = 'Danish', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x2b
    ),
    BabylonLanguage(
      language = 'Finnish', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x2c
    ),
    BabylonLanguage(
      language = 'Icelandic', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x2d
    ),
    BabylonLanguage(
      language = 'Norwegian', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x2e
    ),
    BabylonLanguage(
      language = 'Romanian', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x2f
    ),
    BabylonLanguage(
      language = 'Swedish', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x30
    ),
    BabylonLanguage(
      language = 'Ukranian', 
      charset = 'Cyrillic', 
      encoding = 'cp1251', 
      code = 0x31
    ),
    BabylonLanguage(
      language = 'Belarusian', 
      charset = 'Cyrillic', 
      encoding = 'cp1251', 
      code = 0x32
    ),
    BabylonLanguage(
      language = 'Farsi', 
      charset = 'Arabic', 
      encoding = 'cp1256', 
      code = 0x33
    ),
    BabylonLanguage(
      language = 'Basque', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x34
    ),
    BabylonLanguage(
      language = 'Macedonian', 
      charset = 'Eastern European', 
      encoding = 'cp1250', 
      code = 0x35
    ),
    BabylonLanguage(
      language = 'Afrikaans', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x36
    ),
    BabylonLanguage(
      # Babylon Glossary Builder spells this language 'Faeroese'
      language = 'Faroese', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x37
    ),
    BabylonLanguage(
      language = 'Latin', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x38
    ),
    BabylonLanguage(
      language = 'Esperanto', 
      charset = 'Turkish', 
      encoding = 'cp1254', 
      code = 0x39
    ),
    BabylonLanguage(
      language = 'Tamazight', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x3a
    ),
    BabylonLanguage(
      language = 'Armenian', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x3b
    ),
    BabylonLanguage(
      language = 'Hindi', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x3c
    ),
    BabylonLanguage(
      language = 'Somali', 
      charset = 'Latin', 
      encoding = 'cp1252', 
      code = 0x3d
    ),
  ]
  
  charsets = (
    'cp1252',       # Default                0x41
    'cp1252',       # Latin                  0x42
    'cp1250',       # Eastern European       0x43
    'cp1251',       # Cyrillic               0x44
    'cp932',        # Japanese               0x45
    'cp950',        # Traditional Chinese    0x46
    'cp936',        # Simplified Chinese     0x47
    'cp1257',       # Baltic                 0x48
    'cp1253',       # Greek                  0x49
    'cp949',        # Korean                 0x4A
    'cp1254',       # Turkish                0x4B
    'cp1255',       # Hebrew                 0x4C
    'cp1256',       # Arabic                 0x4D
    'cp874'         # Thai                   0x4E
  )
  partOfSpeech = (
    # Use None for codes we have not seen yet
    # Use '' for codes we've seen but part of speech is unknown
    'n.',           # Noun           0x30
    'adj.',         # Adjective      0x31
    'v.',           # Verb           0x32
    'adv.',         # Adverb         0x33
    'interj.',      # Interjection   0x34
    'pron.',        # Pronoun        0x35
    'prep.',        # Preposition    0x36
    'conj.',        # Conjunction    0x37
    'suff.',        # Suffix         0x38
    'pref.',        # Prefix         0x39
    'art.',         # Article        0x3A
    '',             #                0x3B in Babylon Italian-English.BGL, 
                    #                     Babylon Spanish-English.BGL, 
                    #                     no indication of the part of speech
    'ר"ת',          #                0x3C # in Babylon Hebrew Thesaurus.BGL
    'ת\'/ש"ע',      # 0x3D
    'ת\'/ש"ע',      # 0x3E
    'ת\'/ש"ע',      # 0x3F
    'נ\'',          # 0x40  in Babylon Hebrew Thesaurus.BGL
    'זו"נ',         # 0x41
    'ז\'',          # 0x42  in Babylon Hebrew Thesaurus.BGL
    '',             # 0x43        in Terus Russian-Hebrew Hebrew-Russian/Terus_Heb_Rus.BGL
                    #             no indication of the part of speech
    '',             # 0x44        in Terus Russian-Hebrew Hebrew-Russian/Terus_Heb_Rus.BGL
                    #             no indication of the part of speech
    None,           # 0x45
    None,           # 0x46
    None,           # 0x47
  )

  def __init__(self, filename, 
    # resource path - where to extract embedded files
    resPath=None, 
    ## 0: print nothing
    ## 1: minimal info (for user)
    ## 2: extra info (for user)
    ## 3: debugging (for developer)
    verbose=1, 
    defaultEncodingOverwrite = None, 
    sourceEncodingOverwrite = None, 
    targetEncodingOverwrite = None,
    msgLogPath = None, 
    rawDumpPath = None, 
    decodedDumpPath = None, 
    unpackedGzipPath = None,
    searchCharSamples = False,
    charSamplesPath = None,
    testMode = False, # extra checking, may skip some steps
    noControlSequenceInDefi = False,
    strictStringConvertion = False,
    collectMetadata2 = False,
    ):
    global gVerbose
    self.verbose = verbose
    gVerbose = verbose
    self.filename = filename
    self.title = 'Untitled'
    self.author = ''
    self.email = ''
    self.description = ''
    self.copyright = ''
    self.sourceLang = ''
    self.targetLang = ''
    self.defaultCharset = ''
    self.sourceCharset = ''
    self.targetCharset = ''
    self.defaultEncodingOverwrite = defaultEncodingOverwrite
    self.sourceEncodingOverwrite = sourceEncodingOverwrite
    self.targetEncodingOverwrite = targetEncodingOverwrite
    self.sourceEncoding = None
    self.targetEncoding = None
    self.sourceLangCode = None
    self.targetLangCode = None
    self.option_utf8_encoding = None
    self.bgl_numEntries = None
    self.creationTime = ''
    self.middleUpdated = ''
    self.lastUpdated = ''
    # unicode msgs
    self.purchaseLicenseMsg = u''
    self.licenseExpiredMsg = u''
    self.purchaseAddress = u''
    self.title_wide = u'' # the same as title, but encoded in utf-16 originally
    self.author_wide = u'' # the same as author, but encoded in utf-16 originally
    # non-unicode
    self.contractions = ''
    self.aboutExt = ''
    self.aboutContents = '' # binary data
    self.wordLenMax = 0
    self.defiLenMax = 0
    self.testMode = testMode
    self.noControlSequenceInDefi = noControlSequenceInDefi
    self.strictStringConvertion = strictStringConvertion
    self.target_chars_arr = ([ False ] * 256) if searchCharSamples else None 
    self.metadata2 = MetaData2() if collectMetadata2 else None
    self.rawDumpPath = rawDumpPath
    self.dump_file = None
    self.decodedDumpPath = decodedDumpPath
    self.decoded_dump_file = None
    self.msgLogPath = msgLogPath
    self.msg_log_file = None
    self.charSamplesPath = charSamplesPath
    self.samples_dump_file = None
    self.unpackedGzipPath = unpackedGzipPath
    # apply to unicode string
    self.strip_slash_alt_key_pat = re.compile(r'(^|\s)/(\w)', re.U)
    # apply to unicode string
    self.special_char_pat = re.compile(r'[^\s\w.]', re.U)
    self.file = None
    self.writeGz = None
    # offset of gzip header, set in self.open()
    self.gzip_offset = None
    # must be a in RRGGBB format
    self.partOfSpeechColor = '007000'
    
    self.resPath = self.createResDir(resPath)
    if self.verbose >=4:
      print 'Resource path: {0}'.format(resPath)
    self.resFiles = []
  
  def createResDir(self, resPath):
    if resPath==None:
      # resPath is not specified. 
      # Try directories like:
      # self.filename + "_files"
      # self.filename + "_files_0"
      # self.filename + "_files_1"
      # self.filename + "_files_2"
      # ...
      # use the temp directory if we cannot write to the dictionary directory
      i = -1
      while True:
        if i == -1:
          resPath = '{0}_files{1}'.format(self.filename, os.sep)
        else:
          resPath = '{0}_files_{1}{2}'.format(self.filename, i, os.sep)
        if not os.path.exists(resPath) or os.path.isdir(resPath):
          break
        i += 1
      if not os.path.exists(resPath):
        try:
          os.mkdir(resPath)
        except IOError:
          myRaise(__file__)
          resPath = self.createResDirInTemp()
    else:
      if not os.path.exists(resPath):
        try:
          os.mkdir(resPath)
        except IOError:
          myRaise(__file__)
          resPath = self.createResDirInTemp()
      else:
        if not os.path.isdir(resPath):
          printAsWarning("{0} is not a directory".format(resPath))
          resPath = self.createResDirInTemp()
    return resPath
    
  def createResDirInTemp(self):
    resPath = os.path.join(tmpDir, os.path.basename(self.filename) + '_files') + os.sep
    if not os.path.isdir(resPath):
      os.mkdir(resPath)
    return resPath
  
  # open .bgl file, read signature, find and open gzipped content
  # self.file - ungzipped content
  def open(self, writeGz=False):
    with open(self.filename, 'rb') as f:
      if f==None:
        return False
      buf = f.read(6)
      if len(buf)<6 or not buf[:4] in ('\x12\x34\x00\x01','\x12\x34\x00\x02'):
        return False
      self.gzip_offset = i = binStrToInt(buf[4:6])
      if self.verbose>3:
        print 'Position of gz header: i={0}'.format(i)
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
        f2.close()
        self.file = gzip.open(self.dataFile, 'rb')
      else:
        self.file_bgl = f2 = self.FileOffS(self.filename, i)
        if self.unpackedGzipPath != None:
          self.file = self.GzipWithCheck(f2, self.unpackedGzipPath, self)
        else:
          self.file = BGLGzipFile(fileobj=f2)
    if self.rawDumpPath != None:
      self.dump_file = open(self.rawDumpPath, 'wb')
    if self.decodedDumpPath != None:
      self.decoded_dump_file = open(self.decodedDumpPath, 'wb')
    if self.msgLogPath != None:
      self.msg_log_file = open(self.msgLogPath, 'wb')
    if self.charSamplesPath != None:
      self.samples_dump_file = open(self.charSamplesPath, 'wb')
    return True
    
  def isEndOfDictData(self):
    """Test for end of dictionary data.
    
    A bgl file stores dictionary data as a gzip compressed block. 
    In other words, a bgl file stores a gzip data file inside.
    A gzip file consists of a series of "members". 
    gzip data block in bgl consists of one member (I guess).
    Testing for block type returned by self.readBlock is not a reliable way to detect the end of gzip member.
    For example, consider 'Airport Code Dictionary.BGL' dictionary.
    To reliably test for end of gzip member block we must use a number of 
    undocumented variables of gzip.GzipFile class.
    self.file._new_member - true if the current member has been completely read from the input file
    self.file.extrasize - size of buffered data
    self.file.offset - offset in the input file
    
    after reading one gzip member current position in the input file is set to the first byte after gzip data
    We may get this offset: self.file_bgl.tell()
    The last 4 bytes of gzip block contains the size of the original (uncompressed) input data modulo 2^32
    """
    if isinstance(self.file, self.GzipWithCheck):
      return self.file.file.isNewMember()
    else:
      return self.file.isNewMember()
    
  def close(self):
    if self.file != None:
      self.file.close()
      self.file = None
    # Calling a GzipFile object’s close() method does not close fileobj,
    if self.file_bgl != None:
      self.file_bgl.close()
      self.file_bgl = None
    if self.dump_file != None:
      self.dump_file.close()
      self.dump_file = None
    if self.decoded_dump_file != None:
      self.decoded_dump_file.close()
      self.decoded_dump_file = None
    if self.msg_log_file != None:
      self.msg_log_file.close()
      self.msg_log_file = None
    if self.samples_dump_file != None:
      self.samples_dump_file.close()
      self.samples_dump_file = None
  
  # returns False if error
  def readBlock(self, block):
    block.offset = self.file.tell()
    length = self.readBytes(1)
    if length==-1:
      printAsError('readBlock: length = -1')
      return False
    block.Type = length & 0xf
    length >>= 4
    if length < 4:
      length = self.readBytes(length+1)
      if length == -1:
        printAsError('readBlock: length = -1')
        return False
    else:
      length -= 4
    self.file.flush()
    if length > 0:
      try:
        block.data = self.file.read(length)
      except:#??????????????????
        ##???????? struct.error: unpack requires a string argument of length 4
        myRaise(__file__)
        print 'readBlock: read failed: self.numBlocks = {0}, length = {1}, self.file.tell() = {2}'\
        .format(self.numBlocks, length, self.file.tell())
        block.data = ''
        return False
    else:
      block.data = ''
    return True
  
  # return -1 if error
  def readBytes(self, bytes):
    val=0
    if bytes<1 or bytes>4:
      printAsError('readBytes: invalid argument bytes {0}'.format(bytes))
      return -1
    self.file.flush()
    buf = self.file.read(bytes)
    if len(buf)==0:
      printAsError('readBytes: end of file: len(buf)==0')
      return -1
    if len(buf)!=bytes:
      printAsError('readBytes: to read bytes = {0} , actually read bytes = {1}'.format(bytes, len(buf)))
      return -1
    return binStrToInt(buf)
    
  # read meta information about the dictionary: author, description, source and target languages, etc
  # (articles are not read)
  def read(self):
    self.numEntries = 0
    self.numBlocks = 0
    deferred_block2_num = 0
    block = self.Block()
    while not self.isEndOfDictData():
      if not self.readBlock(block):
        break
      self.numBlocks += 1
      if block.data=='':
        continue
      word=''
      #defi=''
      if block.Type==0:
        self.read_type_0(block)
      elif block.Type in (1,7,10,11,13):
        self.numEntries += 1
      elif block.Type==2:
        if not self.read_type_2(block, 1):
          deferred_block2_num += 1
      elif block.Type==3:
        self.read_type_3(block)
      else:## Unknown block.Type
        self.unknownBlock(block)
    self.file.seek(0)
    ################
    self.detect_encoding()
    
    if deferred_block2_num > 0:
      # process deferred type 2 blocks
      if self.verbose>1:
        print 'processing type 2 blocks, second pass'
      while not self.isEndOfDictData():
        if not self.readBlock(block):
          break
        if block.data=='':
          continue
        if block.Type==2:
          self.read_type_2(block, 2)
      self.file.seek(0)
    
    #######
    self.title = self.toUtf8(self.title, self.targetEncoding)
    self.author = self.toUtf8(self.author, self.targetEncoding)
    self.email = self.toUtf8(self.email, self.targetEncoding)
    self.copyright = self.toUtf8(self.copyright, self.targetEncoding)
    self.description = self.toUtf8(self.description, self.targetEncoding)
    # self.purchaseLicenseMsg - unicode
    # self.licenseExpiredMsg  - unicode
    # self.purchaseAddress    - unicode
    # self.title_wide         - unicode
    # self.author_wide        - unicode
    # self.contractions ?

    if self.verbose>0:
      print 'numEntries = {0}'.format(self.numEntries)
      if self.bgl_numEntries!=self.numEntries:
        # There are a number of cases when these numbers do not match.
        # The dictionary is OK, and these is no doubt that we might missed an entry.
        # self.bgl_numEntries may be less than the number of entries we've read.
        print 'bgl_numEntries = {0} (!!!!!!!!!)'.format(self.bgl_numEntries)
      if self.verbose>1:
        print 'numBlocks = {0}'.format(self.numBlocks)
      print 'defaultCharset = {0}'.format(self.defaultCharset)
      print 'sourceCharset = {0}'.format(self.sourceCharset)
      print 'targetCharset = {0}'.format(self.targetCharset)
      print
      print 'sourceLang = {0}'.format(self.sourceLang)
      print 'targetLang = {0}'.format(self.targetLang)
      print
      print 'creationTime = {0}'.format(self.creationTime)
      print 'middleUpdated = {0}'.format(self.middleUpdated) ## ???????????????
      print 'lastUpdated = {0}'.format(self.lastUpdated)
    self.numBlocks = 0
    
    # remove resource directory if it's empty
    if len(os.listdir(self.resPath))==0:
      try:
        os.rmdir(self.resPath)
      except:
        myRaise(__file__)
    return True

  def read_type_0(self, block):
    x = ord(block.data[0])
    
    if x==2:
      # this number is vary close to self.bgl_numEntries, but does not always equal to the number of entries
      # see self.read_type_3, x == 12 as well
      num = binStrToInt(block.data[1:])
    elif x==8:
      value = binStrToInt(block.data[1:])
      if value >= 0x41:
        value -= 0x41
        if value < len(self.charsets):
          self.defaultCharset = self.charsets[value]
        else:
          printAsWarning('read_type_0: unknown defaultCharset {0}'.format(value))
    elif self.verbose>3:
      self.unknownBlock(block)
      return False
    return True
  
  def read_type_2(self, block, pass_num):
    """Process type 2 block
    
    Type 2 block is an embedded file (mostly Image or HTML).
    pass_num - pass number, may be 1 or 2
    On the first pass self.sourceEncoding is not defined and we cannot decode file names.
    That is why the second pass is needed. The second pass is costly, it 
    apparently increases total processing time. We should avoid the second pass if possible.
    Most of the dictionaries do not have valuable resources, and those that do, use
    file names consisting only of ASCII characters. We may process these resources
    on the second pass. If all files have been processed on the first pass,
    the second pass is not needed.
    
    All dictionaries I've processed so far use only ASCII chars in file names.
    Babylon glossary builder replaces names of files, like links to images, 
    with what looks like a hash code of the file name, for example "8FFC5C68.png".
    
    Return value: True if the resource was successfully processed,
      False - second pass is needed.
    """
    ## Embedded File (mostly Image or HTML)
    name='' ## Embedded file name
    cont='' ## Embedded file content
    pos = 0
    ## name:
    Len = ord(block.data[pos]) 
    pos+=1
    if pos+Len > len(block.data):
      printAsWarning('read_type_2: name too long')
      return True
    name += block.data[pos:pos+Len]
    pos += Len
    if name in ('C2EEF3F6.html', '8EAF66FD.bmp'):
      if self.verbose>1 and pass_num == 1:
        print 'Skipping non-useful file "{0}"'.format(name)
      return True
    if isASCII(name):
      if pass_num > 1:
        return True # processed on the first pass
      # else decoding is not needed
    else:
      if pass_num == 1:
        return False # cannot process now, sourceEncoding is undefined
      else:
        name = self.toUtf8(name, self.sourceEncoding)
    ## cont:
    cont = block.data[pos:]
    path = os.path.join(self.resPath, name)
    with open(path, 'wb') as f:
      f.write(cont)
    self.resFiles.append(name)
    return True
        
  def read_type_3(self, block):
    x = binStrToInt(block.data[0:2])
    pos=2
    if x==0x01:
      # glossary name
      self.title = block.data[pos:]
    elif x==0x02:
      # glossary author name
      # a list of '|'-separated values
      self.author = block.data[pos:]
    elif x==0x03:
      # glossary author e-mail
      self.email = block.data[pos:]
    elif x==0x04:
      # copyright message
      self.copyright = block.data[pos:]
    elif x==0x07:
      value = binStrToInt(block.data[pos:])
      self.sourceLangCode = value
      if value < len(self.languageProps):
        self.sourceLang = self.languageProps[value].language
      else:
        printAsWarning('read_type_3: unknown sourceLangCode = {0}'.format(value))
    elif x==0x08:
      value = binStrToInt(block.data[pos:])
      self.targetLangCode = value
      if value < len(self.languageProps):
        self.targetLang = self.languageProps[value].language
      else:
        printAsWarning('read_type_3: unknown targetLangCode = {0}'.format(value))
    elif x==0x09:
      # Glossary description
      self.description = block.data[pos:]
    elif x==0x0a:
      """
      value = 0 - browsing disabled
      value = 1 - browsing enabled
      """
      value = ord(block.data[pos])
      browsing_enabled = value != 0
    elif x==0x0b:
      """Glossary icon
      """
    elif x==0x0c:
      # this does not always matches the number of entries in the dictionary,
      # but it's close to it.
      # the difference is usually +- 1 or 2, in rare cases may be 9, 29 and more
      self.bgl_numEntries = binStrToInt(block.data[pos:])
    elif x==0x11:
      """A flag field.
      """
      flags = binStrToInt(block.data[pos:])
      # when this flag is set utf8 encoding is used for all articles
      # when false, the encoding is set according to the source and target alphabet
      self.option_utf8_encoding = (flags & 0x8000) != 0
      # Determines whether the glossary offers spelling alternatives for searched terms
      spelling_alternatives = (flags & 0x10000) == 0 
      # defines if the search for terms in this glossary is case sensitive
      # see code 0x20 as well
      case_sensitive = (flags & 0x1000) != 0
    elif x==0x14:## Creation Time
      jd1970 = gregorian.to_jd(1970, 1, 1)
      (djd, hm) = divmod(binStrToInt(block.data[2:]), (24*60))
      (year, month, day) = gregorian.jd_to(djd+jd1970)
      (hour, minute) = divmod(hm, 60)
      self.creationTime = '%.2d/%.2d/%.2d, %.2d:%.2d'%(year, month, day, hour, minute)
    elif x==0x1a:
      value = ord(block.data[2])
      if value >= 0x41:
        value -= 0x41
        if value < len(self.charsets):
          self.sourceCharset = self.charsets[value]
        else:
          printAsWarning('read_type_3: unknown sourceCharset {0}'.format(value))
    elif x==0x1b:
      value = ord(block.data[2])
      if value >= 0x41:
        value -= 0x41
        if value < len(self.charsets):
          self.targetCharset = self.charsets[value]
        else:
          printAsWarning('read_type_3: unknown targetCharset {0}'.format(value))
    elif x==0x1c:## Middle Updated ## ???????????????
      jd1970 = gregorian.to_jd(1970, 1, 1)
      (djd, hm) = divmod(binStrToInt(block.data[2:]), 24*60)
      (year, month, day) = gregorian.jd_to(djd+jd1970)
      (hour, minute) = divmod(hm, 60)
      self.middleUpdated = '%.2d/%.2d/%.2d, %.2d:%.2d'%(year, month, day, hour, minute)
    elif x==0x20:
      """
      0x30 - case sensitive search is disabled
      0x31 - case sensitive search is enabled
      see code 0x11 as well
      """
      if len(block.data) > pos: 
        value = ord(block.data[pos])
    elif x==0x2c:
      # contains a value like this: 
      # In order to view this glossary, you must purchase a license.
      # <br /><a href="http://www.babylon.com/redirects/purchase.cgi?type=170&trid=BPCWHAR">Click here</a> to purchase.
      msg = self.read_type_3_message(block)
      if msg != None:
        self.purchaseLicenseMsg = msg
    elif x==0x2d:
      # contains a value like this: 
      # Your license for this glossary has expired. 
      # In order to view this glossary, you must have a valid license. <br><a href="http://www.babylon.com/redirects/purchase.cgi?type=130&trid=BPCBRTBR">Renew</a> your license today.
      msg = self.read_type_3_message(block)
      if msg != None:
        self.licenseExpiredMsg = msg
    elif x==0x2e:
      # contains a value like this:
      # http://www.babylon.com/redirects/purchase.cgi?type=169&trid=BPCOT
      # or
      # mailto:larousse@babylon.com
      msg = self.read_type_3_message(block)
      if msg != None:
        self.purchaseAddress = msg
    elif x==0x30:
      msg = self.read_type_3_message(block)
      if msg != None:
        self.title_wide = msg
    elif x==0x31:
      # a list of '|'-separated values
      msg = self.read_type_3_message(block)
      if msg != None:
        self.author_wide = msg
    elif x==0x33:## Last Updated
      jd1970 = gregorian.to_jd(1970, 1, 1)
      (djd, hm) = divmod(binStrToInt(block.data[2:]), 24*60)
      (year, month, day) = gregorian.jd_to(djd+jd1970)
      (hour, minute) = divmod(hm, 60)
      self.lastUpdated = '%.2d/%.2d/%.2d, %.2d:%.2d'%(year, month, day, hour, minute)
    elif x==0x3b: # contractions
      # contains a value like this:
      # V-0#Verb|V-0.0#|V-0.1#Infinitive|V-0.1.1#|V-1.0#|V-1.1#|V-1.1.1#Present Simple|V-1.1.2#Present Simple (3rd pers. sing.)|V-2.0#|V-2.1#|V-2.1.1#Past Simple|V-3.0#|V-3.1#|V-3.1.1#Present Participle|V-4.0#|V-4.1#|V-4.1.1#Past Participle|V-5.0#|V-5.1#|V-5.1.1#Future|V2-0#|V2-0.0#|V2-0.1#Infinitive|V2-0.1.1#|V2-1.0#|V2-1.1#|V2-1.1.1#Present Simple (1st pers. sing.)|V2-1.1.2#Present Simple (2nd pers. sing. & plural forms)|V2-1.1.3#Present Simple (3rd pers. sing.)|V2-2.0#|V2-2.1#|V2-2.1.1#Past Simple (1st & 3rd pers. sing.)|V2-2.1.2#Past Simple (2nd pers. sing. & plural forms)|V2-3.0#|V2-3.1#|V2-3.1.1#Present Participle|V2-4.0#|V2-4.1#|V2-4.1.1#Past Participle|V2-5.0#|V2-5.1#|V2-5.1.1#Future||N-0#Noun|N-1.0#|N-1.1#|N-1.1.1#Singular|N-2.0#|N-2.1#|N-2.1.1#Plural|N4-1.0#|N4-1.1#|N4-1.1.1#Singular Masc.|N4-1.1.2#Singular Fem.|N4-2.0#|N4-2.1#|N4-2.1.1#Plural Masc.|N4-2.1.2#Plural Fem.||ADJ-0#Adjective|ADJ-1.0#|ADJ-1.1#|ADJ-1.1.1#Adjective|ADJ-1.1.2#Comparative|ADJ-1.1.3#Superlative||
      # value format: (<contraction> '#' [<value>] '|')+
      # The value is in second language, that is for Babylon Russian-English.BGL the value in russian,
      # for Babylon English-Spanish.BGL the value is spanish (I guess), etc.
      if len(block.data) > 2:
        self.contractions = block.data[pos:]
    elif x==0x3d:
      # contains a value like this:
      # Arial Unicode MS
      # or
      # Tahoma
      self.fontName = block.data[pos:]
    elif x==0x41:
      """
      Glossary manual file
      additional information about the dictionary
      in .txt format this may be short info like this:
      
      Biology Glossary
      Author name: Hafez Divandari
      Author email: hafezdivandari@gmail.com
      ===========================================
      A functional glossary for translating
      English biological articles to fluent Farsi
      ===========================================
      Copyright (c) 2009 All rights reserved.      
      
      in .pdf format this may be a quite large document (about 30 pages),
      an introduction into the dictionary. It describing structure of an article, 
      editors, how to use the dictionary.
      
      format <file extension> '\x00' <file contents>
      file extension may be: '.txt', '.pdf'
      """
      if len(block.data) > pos:
        i = block.data.find('\x00', pos)
        if i == -1:
          printAsWarning('read_type_3: no file extension')
        else:
          self.aboutExt = block.data[pos:i]
          self.aboutContents = block.data[i+1:]
    elif x==0x43:
      """
      The length of the substring match in a term.
      For example, if your glossary contains the term "Dog" and the substring length is 2,
      search of the substrings "Do" or "og" will retrieve the term dog.
      Use substring length 0 for exact match.
      """
      length = binStrToInt(block.data[pos:])
    elif self.verbose>3:
      self.unknownBlock(block)
      return False
    return True
      # print 'Unknown info type x=%s,  block.Type=%s,  len(block.data)=%s'%\
        # (x, block.Type, len(block.data))
      #open('%s-block.%s.%s'%(self.numBlocks, x, block.Type), 'w').write(block.data)

  # block type = 3
  # block format: <2 byte code1><2 byte code2>
  # if code2 == 0: then the block ends
  # if code2 == 1: then the block continues as follows:
  # <4 byte len1> \x00 \x00 <message in utf-16>
  # len1 - length of message in 2-byte chars
  #
  # return value: 
  # uncode message if success, None otherwise
  def read_type_3_message(self, block):
    x = binStrToInt(block.data[0:2])
    pos = 2
    y = binStrToInt(block.data[pos:pos+2])
    pos += 2
    if y == 0:
      if len(block.data) != pos:
        printAsWarning('read_type_3_message: x = {0}. unexpected block size = {1}'.format(x, len(block.data)))
    elif y == 1:
      z = binStrToInt(block.data[pos:pos+4])
      pos += 4
      a = binStrToInt(block.data[pos:pos+2])
      pos += 2
      if a != 0:
        printAsWarning('read_type_3_message: x = {0}. a = {1} != 0'.format(x, a))
      if 2*z != len(block.data)-pos:
        printAsWarning('read_type_3_message: x = {0}. z = {1} does not match block size'.format(x, a))
      else:
        return block.data[pos:].decode('utf16')
    else:
      printAsWarning('read_type_3_message: x = {0}. unknown value y = {1}'.format(x, y))
    return None
    
  def detect_encoding(self):
    """ assign self.sourceEncoding and self.targetEncoding
    """
    if self.sourceEncodingOverwrite != None:
      self.sourceEncoding = self.sourceEncodingOverwrite
    elif self.option_utf8_encoding != None and self.option_utf8_encoding:
      self.sourceEncoding = 'utf8'
    elif self.sourceCharset != '':
      self.sourceEncoding = self.sourceCharset
    elif self.sourceLangCode != None and self.sourceLangCode < len(self.languageProps):
      self.sourceEncoding = self.languageProps[self.sourceLangCode].encoding
    else:
      self.sourceEncoding = 'cp1252'
    
    if self.targetEncodingOverwrite != None:
      self.targetEncoding = self.targetEncodingOverwrite
    elif self.option_utf8_encoding != None and self.option_utf8_encoding:
      self.targetEncoding = 'utf8'
    elif self.targetCharset != '':
      self.targetEncoding = self.targetCharset
    elif self.targetLangCode != None and self.targetLangCode < len(self.languageProps):
      self.targetEncoding = self.languageProps[self.targetLangCode].encoding
    else:
      self.targetEncoding = 'cp1252'
      
    # not used
    if self.defaultEncodingOverwrite != None:
      self.defaultEncoding = self.defaultEncodingOverwrite
    elif self.defaultCharset != '':
      self.defaultEncoding = self.defaultCharset
    else:
      self.defaultEncoding = 'cp1252'
      
  def dump_blocks(self, dumpPath):
    self.file.seek(0)
    metaData = MetaData()
    metaData.numFiles = 0
    metaData.gzip_beg_offset = self.gzip_offset

    self.numEntries = 0
    self.numBlocks = 0
    range_type = None
    range_count = 0
    block = self.Block()
    while not self.isEndOfDictData():
      #print 'readBlock offset {0:#X}'.format(self.file.unpacked_file.tell())
      #print 'readBlock offset {0:#X}'.format(self.file.tell())
      if not self.readBlock(block):
        break
      self.numBlocks += 1
      
      if block.Type in (1,7,10,11,13):
        self.numEntries += 1
      elif block.Type==2: ## Embedded File (mostly Image or HTML)
        metaData.numFiles += 1
      
      if block.Type in (1,2,7,10,11,13):
        if range_type == block.Type:
          range_count += 1
        else:
          if range_count > 0:
            mblock = MetaDataRange(range_type, range_count)
            metaData.blocks.append(mblock)
            range_count = 0
          range_type = block.Type
          range_count = 1
      else:
        if range_count > 0:
          mblock = MetaDataRange(range_type, range_count)
          metaData.blocks.append(mblock)
          range_count = 0
        mblock = MetaDataBlock(block.data, block.Type)
        metaData.blocks.append(mblock)

    if range_count > 0:
      mblock = MetaDataRange(range_type, range_count)
      metaData.blocks.append(mblock)
      range_count = 0

    metaData.numEntries = self.numEntries
    metaData.numBlocks = self.numBlocks
    metaData.gzip_end_offset = self.file_bgl.tell()
    metaData.file_size = os.path.getsize(self.filename)
    with open(self.filename, 'rb') as f:
      metaData.bgl_header = f.read(self.gzip_offset)

    with open(dumpPath, 'wb') as f:
      pickle.dump(metaData, f)

    self.file.seek(0)
  
  def dump_metadata2(self, dumpPath):
    if self.metadata2 == None:
      return
    with open(dumpPath, 'wb') as f:
      pickle.dump(self.metadata2, f)
    
  def unknownBlock(self, block):
    pass
    #print 'Block: type=%s,  data_length=%s,  number=%s'\
    #  %(block.Type, len(block.data), self.numBlocks)
  
  # return True if an entry has been read
  def readEntry(self, entry):
    if self.file==None:
      return False
    block = self.Block()
    while not self.isEndOfDictData():
      if not self.readBlock(block):
        break
      if block.data != '' and block.Type in (1, 7, 10, 11, 13):
        pos = 0
        ## word:
        [res, pos, word, raw_key] = self.readEntry_word(block, pos)
        if not res:
          continue
        ## defi:
        [res, pos, defi, key_defi] = self.readEntry_defi(block, pos, raw_key)
        if not res:
          continue
        # now pos points to the first char after definition
        [res, pos, alts] = self.readEntry_alts(block, pos, raw_key, word)
        if not res:
          continue
        entry.word = word
        entry.defi = defi
        entry.alts = alts      
        return True
    return False
  
  def readEntry_word(self, block, pos):
    """Read word part of entry.
    
    Return value is a list.
    [False, None, None, None] if error
    [True, pos, word, raw_key] if OK
    """
    Err = [False, None, None, None]
    if block.Type == 11:
      if pos + 5 > len(block.data):
        printAsError('readEntry[{0:#X}]: reading word size: pos + 5 > len(block.data)'\
        .format(block.offset))
        return Err
      Len = binStrToInt(block.data[pos:pos+5])
      pos += 5
    else:
      if pos + 1 > len(block.data):
        printAsError('readEntry[{0:#X}]: reading word size: pos + 1 > len(block.data)'\
        .format(block.offset))
        return Err
      Len = ord(block.data[pos])
      pos += 1
    if pos + Len > len(block.data):
      printAsError('readEntry[{0:#X}]: reading word: pos + Len > len(block.data)'\
      .format(block.offset))
      return Err
    raw_key = block.data[pos:pos+Len]
    self.dump_file_write_text('\n\nblock type = ' + str(block.Type) + '\n' + 'key = ')
    self.dump_file_write_data(raw_key)
    word = self.processEntryKey(raw_key)
    """Entry keys may contain html text, for example,
    ante<font face'Lucida Sans Unicode'>&lt; meridiem
    arm und reich c=t&gt;2003;</charset></font>und<font face='Lucida Sans Unicode'>
    etc.
    Babylon does not process keys as html, it display them as is.
    Html in keys is the problem of that particular dictionary.
    We should not process keys as html, since Babylon do not process them as such.
    """
    pos += Len
    self.wordLenMax = max(self.wordLenMax, len(word))
    return [True, pos, word, raw_key]
    
  def readEntry_defi(self, block, pos, raw_key):
    Err = [False, None, None, None]
    if block.Type == 11:
      if pos + 8 > len(block.data):
        printAsError('readEntry[{0:#X}]: reading defi size: pos + 8 > len(block.data)'\
        .format(block.offset))
        return Err
      pos += 4 # binStrToInt(block.data[pos:pos+4]) - may be 0, 1
      Len = binStrToInt(block.data[pos:pos+4])
      pos += 4
    else:
      if pos + 2 > len(block.data):
        printAsError('readEntry[{0:#X}]: reading defi size: pos + 2 > len(block.data)'\
        .format(block.offset))
        return Err
      Len = binStrToInt(block.data[pos:pos+2])
      pos += 2
    if pos + Len > len(block.data):
      printAsError('readEntry[{0:#X}]: reading defi: pos + Len > len(block.data)'\
      .format(block.offset))
      return Err
    raw_defi = block.data[pos:pos+Len]
    self.dump_file_write_text('\n' + 'defi = ')
    self.dump_file_write_data(raw_defi)
    defi = self.processEntryDefinition(raw_defi, raw_key)
    self.defiLenMax = max(self.defiLenMax, len(raw_defi))
    
    pos += Len
    return [True, pos, defi, raw_defi]
  
  def readEntry_alts(self, block, pos, raw_key, key):
    Err = [False, None, None]
    # use set instead of list to prevent duplicates
    alts = set()
    while pos < len(block.data):
      if block.Type == 11:
        if pos + 4 > len(block.data):
          printAsError('readEntry[{0:#X}]: reading alt size: pos + 4 > len(block.data)'\
          .format(block.offset))
          return Err
        Len = binStrToInt(block.data[pos:pos+4])
        pos += 4
        if Len == 0:
          if pos + Len != len(block.data):
            # no evidence
            printAsWarning('readEntry[{0:#X}]: reading alt size: pos + Len != len(block.data)'\
            .format(block.offset))
          break
      else:
        if pos + 1 > len(block.data):
          printAsError('readEntry[{0:#X}]: reading alt size: pos + 1 > len(block.data)'\
          .format(block.offset))
          return Err
        Len = ord(block.data[pos])
        pos += 1
      if pos + Len > len(block.data):
        printAsError('readEntry[{0:#X}]: reading alt: pos + Len > len(block.data)'\
        .format(block.offset))
        return Err
      raw_alt = block.data[pos:pos+Len]
      self.dump_file_write_text('\n' + 'alt = ')
      self.dump_file_write_data(raw_alt)
      alt = self.processEntryAlternativeKey(raw_alt, raw_key)
      # Like entry key, alt is not processed as html by babylon, so do we.
      alts.add(alt)
      pos += Len
    if key in alts:
      alts.remove(key)
    return [True, pos, list(alts)]
    
  def toUtf8(self, text, encoding):
    if self.strictStringConvertion:
      try:
        u_text = text.decode(encoding)
      except UnicodeError:
        self.msg_log_file_write('toUtf8({0}):\nconversion error:\n{1}'\
        .format(text, ExcMessage()))
        u_text = text.decode(encoding, 'ignore')
    else:
      u_text = text.decode(encoding, 'ignore')
    return u_text.encode('utf-8')
    
  def replace_html_entries(self, text):
    # &ldash;
    # &#0147;
    # &#x010b;
    pat_entry = re.compile("(?:&#x|&#|&)(\\w+);?", re.I)
    return re.sub(pat_entry, replace_html_entry, text)
    
  def decode_charset_tags(self, text, defaultEncoding):
    """Decode html text taking into account charset tags and default encoding.
    
    Return value: [utf8-text, defaultEncodingOnly]
    The second parameter is true if the text contains parts encoded with 
    non-default encoding.
    """
    pat = re.compile("(<charset\\s+c\\=['\"]?(\\w)['\"]?>|</charset>)", re.I)
    parts = re.split(pat, text)
    utf8_text = ''
    encodings = [] # stack of encodings
    defaultEncodingOnly = True
    for i in xrange(len(parts)):
      if i % 3 == 0: # text block
        encoding = encodings[-1] if len(encodings) > 0 else defaultEncoding
        text2 = parts[i]
        if encoding == 'babylon-reference':
          m = re.match('([0-9a-fA-F]+);?', text2)
          if m:
            utf8_text += replace_babylon_char_ref(m)
          else:
            self.msg_log_file_write('decode_charset_tags({0})\n'
              'invalid <charset c=t> character reference ({1})\n'
              .format(text, text2))
            u_text = text2.decode(defaultEncoding, 'replace')
            utf8_text += u_text.encode('utf-8')
        else:
          if self.strictStringConvertion:
            try:
              u_text = text2.decode(encoding)
            except UnicodeError:
              self.msg_log_file_write('decode_charset_tags({0})\n'
                'fragment({1})\n'
                'conversion error:\n{2}'\
                .format(text, text2, ExcMessage()))
              u_text = text2.decode(encoding, 'replace')
          else:
            u_text = text2.decode(encoding, 'replace')
          utf8_text += u_text.encode('utf-8')
          if encoding != defaultEncoding:
            defaultEncodingOnly = False
      elif i % 3 == 1: # <charset...> or </charset>
        if parts[i].startswith('</'):
          # </charset>
          if len(encodings) > 0:
            del encodings[-1]
          else:
            self.msg_log_file_write('decode_charset_tags({0})\n'
              'unbalanced </charset> tag\n'\
              .format(text))
        else:
          # <charset c="?">
          c = parts[i+1].lower()
          if c == 't':
            encodings.append('babylon-reference')
          elif c == 'u':
            encodings.append('utf-8')
          elif c == 'k':
            encodings.append(self.sourceEncoding)
          elif c == 'e':
            encodings.append(self.sourceEncoding)
          else:
            self.msg_log_file_write('decode_charset_tags({0})\n'
              'unknown charset code = {1}\n'\
              .format(text, c))
      else:
        # c attribute of charset tag if the previous tag was charset
        pass
    if len(encodings) > 0:
      self.msg_log_file_write('decode_charset_tags({0})\n'
        'unclosed <charset...> tag\n'\
        .format(text))
    return [utf8_text, defaultEncodingOnly]
  
  def remove_control_chars(self, text):
    # \x09 - tab
    # \x0a - line feed
    # \x0b - vertical tab
    # \x0d - carriage return
    return re.sub("[\x00-\x08\x0c\x0e-\x1f]", '', text)
  
  def replace_new_lines(self, text):
    return re.sub("[\r\n]+", ' ', text)
    
  def normalize_new_lines(self, text):
    """convert new lines to unix style and remove consecutive new lines
    """
    return re.sub("[\r\n]+", "\n", text)
    
  def replace_dingbats(self, text):
    """
    In babylon 0x8b - 0x95 codepoints are displayed as (code - 0x8b) interger in black cyrcle
    They may be replaced with unicode chars: U+24FF, U+2776 - U+277F
    code point names:
    0 - Negative circled digit zero,
    1 - Dingbat negative circled digit one,
    ...
    10 - Dingbat negative circled digit ten
    See http://www.alanwood.net/demos/wingdings.html
    """
    u_text = text.decode('utf-8')
    u_text = re.sub(u"[\u008c-\u0095]", replace_dingbat, u_text)
    u_text = u_text.replace(u"\u008b", u"\u24ff")
    return u_text.encode('utf-8')
    
  def processEntryKey(self, word):
    """Return entry key in utf-8 encoding
    """
    (main_word, strip_cnt) = self.stripDollarIndexes(word)
    if strip_cnt > 1:
      self.msg_log_file_write('processEntryKey({0}):\nnumber of dollar indexes = {1}'\
      .format(word, strip_cnt))
    # convert to unicode
    if self.strictStringConvertion:
      try:
        u_main_word = main_word.decode(self.sourceEncoding)
      except UnicodeError:
        self.msg_log_file_write('processEntryKey({0}):\nconversion error:\n{1}'\
        .format(word, ExcMessage()))
        u_main_word = main_word.decode(self.sourceEncoding, 'ignore')
    else:
      u_main_word = main_word.decode(self.sourceEncoding, 'ignore')
      
    self.decoded_dump_file_write(u'\n\nkey: ' + u_main_word)
    utf8_main_word = u_main_word.encode('utf-8')
    utf8_main_word = self.remove_control_chars(utf8_main_word)
    utf8_main_word = self.replace_new_lines(utf8_main_word)
    utf8_main_word = utf8_main_word.strip()
    return utf8_main_word

  def processEntryAlternativeKey(self, raw_word, raw_key):
    (main_word, strip_cnt) = self.stripDollarIndexes(raw_word)
    # convert to unicode
    if self.strictStringConvertion:
      try:
        u_main_word = main_word.decode(self.sourceEncoding)
      except UnicodeError:
        self.msg_log_file_write('processEntryAlternativeKey({0})\nkey = {1}:\nconversion error:\n{2}'\
        .format(raw_word, raw_key, ExcMessage()))
        u_main_word = main_word.decode(self.sourceEncoding, 'ignore')
    else:
      u_main_word = main_word.decode(self.sourceEncoding, 'ignore')
    
    # strip '/' before words
    u_main_word = re.sub(self.strip_slash_alt_key_pat, r'\1\2', u_main_word)
    
    self.decoded_dump_file_write(u'\nalt: ' + u_main_word)
    
    utf8_main_word = u_main_word.encode('utf-8')
    utf8_main_word = self.remove_control_chars(utf8_main_word)
    utf8_main_word = self.replace_new_lines(utf8_main_word)
    utf8_main_word = utf8_main_word.strip()
    return utf8_main_word
  
  def stripDollarIndexes(self, word):
    i = 0
    main_word = ''
    strip_cnt = 0 # number of sequences found
    # strip $<index>$ sequences
    while True:
      d0 = word.find('$', i)
      if d0 == -1:
        main_word += word[i:]
        break
      d1 = word.find('$', d0+1)
      if d1 == -1:
        #self.msg_log_file_write('stripDollarIndexes({0}):\n'
          #'paired $ is not found'.format(word))
        main_word += word[i:]
        break
      if d1 == d0+1:
        """
        You may find keys (or alternative keys) like these:
        sur l'arbre$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        obscurantiste$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        They all end on a sequence of '$', key length including dollars is always 60 chars.
        You may find keys like these:
        extremidade-$$$-$$$-linha
        .FIRM$$$$$$$$$$$$$
        etc
        
        summary: we must remove any sequence of dollar signs longer than 1 chars
        """
        #self.msg_log_file_write('stripDollarIndexes({0}):\n'
          #'found $$'.format(word))
        main_word += word[i:d0]
        i = d1 + 1
        while i < len(word) and word[i] == '$':
          i += 1
        if i >= len(word):
          break
        continue
      ok = True
      for x in word[d0+1:d1]:
        if x not in '0123456789':
          #self.msg_log_file_write('stripDollarIndexes({0}):\n'
            #'non-digit between $$'.format(word))
          ok = False
          break
      if not ok:
        main_word += word[i:d1]
        i = d1
        continue
      if d1+1 < len(word) and word[d1+1] != ' ':
        self.msg_log_file_write('stripDollarIndexes({0}):\n'
          'second $ is followed by non-space'.format(word))
      main_word += word[i:d0]
      i = d1+1
      strip_cnt += 1
    
    return [ main_word, strip_cnt ]
  
  def findDefinitionTrailingFields(self, defi):
    """Find the beginning of the definition trailing fields.
    
    Return value is the index of the first chars of the field set,
    or -1 if the field set is not found.
    
    Normally '\x14' should signal the beginning of the definition fields,
    but some articles may contain this characters inside, so we get false match.
    As a workaround we may check the following chars. If '\x14' is followed 
    by space, we assume this is part of the article and continue search.
    Unfortunately this does no help in many cases...
    """
    b = 0
    while True:
      i = defi.find('\x14', b)
      if i == -1:
        return -1
      if i + 1 < len(defi) and defi[i+1] == ' ':
        b = i + 1
        continue
      else:
        return i
    
  def processEntryDefinition(self, defi, raw_key):
    fields = self.DefinitionFields()
    if self.noControlSequenceInDefi:
      d0 = -1
    else:
      d0 = self.findDefinitionTrailingFields(defi)
    if d0 != -1:
      fields.defi = defi[:d0]
      self.processEntryDefinitionTrailingFields(defi, raw_key, d0, fields)
    else:
      fields.defi = defi
    [fields.utf8_defi, fields.singleEncoding] = self.decode_charset_tags(fields.defi, self.targetEncoding)
    if fields.singleEncoding:
      fields.encoding = self.targetEncoding
    fields.utf8_defi = self.fixImgLinks(fields.utf8_defi)
    fields.utf8_defi = self.replace_html_entries(fields.utf8_defi)
    fields.utf8_defi = self.replace_dingbats(fields.utf8_defi)
    fields.utf8_defi = self.remove_control_chars(fields.utf8_defi)
    fields.utf8_defi = self.normalize_new_lines(fields.utf8_defi)
    fields.utf8_defi = fields.utf8_defi.strip()
    fields.u_defi = fields.utf8_defi.decode('utf-8')
    
    if fields.title != None:
      [fields.utf8_title, singleEncoding] = self.decode_charset_tags(fields.title, self.sourceEncoding)
      fields.utf8_title = self.replace_html_entries(fields.utf8_title)
      fields.utf8_title = self.remove_control_chars(fields.utf8_title)
      fields.u_title = fields.utf8_title.decode('utf-8')
    
    if fields.part_of_speech != None:
      fields.part_of_speech_str = self.partOfSpeech[fields.part_of_speech]
    
    self.processEntryDefinition_statistics(fields, defi, raw_key)
    
    defi_format = ''
    if fields.part_of_speech_str != None or fields.utf8_title != None:
      if fields.part_of_speech_str != None:
        defi_format += '<font color="#{0}">{1}</font>'.format(
                    self.partOfSpeechColor,
                    xml.sax.saxutils.escape(fields.part_of_speech_str)
                  )
      if fields.utf8_title != None:
        if defi_format != '':
          defi_format += ' '
        defi_format += fields.utf8_title
      defi_format += '<br>\n'
    if fields.utf8_defi != None:
      defi_format += fields.utf8_defi
    # test encoding
    defi_format.decode('utf-8')
    return defi_format
  
  def processEntryDefinition_statistics(self, fields, defi, raw_key):
    if fields.singleEncoding:
      self.findAndPrintCharSamples(fields.defi, 'defi, key = ' + raw_key, fields.encoding)
      if self.metadata2 != None:
        self.metadata2.DefiProcessedCnt += 1
        if isASCII(fields.defi):
          self.metadata2.DefiASCIICnt += 1
        try:
          fields.defi.decode('utf8')
        except UnicodeError:
          pass
        else:
          self.metadata2.DefiUtf8Cnt += 1
    if self.metadata2 != None and self.metadata2.isDefiASCII:
      if not isASCII(fields.u_defi):
        self.metadata2.isDefiASCII = False
    if fields.title != None:
      self.dump_file_write_text('\n' + 'title = ')
      self.dump_file_write_data(fields.title)
    if fields.part_of_speech != None:
      self.decoded_dump_file_write(u'\npart of speech: ' + self.partOfSpeech[fields.part_of_speech].decode('utf8'))
    if fields.u_title != None:
      self.decoded_dump_file_write(u'\ndefi title: ' + fields.u_title)
    if fields.u_defi != None:
      self.decoded_dump_file_write(u'\ndefi: ' + fields.u_defi)
  
  # d0 - index of the '\x14 char in defi
  # d0 may be the last char of the string
  # entry definition structure:
  # <main definition>['\x14'['\x02'<part of speech code, 1 byte>]['\x18'<1 byte><entry title>]]
  def processEntryDefinitionTrailingFields(self, defi, raw_key, d0, fields):
    i = d0 + 1
    while i < len(defi):
      if self.metadata2 != None:
        self.metadata2.defiTrailingFields[ord(defi[i])] += 1
      
      if defi[i] == '\x02': # part of speech # '\x02' <one char - part of speech>
        if fields.part_of_speech != None:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nduplicate part of speech item'.format(defi, raw_key))
        if i+1 >= len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ndefi ends after \\x02'.format(defi, raw_key))
          return
        c = defi[i+1]
        x = ord(c)
        if not (0x30 <= x and x < 0x30 + len(self.partOfSpeech) and self.partOfSpeech[x - 0x30] != None ):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nunknown part of speech. Char code = {2:#X}'.format(defi, raw_key, x))
          return
        if self.partOfSpeech[x - 0x30] != '':
          fields.part_of_speech = x - 0x30
        i = i+2
      elif defi[i] == '\x06': # \x06<one byte>
        if fields.type_6 != None:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nduplicate type 6'.format(defi, raw_key))
        if i+1 >= len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ndefi ends after \\x06'.format(defi, raw_key))
          return
        #self.definitionType6Sample(ord(c), raw_key)
        #fields.type_6 = c
        i += 2
      elif defi[i] == '\x07': # \x07<two bytes>
        if i+3 > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x07'.format(defi, raw_key))
          return
        i += 3
      elif defi[i] == '\x13': # \x13 03 06 0D C7 ??????
        if i + 5 > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x13'.format(defi, raw_key))
          return
        i += 5
      elif defi[i] == '\x18': # \x18<one byte - title length><entry title>
        if fields.title != None:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nduplicate entry title item'.format(defi, raw_key))
        if i+1 >= len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ndefi ends after \\x18'.format(defi, raw_key))
          return
        i += 1
        Len = ord(defi[i])
        i += 1
        if Len == 0:
          #self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            #'key = ({1}):\nblank entry title'.format(defi, raw_key))
          continue
        if i + Len > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntitle is too long'.format(defi, raw_key))
          return
        fields.title = defi[i:i+Len]
        i += Len
      elif defi[i] == '\x1A': # '\x1A'<one byte - length><text>
        if i + 1 >= len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x1A'.format(defi, raw_key))
          return
        Len = ord(defi[i+1])
        i += 2
        if Len == 0:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nblank data after \\x1A'.format(defi, raw_key))
          continue
        if i+Len > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x1A'.format(defi, raw_key))
          return
        i += Len
      elif defi[i] == '\x28': # '\x28' <two bytes - length><html text>
        if i + 2 >= len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x28'.format(defi, raw_key))
          return
        i += 1
        Len = binStrToInt(defi[i:i+2])
        i += 2
        if Len == 0:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nblank data after \\x28'.format(defi, raw_key))
          continue
        if i+Len > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x28'.format(defi, raw_key))
          return
        i += Len
      elif 0x40 <= ord(defi[i]) <= 0x4f: # [\x41-\x4f] <one byte> <text>
      #elif ord(defi[i]) in [ 0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x48, 0x49, 0x4f ]: # tested values
        Len = ord(defi[i]) - 0x3F
        if i+2+Len > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x40+'.format(defi, raw_key))
          return
        #s = 'type 0x41 ({0})\n{1}\n'.format(raw_key, defi[i:i+4])
        #self.msg_log_file_write(s)
        i += 2
        i += Len
      elif defi[i] == '\x50': # \x50 <one byte> <one byte - length><data>
        if i + 2 >= len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x50'.format(defi, raw_key))
          return
        Len = ord(defi[i+2])
        i += 3
        if Len == 0:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nblank data after \\x50'.format(defi, raw_key))
          continue
        if i+Len > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x50'.format(defi, raw_key))
          return
        i += Len
      elif defi[i] == '\x60': # '\x60' <one byte> <two bytes - length> <text>
        if i + 4 > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x60'.format(defi, raw_key))
          return
        i += 2
        Len = binStrToInt(defi[i:i+2])
        i += 2
        if Len == 0:
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\nblank data after \\x60'.format(defi, raw_key))
          continue
        if i+Len > len(defi):
          self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
            'key = ({1}):\ntoo few data after \\x60'.format(defi, raw_key))
          return
        i += Len
      else:
        self.msg_log_file_write('processEntryDefinitionTrailingFields({0})\n'
          'key = ({1}):\nunknown control char. Char code = {2:#X}'.format(defi, raw_key, ord(defi[i])))
        return
    
  def fixImgLinks(self, text):
    """Fix img tag links
    
    src attribute value of image tag is often enclosed in \x1e - \x1f characters.
    For example, <IMG border='0' src='\x1e6B6C56EC.png\x1f' width='9' height='8'>.
    Naturally the control characters are not part of the image source name.
    They may be used to quickly find all names of resources.
    This function strips all such characters.
    Control characters \x1e and \x1f are useless in html text, so we may safely remove
    all of them, irrespective of context.
    """
    return text.replace('\x1e', '').replace('\x1f', '')
    
  def __del__(self):
    #if self.verbose>2:
      #print 'wordLenMax = %s'%self.wordLenMax
      #print 'defiLenMax = %s'%self.defiLenMax
    if self.file != None:
      self.file.close()
    if self.writeGz:
      os.remove(self.dataFile)

  # write text to dump file as is
  def dump_file_write_text(self, text):
    if self.dump_file != None:
      self.dump_file.write(text)
  
  # write data to dump file unambiguously representing control chars
  # escape '\' with '\\'
  # print control chars as '\xhh'
  def dump_file_write_data(self, text):
    # the next function escapes too many chars, for example, it escapes äöü
    # self.dump_file.write(text.encode('string_escape'))
    if self.dump_file != None:
      self.dump_file.write(text)
  
  # write text into the decoded_dump_file
  # text - must be a unicode string
  def decoded_dump_file_write(self, text):
    if not isinstance(text, unicode):
      printAsError('decoded_dump_file_write({0}): text is not a unicode string'.format(text))
      return
    if self.decoded_dump_file != None:
      self.decoded_dump_file.write(text.encode('utf8'))
  
  def msg_log_file_write(self, text):
    if self.msg_log_file != None:
      offset = self.msg_log_file.tell()
      # print offset in the log file to facilitate navigating this log in hex editor
      # intended usage:
      # the log file is opened in a text editor and hex editor
      # use text editor to read error messages, use hex editor to inspect char codes
      # offsets allows to quickly jump to the right place of the file hex editor
      self.msg_log_file.write('\noffset = {0:#X}\n'.format(offset))
      self.msg_log_file.write(text+'\n')
    else:
      sys.stdout.write(text +'\n')
      
  def samples_file_write(self, text):
    if self.samples_dump_file != None:
      offset = self.samples_dump_file.tell()
      self.samples_dump_file.write('\noffset = {0:#X}\n'.format(offset))
      self.samples_dump_file.write(text+'\n')
    else:
      sys.stdout.write(text +'\n')

  # search for new chars in data
  # if new chars are found, mark them with a special sequence in the text
  # and print result into msg log
  def findAndPrintCharSamples(self, data, hint, encoding):
    if self.target_chars_arr == None:
      return
    offsets = self.findCharSamples(data)
    if len(offsets) == 0:
      return
    res = ''
    utf8 = (encoding.lower() == 'utf8')
    i = 0
    for o in offsets:
      j = o
      if utf8:
        while (ord(data[j]) & 0xC0) == 0x80:
          j -= 1
      res += data[i:j]
      res += '!!!--+!!!'
      i = j
    res += data[j:]
    offsets_str = ' '.join(['{0}'.format(el) for el in offsets])
    self.samples_file_write('charSample({0})\noffsets = {1}\nmarked = {2}\norig = {3}\n'\
    .format(hint, offsets_str, res, data))
  
  def findCharSamples(self, data):
    """Find samples of chars in data.
    
    Search for chars in data that have not been marked so far in 
    the target_chars_arr array, mark new chars.
    Returns a list of offsets in data string.
    May return an empty list.
    """
    res = []
    if not isinstance(data, str):
      printAsError('findCharSamples: data is not a string')
      return res
    if self.target_chars_arr == None:
      printAsError('findCharSamples: self.target_chars_arr == None')
      return res
    for i in range(len(data)):
      x = ord(data[i])
      if x < 128:
        continue
      if not self.target_chars_arr[x]:
        self.target_chars_arr[x] = True
        res.append(i)
    return res
  
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


def read(glos, filename, appendAlternatives=True, options={}):
  glos.data = []
  db = BGL(filename, **options)
  if not db.open():
    raise 'can not open BGL file "{0}"'.format(filename)
  if not db.read():
    raise 'can not read BGL file "{0}"'.format(filename)
  n = db.numEntries
  ui = glos.ui
  if not isinstance(n, int):
    ui = None
  entry = BGL.Entry()
  if ui != None:
    ui.progressStart()
  k = 2000
  for i in xrange(n):
    if not db.readEntry(entry):
      printAsError('No enough entries found!')
      break
    if appendAlternatives:
      for alt in entry.alts:####??????????????? What do with alternates?
        entry.word += ' | '+alt #@3
    glos.data.append((entry.word, entry.defi))
    if ui != None and i%k==0:
      rat = float(i)/n
      ui.progress(rat)
  if ui != None:
    ui.progressEnd()
  db.close()
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

