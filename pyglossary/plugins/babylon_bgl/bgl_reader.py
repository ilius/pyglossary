# -*- coding: utf-8 -*-
#
# Copyright © 2008-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright © 2011-2012 kubtek <kubtek@gmail.com>
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
# Thanks to Raul Fernandes <rgfbr@yahoo.com.br> and Karl Grill
#       for reverse engineering
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

import io
import gzip
import re
from collections import OrderedDict as odict

from pyglossary.plugins.formats_common import *  # FIXME
try:
    GzipFile = __import__(
        'pyglossary.plugin_lib.py%d%d.gzip_no_crc' % sys.version_info[:2],
        fromlist='GzipFile',
    ).GzipFile
except ImportError:
    from gzip import GzipFile
    log.exception('')
    log.warning(
        'If things didn\'t work well with BGL files, '
        'install Python 3.5 and try again'
    )

from pyglossary.text_utils import (
    binStrToInt,
    excMessage,
    isASCII,
)

from pyglossary.xml_utils import xml_escape

from .bgl_info import (
    infoKeysByCode,
    infoKeyDecodeMethods,
    charsetInfoDecode,
)
from .bgl_pos import partOfSpeechByCode
from .bgl_text import (
    replaceHtmlEntries,
    replaceHtmlEntriesInKeys,
    stripHtmlTags,
    removeControlChars,
    removeNewlines,
    normalizeNewlines,
    replaceAsciiCharRefs,
    fixImgLinks,
    stripDollarIndexes,
    unkownHtmlEntries,
)

file = io.BufferedReader

debugReadOptions = {
    'searchCharSamples',  # bool
    'collectMetadata2',  # bool
    'writeGz',  # bool
    'charSamplesPath',  # str, file path
    'msgLogPath',  # str, file path
    'rawDumpPath',  # str, file path
    'unpackedGzipPath',  # str, file path
}
readOptions = [
    'defaultEncodingOverwrite',  # str, encoding
    'sourceEncodingOverwrite',  # str, encoding
    'targetEncodingOverwrite',  # str, encoding
    'partOfSpeechColor',  # str, for example 'ff0000' for green

    'noControlSequenceInDefi',  # bool
    'strictStringConvertion',  # bool
    'processHtmlInKey',  # bool
    'keyRStripChars',  # str, list of characters to strip (from right side)
] + sorted(debugReadOptions)


if os.sep == '/':  # Operating system is Unix-like
    tmpDir = '/tmp'
elif os.sep == '\\':  # Operating system is ms-windows
    tmpDir = os.getenv('TEMP')
else:
    raise RuntimeError(
        'Unknown path separator(os.sep=="%s")' % os.sep +
        'What is your operating system?'
    )

charsetDecodePattern = re.compile(
    b'(<charset\\s+c\\=[\'\"]?(\\w)[\'\"]?>|</charset>)',
    re.I,
)


class BGLGzipFile(GzipFile):
    """
    gzip_no_crc.py contains GzipFile class without CRC check.

    It prints a warning when CRC code does not match.
    The original method raises an exception in this case.
    Some dictionaries do not use CRC code, it is set to 0.
    """
    def __init__(
        self,
        fileobj=None,
        closeFileobj=False,
        **kwargs
    ):
        GzipFile.__init__(self, fileobj=fileobj, **kwargs)
        self.closeFileobj = closeFileobj

    def close(self):
        if self.closeFileobj:
            self.fileobj.close()


class Block(object):
    def __init__(self):
        self.data = b''
        self.type = ''
        # block offset in the gzip stream, for debugging
        self.offset = -1

    def __str__(self):
        return 'Block type=%s, length=%s, len(data)=%s' % (
            self.type,
            self.length,
            len(self.data),
        )


class FileOffS(file):
    """
    A file class with an offset.

    This class provides an interface to a part of a file starting at specified
    offset and ending at the end of the file, making it appear an independent
    file. offset parameter of the constructor specifies the offset of the first
    byte of the modeled file.
    """
    def __init__(self, filename, offset=0):
        fp = open(filename, 'rb')
        file.__init__(self, fp)
        self._fp = fp
        self.offset = offset
        self.filesize = os.path.getsize(filename)
        file.seek(self, offset)  # OR self.seek(0)

    def close(self):
        self._fp.close()

    def seek(self, pos, whence=0):  # position, whence
        if whence == 0:  # relative to start of file
            file.seek(
                self,
                max(0, pos) + self.offset,
                0,
            )
        elif whence == 1:  # relative to current position
            file.seek(
                self,
                max(
                    self.offset,
                    self.tell() + pos,
                ),
                0
            )
        elif whence == 2:  # relative to end of file
            file.seek(self, pos, 2)
        else:
            raise ValueError('FileOffS.seek: bad whence=%s' % whence)

    def tell(self):
        return file.tell(self) - self.offset


class DefinitionFields(object):
    """
        Fields of entry definition

        Entry definition consists of a number of fields.
        The most important of them are:
        defi - the main definition, mandatory, comes first.
        part of speech
        title
    """
    # nameByCode = {
    # }
    def __init__(self):
        # self.bytesByCode = {}
        # self.strByCode = {}

        self.encoding = None  # encoding of the definition
        self.singleEncoding = True
        # singleEncoding=True if the definition was encoded with
        # a single encoding

        self.b_defi = None  # bytes, main definition part of defi
        self.u_defi = None  # str, main part of definition

        self.partOfSpeech = None
        # string representation of the part of speech, utf-8

        self.b_title = None  # bytes
        self.u_title = None  # str

        self.b_title_trans = None  # bytes
        self.u_title_trans = None  # str

        self.b_transcription_50 = None  # bytes
        self.u_transcription_50 = None  # str
        self.code_transcription_50 = None

        self.b_transcription_60 = None  # bytes
        self.u_transcription_60 = None  # str
        self.code_transcription_60 = None

        self.b_field_1a = None  # bytes
        self.u_field_1a = None  # str

        self.b_field_07 = None  # bytes
        self.b_field_06 = None  # bytes
        self.b_field_13 = None  # bytes


class BglReader(object):

    ##########################################################################
    """
    Dictionary properties
    ---------------------

    Dictionary (or glossary) properties are textual data like glossary name,
    glossary author name, glossary author e-mail, copyright message and
    glossary description. Most of the dictionaries have these properties set.
    Since they contain textual data we need to know the encoding.
    There may be other properties not listed here. I've enumerated only those
    that are available in Babylon Glossary builder.

    Playing with Babylon builder allows us detect how encoding is selected.
    If global utf-8 flag is set, utf-8 encoding is used for all properties.
    Otherwise the target encoding is used, that is the encoding corresponding
    to the target language. The chars that cannot be represented in the target
    encoding are replaced with question marks.

    Using this algorithm to decode dictionary properties you may encounter that
    some of them are decoded incorrectly. For example, it is clear that the
    property is in cp1251 encoding while the algorithm says we must use cp1252,
    and we get garbage after decoding. That is OK, the algorithm is correct.
    You may install that dictionary in Babylon and check dictionary properties.
    It shows the same garbage. Unfortunately, we cannot detect correct encoding
    in this case automatically. We may add a parameter the will overwrite the
    selected encoding, so the user may fix the encoding if needed.
    """

    def __init__(self, glos):  # no more arguments
        self._glos = glos
        self._filename = ''
        self.info = odict()
        self.numEntries = None
        ####
        self.sourceLang = ''
        self.targetLang = ''
        ##
        self.defaultCharset = ''
        self.sourceCharset = ''
        self.targetCharset = ''
        ##
        self.sourceEncoding = None
        self.targetEncoding = None
        ####
        self.bgl_numEntries = None
        self.wordLenMax = 0
        self.defiMaxBytes = 0
        ##
        self.metadata2 = None
        self.rawDumpFile = None
        self.msgLogFile = None
        self.samplesDumpFile = None
        ##
        self.stripSlashAltKeyPattern = re.compile(r'(^|\s)/(\w)', re.U)
        self.specialCharPattern = re.compile(r'[^\s\w.]', re.U)
        ###
        self.file = None
        # offset of gzip header, set in self.open()
        self.gzipOffset = None
        # must be a in RRGGBB format
        self.partOfSpeechColor = '007000'
        self.iconData = None

    def __len__(self):
        if self.numEntries is None:
            log.warning('len(reader) called while numEntries=None')
            return 0
        return self.numEntries + self.numResources

    # open .bgl file, read signature, find and open gzipped content
    # self.file - ungzipped content
    def open(
        self,
        filename,
        defaultEncodingOverwrite=None,
        sourceEncodingOverwrite=None,
        targetEncodingOverwrite=None,
        partOfSpeechColor=None,
        noControlSequenceInDefi=False,
        strictStringConvertion=False,
        # process keys and alternates as HTML
        # Babylon does not interpret keys and alternates as HTML text,
        # however you may encounter many keys containing character references
        # and html tags. That is clearly a bug of the dictionary.
        # We must be very careful processing HTML tags in keys, not damage
        # normal keys. This option should be disabled by default, enabled
        # explicitly by user. Namely this option does the following:
        # - resolve character references
        # - strip HTML tags
        processHtmlInKey=False,
        # a string of characters that will be stripped from the end of the
        # key (and alternate), see str.rstrip function
        keyRStripChars=None,
        **kwargs
    ):
        if kwargs:
            for key in kwargs:
                if key in debugReadOptions:
                    log.error(
                        'BGL Reader: option "%s" is only usable' % key +
                        'in debug mode, add -v4 to enable debug mode'
                    )
                else:
                    log.error('BGL Reader: invalid option "%s"' % key)
            return False

        self._filename = filename
        self.defaultEncodingOverwrite = defaultEncodingOverwrite
        self.sourceEncodingOverwrite = sourceEncodingOverwrite
        self.targetEncodingOverwrite = targetEncodingOverwrite

        if partOfSpeechColor:
            self.partOfSpeechColor = partOfSpeechColor

        self.noControlSequenceInDefi = noControlSequenceInDefi
        self.strictStringConvertion = strictStringConvertion
        self.processHtmlInKey = processHtmlInKey
        self.keyRStripChars = keyRStripChars

        if not self.openGzip():
            return False

        self.readInfo()
        self.setGlossaryInfo()

        return True

    def openGzip(self):
        with open(self._filename, 'rb') as bglFile:
            if not bglFile:
                log.error('file pointer empty: %s' % bglFile)
                return False
            b_head = bglFile.read(6)

        if len(b_head) < 6 or not b_head[:4] in (
            b'\x12\x34\x00\x01',
            b'\x12\x34\x00\x02',
        ):
            log.error('invalid header: %r' % b_head[:6])
            return False

        self.gzipOffset = gzipOffset = binStrToInt(b_head[4:6])
        log.debug('Position of gz header: %s' % gzipOffset)

        if gzipOffset < 6:
            log.error('invalid gzip header position: %s' % gzipOffset)
            return False

        self.file = BGLGzipFile(
            fileobj=FileOffS(self._filename, gzipOffset),
            closeFileobj=True,
        )

        return True

    def readInfo(self):
        """
        read meta information about the dictionary: author, description,
        source and target languages, etc (articles are not read)
        """
        self.numEntries = 0
        self.numBlocks = 0
        self.numResources = 0
        block = Block()
        while not self.isEndOfDictData():
            if not self.readBlock(block):
                break
            self.numBlocks += 1
            if not block.data:
                continue
            if block.type == 0:
                self.readType0(block)
            elif block.type in (1, 7, 10, 11, 13):
                self.numEntries += 1
            elif block.type == 2:
                self.numResources += 1
            elif block.type == 3:
                self.readType3(block)
            else:  # Unknown block.type
                log.debug(
                    'Unkown Block type "%s"' % block.type +
                    ', data_length = %s' % len(block.data) +
                    ', number = %s' % self.numBlocks
                )
        self.file.seek(0)

        self.detectEncoding()

        log.debug('numEntries = %s' % self.numEntries)
        if self.bgl_numEntries and self.bgl_numEntries != self.numEntries:
            # There are a number of cases when these numbers do not match.
            # The dictionary is OK, and these is no doubt that we might missed
            # an entry.
            # self.bgl_numEntries may be less than the number of entries
            # we've read.
            log.warning(
                'bgl_numEntries=%s' % self.bgl_numEntries +
                ', numEntries=%s' % self.numEntries
            )

        self.numBlocks = 0

    def setGlossaryInfo(self):
        glos = self._glos
        ###
        if self.sourceLang:
            glos.setInfo('sourceLang', self.sourceLang.name)
        if self.targetLang:
            glos.setInfo('targetLang', self.targetLang.name)
        ###
        for attr in (
            'defaultCharset',
            'sourceCharset',
            'targetCharset',
            'defaultEncoding',
            'sourceEncoding',
            'targetEncoding',
        ):
            value = getattr(self, attr, None)
            if value:
                glos.setInfo('bgl_' + attr, value)
        ###
        glos.setInfo('sourceCharset', 'UTF-8')
        glos.setInfo('targetCharset', 'UTF-8')
        ###
        for key, value in self.info.items():
            if key in {
                'creationTime',
                'middleUpdated',
                'lastUpdated',
            }:
                key = 'bgl_' + key
            try:
                glos.setInfo(key, value)
            except:
                log.exception('key = %s' % key)

    def isEndOfDictData(self):
        """
            Test for end of dictionary data.

            A bgl file stores dictionary data as a gzip compressed block.
            In other words, a bgl file stores a gzip data file inside.
            A gzip file consists of a series of "members".
            gzip data block in bgl consists of one member (I guess).
            Testing for block type returned by self.readBlock is not a
            reliable way to detect the end of gzip member.
            For example, consider 'Airport Code Dictionary.BGL' dictionary.
            To reliably test for end of gzip member block we must use a number
            of undocumented variables of gzip.GzipFile class.
            self.file._new_member - true if the current member has been
            completely read from the input file
            self.file.extrasize - size of buffered data
            self.file.offset - offset in the input file

            after reading one gzip member current position in the input file
            is set to the first byte after gzip data
            We may get this offset: self.file_bgl.tell()
            The last 4 bytes of gzip block contains the size of the original
            (uncompressed) input data modulo 2^32
        """
        return False

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    def __del__(self):
        self.close()
        while unkownHtmlEntries:
            log.debug(
                'BGL: unknown html entity: %s' % unkownHtmlEntries.pop()
            )

    # returns False if error
    def readBlock(self, block):
        block.offset = self.file.tell()
        length = self.readBytes(1)
        if length == -1:
            log.debug('readBlock: length = -1')
            return False
        block.type = length & 0xf
        length >>= 4
        if length < 4:
            length = self.readBytes(length+1)
            if length == -1:
                log.error('readBlock: length = -1')
                return False
        else:
            length -= 4
        self.file.flush()
        if length > 0:
            try:
                block.data = self.file.read(length)
            except:
                # struct.error: unpack requires a string argument of length 4
                # FIXME
                log.exception(
                    'failed to read block data' +
                    ': numBlocks=%s' % self.numBlocks +
                    ', length=%s' % length +
                    ', filePos=%s' % self.file.tell()
                )
                block.data = b''
                return False
        else:
            block.data = b''
        return True

    def readBytes(self, num):
        """
            return -1 if error
        """
        if num < 1 or num > 4:
            log.error('invalid argument num=%s' % num)
            return -1
        self.file.flush()
        buf = self.file.read(num)
        if len(buf) == 0:
            log.debug('readBytes: end of file: len(buf)==0')
            return -1
        if len(buf) != num:
            log.error(
                'readBytes: expected to read %s bytes' % num +
                ', but found %s bytes' % len(buf)
            )
            return -1
        return binStrToInt(buf)

    def readType0(self, block):
        code = block.data[0]
        if code == 2:
            # this number is vary close to self.bgl_numEntries,
            # but does not always equal to the number of entries
            # see self.readType3, code == 12 as well
            num = binStrToInt(block.data[1:])
        elif code == 8:
            self.defaultCharset = charsetInfoDecode(block.data[1:])
            if not self.defaultCharset:
                log.warning('defaultCharset is not valid')
        else:
            self.logUnknownBlock(block)
            return False
        return True

    def readType2(self, block):
        """
        Process type 2 block

        Type 2 block is an embedded file (mostly Image or HTML).
        pass_num - pass number, may be 1 or 2
        On the first pass self.sourceEncoding is not defined and we cannot
        decode file names.
        That is why the second pass is needed. The second pass is costly, it
        apparently increases total processing time. We should avoid the second
        pass if possible.
        Most of the dictionaries do not have valuable resources, and those
        that do, use file names consisting only of ASCII characters. We may
        process these resources on the second pass. If all files have been
        processed on the first pass, the second pass is not needed.

        All dictionaries I've processed so far use only ASCII chars in
        file names.
        Babylon glossary builder replaces names of files, like links to images,
        with what looks like a hash code of the file name,
        for example "8FFC5C68.png".

        returns: DataEntry instance if the resource was successfully processed
                 or None
        """
        # Embedded File (mostly Image or HTML)
        name = ''  # Embedded file name
        pos = 0
        # name:
        Len = block.data[pos]
        pos += 1
        if pos+Len > len(block.data):
            log.warning('reading block type 2: name too long')
            return
        b_name = block.data[pos:pos+Len]
        pos += Len
        b_data = block.data[pos:]
        # if b_name in (b'C2EEF3F6.html', b'8EAF66FD.bmp'):
        #    log.debug('Skipping non-useful file "%s"' % b_name)
        #    return
        u_name = b_name.decode(self.sourceEncoding)
        return self._glos.newDataEntry(
            u_name,
            b_data,
        )

    def readType3(self, block):
        """
            reads block with type 3, and updates self.info
            returns None
        """
        code, b_value = binStrToInt(block.data[:2]), block.data[2:]
        if not b_value:
            return
        # if not b_value.strip(b'\x00'): return  # FIXME

        try:
            key = infoKeysByCode[code]
        except KeyError:
            if b_value.strip(b'\x00'):
                log.debug(
                    'Unknown info type code=%#.2x' % code +
                    ', b_value=%r' % b_value,
                )
            return

        try:
            func = infoKeyDecodeMethods[key]
        except KeyError:
            value = b_value
        else:
            value = func(b_value)

        # `value` can be a bytes instance,
        # or str instance, depending on `key` FIXME

        if value:
            if isinstance(value, dict):
                self.info.update(value)
            elif key in {
                'sourceLang',
                'targetLang',
                'defaultCharset',
                'sourceCharset',
                'targetCharset',
                'sourceEncoding',
                'targetEncoding',
                'bgl_numEntries',
                'iconData',
            }:
                setattr(self, key, value)
            else:
                self.info[key] = value

    def detectEncoding(self):
        """
            assign self.sourceEncoding and self.targetEncoding
        """
        utf8Encoding = self.info.get('utf8Encoding', False)

        if self.sourceEncodingOverwrite:
            self.sourceEncoding = self.sourceEncodingOverwrite
        elif utf8Encoding:
            self.sourceEncoding = 'utf8'
        elif self.sourceCharset:
            self.sourceEncoding = self.sourceCharset
        elif self.sourceLang:
            self.sourceEncoding = self.sourceLang.encoding
        else:
            self.sourceEncoding = 'cp1252'

        if self.targetEncodingOverwrite:
            self.targetEncoding = self.targetEncodingOverwrite
        elif utf8Encoding:
            self.targetEncoding = 'utf8'
        elif self.targetCharset:
            self.targetEncoding = self.targetCharset
        elif self.targetLang:
            self.targetEncoding = self.targetLang.encoding
        else:
            self.targetEncoding = 'cp1252'

        # not used
        if self.defaultEncodingOverwrite:
            self.defaultEncoding = self.defaultEncodingOverwrite
        elif self.defaultCharset:
            self.defaultEncoding = self.defaultCharset
        else:
            self.defaultEncoding = 'cp1252'

    def logUnknownBlock(self, block):
        log.debug(
            'Unknown block: type=%s' % block.type +
            ', number=%s' % self.numBlocks +
            ', data=%r' % block.data
        )

    def __iter__(self):
        return self

    def __next__(self):
        if not self.file:
            raise StopIteration
        block = Block()
        while not self.isEndOfDictData():
            if not self.readBlock(block):
                break
            if not block.data:
                continue
            if block.type in (1, 7, 10, 11, 13):
                pos = 0
                # word:
                succeed, pos, u_word, b_word = self.readEntryWord(block, pos)
                if not succeed:
                    continue
                # defi:
                succeed, pos, u_defi, b_defi = \
                    self.readEntryDefi(block, pos, b_word)
                if not succeed:
                    continue
                # now pos points to the first char after definition
                succeed, pos, u_alts = \
                    self.readEntryAlts(block, pos, b_word, u_word)
                if not succeed:
                    continue

                return self._glos.newEntry(
                    [u_word] + u_alts,
                    u_defi,
                )

            elif block.type == 2:
                return self.readType2(block)

        raise StopIteration

    def readEntryWord(self, block, pos):
        """
            Read word part of entry.

            Return value is a list.
            (False, None, None, None) if error
            (True, pos, u_word, b_word) if OK
                u_word is a str instance (utf-8)
                b_word is a bytes instance
        """
        Err = (False, None, None, None)
        if block.type == 11:
            if pos + 5 > len(block.data):
                log.error(
                    'reading block offset=%#.2x' % block.offset +
                    ', reading word size: pos + 5 > len(block.data)'
                )
                return Err
            Len = binStrToInt(block.data[pos:pos+5])
            pos += 5
        else:
            if pos + 1 > len(block.data):
                log.error(
                    'reading block offset=%#.2x' % block.offset +
                    ', reading word size: pos + 1 > len(block.data)'
                )
                return Err
            Len = block.data[pos]
            pos += 1
        if pos + Len > len(block.data):
            log.error(
                'reading block offset=%#.2x' % block.offset +
                ', reading word: pos + Len > len(block.data)'
            )
            return Err
        b_word = block.data[pos:pos+Len]
        u_word = self.processKey(b_word)
        """
        Entry keys may contain html text, for example:
        ante<font face'Lucida Sans Unicode'>&lt; meridiem
        arm und reich c=t&gt;2003;</charset>
        </font>und<font face='Lucida Sans Unicode'>
        etc.

        Babylon does not process keys as html, it display them as is.
        Html in keys is the problem of that particular dictionary.
        We should not process keys as html, since Babylon do not process
        them as such.
        """
        pos += Len
        self.wordLenMax = max(self.wordLenMax, len(u_word))
        return True, pos, u_word, b_word

    def readEntryDefi(self, block, pos, b_key):
        """
        Read defi part of entry.

        Return value is a list.
        (False, None, None, None) if error
        (True, pos, u_defi, b_defi) if OK
            u_defi is a str instance (utf-8)
            b_defi is a bytes instance
        """
        Err = (False, None, None, None)
        if block.type == 11:
            if pos + 8 > len(block.data):
                log.error(
                    'reading block offset=%#.2x' % block.offset +
                    ', reading defi size: pos + 8 > len(block.data)'
                )
                return Err
            pos += 4  # binStrToInt(block.data[pos:pos+4]) - may be 0, 1
            Len = binStrToInt(block.data[pos:pos+4])
            pos += 4
        else:
            if pos + 2 > len(block.data):
                log.error(
                    'reading block offset=%#.2x' % block.offset +
                    ', reading defi size: pos + 2 > len(block.data)'
                )
                return Err
            Len = binStrToInt(block.data[pos:pos+2])
            pos += 2
        if pos + Len > len(block.data):
            log.error(
                'reading block offset=%#.2x' % block.offset +
                ', reading defi: pos + Len > len(block.data)'
            )
            return Err
        b_defi = block.data[pos:pos+Len]
        u_defi = self.processDefi(b_defi, b_key)
        self.defiMaxBytes = max(self.defiMaxBytes, len(b_defi))

        pos += Len
        return True, pos, u_defi, b_defi

    def readEntryAlts(self, block, pos, b_key, u_key):
        """
        returns:
            (False, None, None) if error
            (True, pos, u_alts) if succeed
                u_alts is a sorted list, items are str (utf-8)
        """
        Err = (False, None, None)
        # use set instead of list to prevent duplicates
        u_alts = set()
        while pos < len(block.data):
            if block.type == 11:
                if pos + 4 > len(block.data):
                    log.error(
                        'reading block offset=%#.2x' % block.offset +
                        ', reading alt size: pos + 4 > len(block.data)'
                    )
                    return Err
                Len = binStrToInt(block.data[pos:pos+4])
                pos += 4
                if Len == 0:
                    if pos + Len != len(block.data):
                        # no evidence
                        log.warning(
                            'reading block offset=%#.2x' % block.offset +
                            ', reading alt size: pos + Len != len(block.data)'
                        )
                    break
            else:
                if pos + 1 > len(block.data):
                    log.error(
                        'reading block offset=%#.2x' % block.offset +
                        ', reading alt size: pos + 1 > len(block.data)'
                    )
                    return Err
                Len = block.data[pos]
                pos += 1
            if pos + Len > len(block.data):
                log.error(
                    'reading block offset=%#.2x' % block.offset +
                    ', reading alt: pos + Len > len(block.data)'
                )
                return Err
            b_alt = block.data[pos:pos+Len]
            u_alt = self.processAlternativeKey(b_alt, b_key)
            # Like entry key, alt is not processed as html by babylon,
            # so do we.
            u_alts.add(u_alt)
            pos += Len
        if u_key in u_alts:
            u_alts.remove(u_key)
        return True, pos, list(sorted(u_alts))

    def charReferencesStat(self, b_text, encoding):
        pass

    def decodeCharsetTags(self, b_text, defaultEncoding):
        """
        b_text is a bytes
        Decode html text taking into account charset tags and default encoding

        Return value: (u_text, defaultEncodingOnly)
        u_text is str
        defaultEncodingOnly parameter is false if the text contains parts
        encoded with non-default encoding (babylon character references
        '<CHARSET c="T">00E6;</CHARSET>' do not count).
        """
        b_parts = re.split(charsetDecodePattern, b_text)
        u_text = ''
        encodings = []  # stack of encodings
        defaultEncodingOnly = True
        for i, b_part in enumerate(b_parts):
            if i % 3 == 0:  # text block
                encoding = encodings[-1] if encodings else defaultEncoding
                b_text2 = b_part
                if encoding == 'babylon-reference':
                    b_refs = b_text2.split(b';')
                    for i_ref, b_ref in enumerate(b_refs):
                        if not b_ref:
                            if i_ref != len(b_refs)-1:
                                log.debug(
                                    'decoding charset tags' +
                                    ', b_text=%r\n' % b_text +
                                    'blank <charset c=t> character' +
                                    ' reference (%r)\n' % b_text2
                                )
                            continue
                        if not re.match(b'^[0-9a-fA-F]{4}$', b_ref):
                            log.debug(
                                'decoding charset tags, b_text=%r\n' % b_text +
                                'invalid <charset c=t> character' +
                                ' reference (%r)\n' % b_text2
                            )
                            continue
                        u_text += chr(int(b_ref, 16))
                else:
                    self.charReferencesStat(b_text2, encoding)
                    if encoding == 'cp1252':
                        b_text2 = replaceAsciiCharRefs(b_text2, encoding)
                    if self.strictStringConvertion:
                        try:
                            u_text2 = b_text2.decode(encoding)
                        except UnicodeError:
                            log.debug(
                                'decoding charset tags' +
                                ', b_text=%r' % b_text +
                                '\nfragment: %r' % b_text2 +
                                '\nconversion error:\n%s' % excMessage()
                            )
                            u_text2 = text2.decode(encoding, 'replace')
                    else:
                        u_text2 = b_text2.decode(encoding, 'replace')
                    u_text += u_text2
                    if encoding != defaultEncoding:
                        defaultEncodingOnly = False
            elif i % 3 == 1:  # <charset...> or </charset>
                if b_part.startswith(b'</'):
                    # </charset>
                    if encodings:
                        encodings.pop()
                    else:
                        log.debug(
                            'decoding charset tags, b_text=%r\n' % b_text +
                            'unbalanced </charset> tag\n'
                        )
                else:
                    # <charset c="?">
                    b_type = b_parts[i+1].lower()
                    # b_type is a bytes instance, with length 1
                    if b_type == b't':
                        encodings.append('babylon-reference')
                    elif b_type == b'u':
                        encodings.append('utf-8')
                    elif b_type == b'k':
                        encodings.append(self.sourceEncoding)
                    elif b_type == b'e':
                        encodings.append(self.sourceEncoding)
                    elif b_type == b'g':
                        # gbk or gb18030 encoding
                        # (not enough data to make distinction)
                        encodings.append('gbk')
                    else:
                        log.debug(
                            'decoding charset tags, text = %r\n' % b_text +
                            'unknown charset code = %#.2x\n' % ord(b_type)
                        )
                        # add any encoding to prevent
                        # 'unbalanced </charset> tag' error
                        encodings.append(defaultEncoding)
            else:
                # c attribute of charset tag if the previous tag was charset
                pass
        if encodings:
            log.debug(
                'decoding charset tags, text=%s\n' % b_text +
                'unclosed <charset...> tag\n'
            )
        return u_text, defaultEncodingOnly

    def processKey(self, b_word):
        """
            b_word is a bytes instance
            returns u_word_main, as str instance (utf-8 encoding)
        """
        b_word_main, strip_count = stripDollarIndexes(b_word)
        if strip_count > 1:
            log.debug(
                'processKey(%s):\n' % b_word +
                'number of dollar indexes = %s' % strip_count,
            )
        # convert to unicode
        if self.strictStringConvertion:
            try:
                u_word_main = b_word_main.decode(self.sourceEncoding)
            except UnicodeError:
                log.debug(
                    'processKey(%s):\n' % b_word +
                    'conversion error:\n%s' % excMessage()
                )
                u_word_main = b_word_main.decode(
                    self.sourceEncoding,
                    'ignore',
                )
        else:
            u_word_main = b_word_main.decode(self.sourceEncoding, 'ignore')

        if self.processHtmlInKey:
            # u_word_main_orig = u_word_main
            u_word_main = stripHtmlTags(u_word_main)
            u_word_main = replaceHtmlEntriesInKeys(u_word_main)
#            if(re.match('.*[&<>].*', u_word_main_orig)):
#                log.debug('original text: ' + u_word_main_orig + '\n' \
#                          + 'new      text: ' + u_word_main + '\n')
        u_word_main = removeControlChars(u_word_main)
        u_word_main = removeNewlines(u_word_main)
        u_word_main = u_word_main.lstrip()
        u_word_main = u_word_main.rstrip(self.keyRStripChars)
        return u_word_main

    def processAlternativeKey(self, b_word, b_key):
        """
            b_word is a bytes instance
            returns u_word_main, as str instance (utf-8 encoding)
        """
        b_word_main, strip_count = stripDollarIndexes(b_word)
        # convert to unicode
        if self.strictStringConvertion:
            try:
                u_word_main = b_word_main.decode(self.sourceEncoding)
            except UnicodeError:
                log.debug(
                    'processAlternativeKey(%s)\n' % b_word +
                    'key = %s:\n' % b_key +
                    'conversion error:\n%s' % excMessage()
                )
                u_word_main = b_word_main.decode(self.sourceEncoding, 'ignore')
        else:
            u_word_main = b_word_main.decode(self.sourceEncoding, 'ignore')

        # strip '/' before words
        u_word_main = re.sub(
            self.stripSlashAltKeyPattern,
            r'\1\2',
            u_word_main,
        )

        if self.processHtmlInKey:
            # u_word_main_orig = u_word_main
            u_word_main = stripHtmlTags(u_word_main)
            u_word_main = replaceHtmlEntriesInKeys(u_word_main)
#            if(re.match('.*[&<>].*', u_word_main_orig)):
#                log.debug('original text: ' + u_word_main_orig + '\n' \
#                        + 'new      text: ' + u_word_main + '\n')
        u_word_main = removeControlChars(u_word_main)
        u_word_main = removeNewlines(u_word_main)
        u_word_main = u_word_main.lstrip()
        u_word_main = u_word_main.rstrip(self.keyRStripChars)
        return u_word_main

    def processDefi(self, b_defi, b_key):
        """
        b_defi: bytes
        b_key: bytes

        return: u_defi_format
        """

        fields = DefinitionFields()
        self.collectDefiFields(b_defi, b_key, fields)

        fields.u_defi, fields.singleEncoding = self.decodeCharsetTags(
            fields.b_defi,
            self.targetEncoding,
        )
        if fields.singleEncoding:
            fields.encoding = self.targetEncoding
        fields.u_defi = fixImgLinks(fields.u_defi)
        fields.u_defi = replaceHtmlEntries(fields.u_defi)
        fields.u_defi = removeControlChars(fields.u_defi)
        fields.u_defi = normalizeNewlines(fields.u_defi)
        fields.u_defi = fields.u_defi.strip()

        if fields.b_title:
            fields.u_title, singleEncoding = self.decodeCharsetTags(
                fields.b_title,
                self.sourceEncoding,
            )
            fields.u_title = replaceHtmlEntries(fields.u_title)
            fields.u_title = removeControlChars(fields.u_title)

        if fields.b_title_trans:
            # sourceEncoding or targetEncoding ?
            fields.u_title_trans, singleEncoding = self.decodeCharsetTags(
                fields.b_title_trans,
                self.sourceEncoding,
            )
            fields.u_title_trans = replaceHtmlEntries(fields.u_title_trans)
            fields.u_title_trans = removeControlChars(fields.u_title_trans)

        if fields.b_transcription_50:
            if fields.code_transcription_50 == 0x10:
                # contains values like this (char codes):
                # 00 18 00 19 00 1A 00 1B 00 1C 00 1D 00 1E 00 40 00 07
                # this is not utf-16
                # what is this?
                pass
            elif fields.code_transcription_50 == 0x1b:
                fields.u_transcription_50, singleEncoding = \
                    self.decodeCharsetTags(
                        fields.b_transcription_50,
                        self.sourceEncoding,
                    )
                fields.u_transcription_50 = \
                    replaceHtmlEntries(fields.u_transcription_50)
                fields.u_transcription_50 = \
                    removeControlChars(fields.u_transcription_50)
            elif fields.code_transcription_50 == 0x18:
                # incomplete text like:
                # t c=T>02D0;</charset>g<charset c=T>0259;</charset>-
                # This defi normally contains fields.b_transcription_60
                # in this case.
                pass
            else:
                log.debug(
                    'processDefi(%s)\n' % b_defi +
                    'b_key = %s:\n' % b_key +
                    'defi field 50, ' +
                    'unknown code: %#.2x' % fields.code_transcription_50
                )

        if fields.b_transcription_60:
            if fields.code_transcription_60 == 0x1b:
                fields.u_transcription_60, singleEncoding = \
                    self.decodeCharsetTags(
                        fields.b_transcription_60,
                        self.sourceEncoding,
                    )
                fields.u_transcription_60 = \
                    replaceHtmlEntries(fields.u_transcription_60)
                fields.u_transcription_60 = \
                    removeControlChars(fields.u_transcription_60)
            else:
                log.debug(
                    'processDefi(%s)\n' % b_defi +
                    'b_key = %s:\n' % b_key +
                    'defi field 60' +
                    'unknown code: %#.2x' % fields.code_transcription_60,
                )

        if fields.b_field_1a:
            fields.u_field_1a, singleEncoding = self.decodeCharsetTags(
                fields.b_field_1a,
                self.sourceEncoding,
            )

        self.processDefiStat(fields, b_defi, b_key)

        u_defi_format = ''
        if fields.partOfSpeech or fields.u_title:
            if fields.partOfSpeech:
                u_defi_format += '<font color="#%s">%s</font>' % (
                    self.partOfSpeechColor,
                    xml_escape(fields.partOfSpeech),
                )
            if fields.u_title:
                if u_defi_format:
                    u_defi_format += ' '
                u_defi_format += fields.u_title
            u_defi_format += '<br>\n'
        if fields.u_title_trans:
            u_defi_format += fields.u_title_trans + '<br>\n'
        if fields.u_transcription_50:
            u_defi_format += '[%s]<br>\n' % fields.u_transcription_50
        if fields.u_transcription_60:
            u_defi_format += '[%s]<br>\n' % fields.u_transcription_60
        if fields.u_defi:
            u_defi_format += fields.u_defi
        return u_defi_format

    def processDefiStat(self, fields, b_defi, b_key):
        pass

    def findDefiFieldsStart(self, b_defi):
        """
        b_defi is a bytes instance

        Finds the beginning of the definition trailing fields.

        Return value is the index of the first chars of the field set,
        or -1 if the field set is not found.

        Normally '\x14' should signal the beginning of the definition fields,
        but some articles may contain this characters inside, so we get false
        match.
        As a workaround we may check the following chars. If '\x14' is followed
        by space, we assume this is part of the article and continue search.
        Unfortunately this does no help in many cases...
        """
        if self.noControlSequenceInDefi:
            return -1
        index = -1
        while True:
            index = b_defi.find(
                0x14,
                index+1,  # starting from next character
                -1,  # not the last character
            )
            if index == -1:
                break
            if b_defi[index+1] != 0x20:  # b' '[0] == 0x20
                break
        return index

    def collectDefiFields(self, b_defi, b_key, fields):
        """
        entry definition structure:
        <main definition>['\x14'[{field_code}{field_data}]*]
        {field_code} is one character
        {field_data} has arbitrary length
        """
        # d0 is index of the '\x14 char in b_defi
        # d0 may be the last char of the string
        d0 = self.findDefiFieldsStart(b_defi)
        if d0 == -1:
            fields.b_defi = b_defi
            return

        fields.b_defi = b_defi[:d0]

        i = d0 + 1
        while i < len(b_defi):
            if self.metadata2:
                self.metadata2.defiTrailingFields[b_defi[i]] += 1

            if b_defi[i] == 0x02:
                # part of speech # '\x02' <one char - part of speech>
                if fields.partOfSpeech:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\n' % b_key +
                        'duplicate part of speech item',
                    )
                if i+1 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nb_defi ends after \\x02' % b_key
                    )
                    return

                posCode = b_defi[i+1]

                try:
                    fields.partOfSpeech = partOfSpeechByCode[posCode]
                except KeyError:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\n' % b_key +
                        'unknown part of speech code = %#.2x' % posCode
                    )
                    return
                i += 2
            elif b_defi[i] == 0x06:  # \x06<one byte>
                if fields.b_field_06:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nduplicate type 6' % b_key
                    )
                if i+1 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nb_defi ends after \\x06' % b_key
                    )
                    return
                fields.b_field_06 = b_defi[i+1]
                i += 2
            elif b_defi[i] == 0x07:  # \x07<two bytes>
                # Found in 4 Hebrew dictionaries. I do not understand.
                if i+3 > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x07' % b_key
                    )
                    return
                fields.b_field_07 = b_defi[i+1:i+3]
                i += 3
            elif b_defi[i] == 0x13:  # '\x13'<one byte - length><data>
                # known values:
                # 03 06 0D C7
                # 04 00 00 00 44
                # ...
                # 04 00 00 00 5F
                if i + 1 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x13' % b_key
                    )
                    return
                Len = b_defi[i+1]
                i += 2
                if Len == 0:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nblank data after \\x13' % b_key
                    )
                    continue
                if i+Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x13' % b_key
                    )
                    return
                fields.b_field_13 = b_defi[i:i+Len]
                i += Len
            elif b_defi[i] == 0x18:
                # \x18<one byte - title length><entry title>
                if fields.b_title:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nduplicate entry title item' % b_key
                    )
                if i+1 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nb_defi ends after \\x18' % b_key
                    )
                    return
                i += 1
                Len = b_defi[i]
                i += 1
                if Len == 0:
                    # log.debug(
                    #    'collecting definition fields, b_defi = %r\n'%b_defi +
                    #    'b_key = %r:\nblank entry title'%b_key
                    # )
                    continue
                if i + Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntitle is too long' % b_key
                    )
                    return
                fields.b_title = b_defi[i:i+Len]
                i += Len
            elif b_defi[i] == 0x1a:  # '\x1a'<one byte - length><text>
                # found only in Hebrew dictionaries, I do not understand.
                if i + 1 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %s:\ntoo few data after \\x1a' % b_key
                    )
                    return
                Len = b_defi[i+1]
                i += 2
                if Len == 0:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nblank data after \\x1a' % b_key
                    )
                    continue
                if i+Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x1a' % b_key
                    )
                    return
                fields.b_field_1a = b_defi[i:i+Len]
                i += Len
            elif b_defi[i] == 0x28:  # '\x28' <two bytes - length><html text>
                # title with transcription?
                if i + 2 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x28' % b_key
                    )
                    return
                i += 1
                Len = binStrToInt(b_defi[i:i+2])
                i += 2
                if Len == 0:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nblank data after \\x28' % b_key
                    )
                    continue
                if i+Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x28' % b_key
                    )
                    return
                fields.b_title_trans = b_defi[i:i+Len]
                i += Len
            elif 0x40 <= b_defi[i] <= 0x4f:  # [\x41-\x4f] <one byte> <text>
                # often contains digits as text:
                # 56
                # &#0230;lps - key Alps
                # 48@i
                # has no apparent influence on the article
                code = b_defi[i]
                Len = b_defi[i] - 0x3f
                if i+2+Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x40+' % b_key
                    )
                    return
                i += 2
                b_text = b_defi[i:i+Len]
                i += Len
                log.debug(
                    '\nunknown definition field %#.2x' % code +
                    ', b_text=%r' % b_text
                )
            elif b_defi[i] == 0x50:
                # \x50 <one byte> <one byte - length><data>
                if i + 2 >= len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x50' % b_key
                    )
                    return
                fields.code_transcription_50 = b_defi[i+1]
                Len = b_defi[i+2]
                i += 3
                if Len == 0:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nblank data after \\x50' % b_key
                    )
                    continue
                if i+Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x50' % b_key
                    )
                    return
                fields.b_transcription_50 = b_defi[i:i+Len]
                i += Len
            elif b_defi[i] == 0x60:
                # '\x60' <one byte> <two bytes - length> <text>
                if i + 4 > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x60' % b_key
                    )
                    return
                fields.code_transcription_60 = b_defi[i+1]
                i += 2
                Len = binStrToInt(b_defi[i:i+2])
                i += 2
                if Len == 0:
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\nblank data after \\x60' % b_key
                    )
                    continue
                if i+Len > len(b_defi):
                    log.debug(
                        'collecting definition fields, ' +
                        'b_defi = %r\n' % b_defi +
                        'b_key = %r:\ntoo few data after \\x60' % b_key
                    )
                    return
                fields.b_transcription_60 = b_defi[i:i+Len]
                i += Len
            else:
                log.debug(
                    'collecting definition fields, ' +
                    'b_defi = %r\n' % b_defi +
                    'b_key = %r:\n' % b_key +
                    'unknown control char. Char code = %#.2x' % b_defi[i]
                )
                return
