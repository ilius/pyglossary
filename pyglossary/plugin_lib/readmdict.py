#!/usr/bin/env python
# -*- coding: utf-8 -*-
## readmdict.py
## Octopus MDict Dictionary File (.mdx) and Resource File (.mdd) Analyser
##
## Copyright (C) 2012, 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, version 3 of the License.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

from struct import pack, unpack
import re

import logging
log = logging.getLogger('root')

# zlib compression is used for engine version >=2.0
import zlib
# LZO compression is used for engine version < 2.0
try:
    import lzo
    HAVE_LZO = True
except:
    HAVE_LZO = False
    log.warning("LZO compression support is not available")


def _unescape_entities(text):
    """
    unescape offending tags < > " &
    """
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    return text

class MDict(object):
    """
    Base class which reads in header and key block.
    It has no public methods and serves only as code sharing base class.
    """
    def __init__(self, fname, encoding=''):
        self._fname = fname
        self._encoding = encoding.upper()

        self.header   = self._read_header()
        self._key_list = self._read_keys()

    def __len__(self):
        return self._num_entries

    def __iter__(self):
        return self.keys()

    def keys(self):
        """
        Return an iterator over dictionary keys.
        """
        return (key_value for key_id, key_value in self._key_list)

    def _read_number(self, f):
        return unpack(self._number_format, f.read(self._number_width))[0]

    def _parse_header(self, header):
        """
        extract attributes from <Dict attr="value" ... >
        """
        taglist = re.findall('(\w+)="(.*?)"', header, re.DOTALL)
        tagdict = {}
        for key, value in taglist:
            tagdict[key] = _unescape_entities(value)
        return tagdict

    def _decode_key_block_info(self, key_block_info):
        # zlib compressed for version > 2
        if self._version >= 2:
            # \x02\x00\x00\x00
            assert(key_block_info[:4] == '\x02\x00\x00\x00')
            # 4 bytes as a checksum
            assert(key_block_info[4:8] == key_block_info[-4:])
            # decompress
            key_block_info = zlib.decompress(key_block_info[8:])
        # decode
        key_block_info_list = []
        i = 0
        if self._version >= 2:
            byte_format = '>H'
            byte_width  = 2
            text_term   = 1
        else:
            byte_format = '>B'
            byte_width  = 1
            text_term   = 0

        while i < len(key_block_info):
            # unknow
            unpack(self._number_format, key_block_info[i:i+self._number_width])[0]
            i += self._number_width
            # text head size
            text_head_size = unpack(byte_format, key_block_info[i:i+byte_width])[0]
            i += byte_width
            # text head
            if self._encoding != 'UTF-16':
                i += text_head_size + text_term
            else:
                i += (text_head_size + text_term) * 2
            # text tail size
            text_tail_size = unpack(byte_format, key_block_info[i:i+byte_width])[0]
            i += byte_width
            # text tail
            if self._encoding != 'UTF-16':
                i += text_tail_size + text_term
            else:
                i += (text_tail_size + text_term) * 2
            # key block compressed size
            key_block_compressed_size = unpack(self._number_format, key_block_info[i:i+self._number_width])[0]
            i += self._number_width
            # key block decompressed size
            key_block_decompressed_size = unpack(self._number_format, key_block_info[i:i+self._number_width])[0]
            i += self._number_width
            key_block_info_list += [(key_block_compressed_size, key_block_decompressed_size)]
        return key_block_info_list

    def _decode_key_block(self, key_block_compressed, key_block_info_list):
        key_list = []
        i = 0
        for compressed_size, decompressed_size in key_block_info_list:
            start = i;
            end = i + compressed_size
            # 4 bytes : compression type
            key_block_type = key_block_compressed[start:start+4]
            if key_block_type == '\x00\x00\x00\x00':
                # extract one single key block into a key list
                key_list += self._split_key_block(key_block_compressed[start+8:end])
            elif key_block_type == '\x01\x00\x00\x00':
                if not HAVE_LZO:
                    log.error("LZO compression is not supported")
                    break
                # 4 bytes as adler32 checksum
                adler32 = unpack('>I', key_block_compressed[start+4:start+8])[0]
                # decompress key block
                header = '\xf0' + pack('>I', decompressed_size)
                key_block = lzo.decompress(header + key_block_compressed[start+8:end])
                # notice that lzo 1.x return signed value
                assert(adler32 == lzo.adler32(key_block) & 0xffffffff)
                # extract one single key block into a key list
                key_list += self._split_key_block(key_block)
            elif key_block_type == '\x02\x00\x00\x00':
                # 4 bytes same as end of block
                assert(key_block_compressed[start+4:start+8] == key_block_compressed[end-4:end])
                # decompress key block
                key_block = zlib.decompress(key_block_compressed[start+self._number_width:end])
                # extract one single key block into a key list
                key_list += self._split_key_block(key_block)
            i += compressed_size
        return key_list

    def _split_key_block(self, key_block):
        key_list = []
        key_start_index = 0
        while key_start_index < len(key_block):
            # the corresponding record's offset in record block
            key_id = unpack(self._number_format, key_block[key_start_index:key_start_index+self._number_width])[0]
            # key text ends with '\x00'
            if self._encoding == 'UTF-16':
                delimiter = '\x00\x00'
                width = 2
            else:
                delimiter = '\x00'
                width = 1
            i = key_start_index + self._number_width
            while i < len(key_block):
                if key_block[i:i+width] == delimiter:
                    key_end_index = i
                    break
                i += width
            key_text = key_block[key_start_index+self._number_width:key_end_index].decode(self._encoding, errors='ignore').encode('utf-8').strip()
            key_start_index = key_end_index + width
            key_list += [(key_id, key_text)]
        return key_list



    def _read_header(self):
        f = open(self._fname, 'rb')
        # number of bytes of header text
        header_text_size = unpack('>I', f.read(4))[0]
        # text in utf-16 encoding ending with '\x00\x00'
        header_text = f.read(header_text_size)[:-2].decode('utf-16').encode('utf-8')
        header_tag = self._parse_header(header_text)
        if not self._encoding:
            encoding = header_tag['Encoding']
            # GB18030 > GBK > GB2312
            if encoding in ['GBK', 'GB2312']:
                encoding = 'GB18030'
            self._encoding = encoding

        # stylesheet attribute if present takes form of:
        #   style_number # 1-255
        #   style_begin  # or ''
        #   style_end    # or ''
        # store stylesheet in dict in the form of
        # {'number' : ('style_begin', 'style_end')}
        self._stylesheet = {}
        if header_tag.get('StyleSheet'):
            lines = header_tag['StyleSheet'].splitlines()
            for i in range(0, len(lines), 3):
                self._stylesheet[lines[i]] = (lines[i+1], lines[i+2])

        # before version 2.0, number is 4 bytes integer
        # version 2.0 and above uses 8 bytes
        self._version = float(header_tag['GeneratedByEngineVersion'])
        if self._version < 2.0:
            self._number_width = 4
            self._number_format = '>I'
        else:
            self._number_width = 8
            self._number_format = '>Q'

        # 4 bytes unknown
        f.read(4).encode('hex')
        self._key_block_offset = f.tell()
        f.close()

        return header_tag

    def _read_keys(self):
        f = open(self._fname, 'rb')
        f.seek(self._key_block_offset)
        # number of key blocks
        num_key_blocks = self._read_number(f)
        # number of entries
        self._num_entries =  self._read_number(f)

        # unkown
        if self._version >= 2.0:
            self._read_number(f)
        # number of bytes of key block info
        key_block_info_size = self._read_number(f)
        # number of bytes of key block
        key_block_size = self._read_number(f)

        # 4 bytes unknown
        if self._version >= 2.0:
            f.read(4)

        # read key block info, which indicates key block's compressed and decompressed size
        key_block_info = f.read(key_block_info_size)
        try:
            key_block_info_list = self._decode_key_block_info(key_block_info)
            assert(num_key_blocks == len(key_block_info_list))
        except:
            key_block_info_list = []
            log.exception('Cannot Decode Key Block Info Section. Try Brutal Force.')

        # read key block
        key_block_compressed = f.read(key_block_size)

        # extract key block
        key_list = []
        if key_block_info_list:
            key_list = self._decode_key_block(key_block_compressed, key_block_info_list)
        else:
            for key_block in key_block_compressed.split('\x02\x00\x00\x00')[1:]:
                key_block_decompressed = zlib.decompress(key_block[4:])
                key_list += self._split_key_block(key_block_decompressed)

        self._record_block_offset = f.tell()
        f.close()

        return key_list

class MDD(MDict):
    """
    MDict resource file format (*.MDD) reader.
    >>> mdd = MDD('example.mdd')
    >>> len(mdd)
    208
    >>> for filename, content in mdd.items():
    ... print(filename, content[:10])
    """
    def __init__(self, fname):
        MDict.__init__(self, fname, encoding='UTF-16')

    def items(self):
        """Return a generator which in turn produce tuples in the form of (filename, content)
        """
        return self._decode_record_block()

    def _decode_record_block(self):
        f = open(self._fname, 'rb')
        f.seek(self._record_block_offset)

        num_record_blocks       = self._read_number(f)
        num_entries             = self._read_number(f)
        assert(num_entries == self._num_entries)
        record_block_info_size  = self._read_number(f)
        record_block_size       = self._read_number(f)

        # record block info section
        record_block_info_list = []
        size_counter = 0
        for i in range(num_record_blocks):
            compressed_size = self._read_number(f)
            decompressed_size = self._read_number(f)
            record_block_info_list += [(compressed_size, decompressed_size)]
            size_counter += self._number_width * 2
        assert(size_counter == record_block_info_size)

        # actual record block
        offset = 0
        i = 0
        size_counter = 0
        for compressed_size, decompressed_size in record_block_info_list:
            record_block_compressed = f.read(compressed_size)
            record_block_type = record_block_compressed[:4]
            if record_block_type == '\x00\x00\x00\x00':
                record_block = record_block_compressed[8:]
            elif record_block_type == '\x01\x00\x00\x00':
                if not HAVE_LZO:
                    log.error("LZO compression is not supported")
                    break
                # 4 bytes as adler32 checksum
                adler32 = unpack('>I', record_block_compressed[4:8])[0]
                # decompress
                header = '\xf0' + pack('>I', decompressed_size)
                record_block = lzo.decompress(header + record_block_compressed[8:])
                # notice that lzo 1.x return signed value
                assert(adler32 == lzo.adler32(record_block) & 0xffffffff)
            elif record_block_type == '\x02\x00\x00\x00':
                # 4 bytes as checksum
                assert(record_block_compressed[4:8] == record_block_compressed[-4:])
                # compressed contents
                record_block = zlib.decompress(record_block_compressed[8:])
            assert(len(record_block) == decompressed_size)
            # split record block according to the offset info from key block
            while i < len(self._key_list):
                record_start, key_text = self._key_list[i]
                # reach the end of current record block
                if record_start - offset >= len(record_block):
                    break
                # record end index
                if i < len(self._key_list)-1:
                    record_end = self._key_list[i+1][0]
                else:
                    record_end = len(record_block) + offset
                i += 1
                data = record_block[record_start-offset:record_end-offset]
                yield key_text, data
            offset += len(record_block)
            size_counter += compressed_size
        assert(size_counter == record_block_size)

        f.close()

class MDX(MDict):
    """
    MDict dictionary file format (*.MDD) reader.
    >>> mdx = MDX('example.mdx')
    >>> len(mdx)
    42481
    >>> for key, value in mdx.items():
    ... print(key, value[:10])
    """
    def __init__(self, fname, encoding='', substyle=False):
        MDict.__init__(self, fname, encoding)
        self._substyle = substyle

    def items(self):
        """Return a generator which in turn produce tuples in the form of (key, value)
        """
        return self._decode_record_block()

    def _substitute_stylesheet(self, txt):
        # substitute stylesheet definition
        txt_list = re.split('`\d+`', txt)
        txt_tag  = re.findall('`\d+`', txt)
        txt_styled = txt_list[0]
        for  j, p in enumerate(txt_list[1:]):
            style = self._stylesheet[txt_tag[j][1:-1]]
            if p and p[-1] == '\n':
                txt_styled = txt_styled + style[0] + p.rstrip() + style[1] + '\r\n'
            else:
                txt_styled = txt_styled + style[0] + p + style[1]
        return txt_styled

    def _decode_record_block(self):
        f = open(self._fname, 'rb')
        f.seek(self._record_block_offset)

        num_record_blocks       = self._read_number(f)
        num_entries             = self._read_number(f)
        assert(num_entries == self._num_entries)
        record_block_info_size  = self._read_number(f)
        record_block_size       = self._read_number(f)

        # record block info section
        record_block_info_list = []
        size_counter = 0
        for i in range(num_record_blocks):
            compressed_size     = self._read_number(f)
            decompressed_size   = self._read_number(f)
            record_block_info_list += [(compressed_size, decompressed_size)]
            size_counter += self._number_width * 2
        assert(size_counter == record_block_info_size)

        # actual record block data
        offset = 0
        i = 0
        size_counter = 0
        for compressed_size, decompressed_size in record_block_info_list:
            record_block_compressed = f.read(compressed_size)
            # 4 bytes indicates block compression type
            record_block_type = record_block_compressed[:4]
            # no compression
            if record_block_type == '\x00\x00\x00\x00':
                record_block = record_block_compressed[8:]
            # lzo compression
            elif record_block_type == '\x01\x00\x00\x00':
                if not HAVE_LZO:
                    log.error("LZO compression is not supported")
                    break
                # 4 bytes as adler32 checksum
                adler32 = unpack('>I', record_block_compressed[4:8])[0]
                # decompress
                header = '\xf0' + pack('>I', decompressed_size)
                record_block = lzo.decompress(header + record_block_compressed[8:])
                # notice that lzo 1.x return signed value
                assert(adler32 == lzo.adler32(record_block) & 0xffffffff)
            # zlib compression
            elif record_block_type == '\x02\x00\x00\x00':
                # 4 bytes as checksum
                assert(record_block_compressed[4:8] == record_block_compressed[-4:])
                # compressed contents
                record_block = zlib.decompress(record_block_compressed[8:])
            assert(len(record_block) == decompressed_size)
            # split record block according to the offset info from key block
            while i < len(self._key_list):
                record_start, key_text = self._key_list[i]
                # reach the end of current record block
                if record_start - offset >= len(record_block):
                    break
                # record end index
                if i < len(self._key_list)-1:
                    record_end = self._key_list[i+1][0]
                else:
                    record_end = len(record_block) + offset
                i += 1
                record = record_block[record_start-offset:record_end-offset]
                # convert to utf-8
                record = record.decode(self._encoding, errors='ignore').strip(u'\x00').encode('utf-8')
                # substitute styles
                if self._substyle and self._stylesheet:
                    record = self._substitute_stylesheet(record)

                yield key_text, record
            offset += len(record_block)
            size_counter += compressed_size
        assert(size_counter == record_block_size)

        f.close()


if __name__ == '__main__':
    import os
    import os.path
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--extract', action="store_true",
                        help='extract mdx to source format and extract files from mdd')
    parser.add_argument('-s', '--substyle', action="store_true",
                        help='substitute style definition if present')
    parser.add_argument('-d', '--datafolder', default="data",
                        help='folder to extract data files from mdd')
    parser.add_argument('-e', '--encoding', default="",
                        help='folder to extract data files from mdd')
    parser.add_argument("filename", nargs='?', help="mdx file name")
    args = parser.parse_args()

    # use GUI to select file, default to extract
    if not args.filename:
        import Tkinter
        import tkFileDialog
        root = Tkinter.Tk() ; root.withdraw()
        args.filename = tkFileDialog.askopenfilename(parent=root)
        args.extract = True

    if not os.path.exists(args.filename):
        log.error("Please specify a valid MDX/MDD file")

    base, ext = os.path.splitext(args.filename)

    # read mdx file
    if ext.lower() == os.path.extsep + 'mdx':
        mdx = MDX(args.filename, args.encoding, args.substyle)
        if isinstance(args.filename, unicode):
            fname = args.filename.encode('utf-8')
        else:
            fname = args.filename
        log.info('filename: %s'%fname)
        log.info('number of Entries: %s'%len(mdx))
        for key, value in mdx.header.items():
            log.debug('%s: %s'%(key, value))
    else:
        mdx = None

    # find companion mdd file
    mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
    if (os.path.exists(mdd_filename)):
        mdd = MDD(mdd_filename)
        if isinstance(mdd_filename, unicode):
            fname = mdd_filename.encode('utf-8')
        else:
            fname = mdd_filename
        log.info('filename: %s'%fname)
        log.info('number of Entries: %s'%len(mdx))
        for key, value in mdx.header.items():
            log.debug('%s: %s'%(key, value))
    else:
        mdd = None

    if args.extract:
        # write out glos
        if mdx:
            output_fname = ''.join([base, os.path.extsep, 'txt'])
            f = open(output_fname, 'wb')
            for key, value in mdx.items():
                f.write(key)
                f.write('\r\n')
                f.write(value)
                f.write('\r\n')
                f.write('</>\r\n')
            f.close()
            # write out style
            if mdx.header.get('StyleSheet'):
                style_fname = ''.join([base, '_style', os.path.extsep, 'txt'])
                f = open(style_fname, 'wb')
                f.write('\r\n'.join(mdx.header['StyleSheet'].splitlines()))
                f.close()
        # write out optional data files
        if mdd:
            datafolder = os.path.join(os.path.dirname(args.filename), args.datafolder)
            if not os.path.exists(datafolder):
                os.makedirs(datafolder)
            for key, value in mdd.items():
                fname = ''.join([datafolder, key.replace('\\', os.path.sep).decode('utf-8')]);
                if not os.path.exists(os.path.dirname(fname)):
                    os.makedirs(os.path.dirname(fname))
                f = open(fname, 'wb')
                f.write(value)
                f.close()
