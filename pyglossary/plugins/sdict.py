# -*- coding: utf-8 -*-
# sdict.py
# Loader engine for AXMASoft's open dictionary format
#
# Copyright (C) 2010-2016 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright (C) 2006-2008 Igor Tkach, as part of SDict Viewer:
#               http://sdictviewer.sf.net
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

from struct import unpack
from formats_common import *

enable = True
format = 'Sdict'
description = 'Sdictionary Binary(dct)'
extentions = ['.dct']
readOptions = [
    'encoding',  # str
]
writeOptions = []


class GzipCompression(object):
    def __str__(self):
        return 'gzip'

    def decompress(self, string):
        import zlib
        return zlib.decompress(string)


class Bzip2Compression(object):
    def __str__(self):
        return 'bzip2'

    def decompress(self, string):
        import bz2
        return bz2.decompress(string)


class NoCompression(object):
    def __str__(self):
        return 'no compression'

    def decompress(self, string):
        return string


compressions = [
    NoCompression(),
    GzipCompression(),
    Bzip2Compression(),
]


def read_raw(s, fe):
    return s[fe.offset:fe.offset + fe.length]


def read_str(s, fe):
    read_raw(s, fe).replace(b'\x00', b'')


def read_int(s, fe=None):
    return unpack('<I', read_raw(s, fe) if fe else s)[0]


def read_short(raw):
    return unpack('<H', raw)[0]


def read_byte(raw):
    return unpack('<B', raw)[0]


class FormatElement(object):
    def __init__(self, offset, length):
        self.offset = offset
        self.length = length


class Header(object):
    f_signature = FormatElement(0x0, 4)
    f_input_lang = FormatElement(0x4, 3)
    f_output_lang = FormatElement(0x7, 3)
    f_compression = FormatElement(0xa, 1)
    f_num_of_words = FormatElement(0xb, 4)
    f_length_of_short_index = FormatElement(0xf, 4)
    f_title = FormatElement(0x13, 4)
    f_copyright = FormatElement(0x17, 4)
    f_version = FormatElement(0x1b, 4)
    f_short_index = FormatElement(0x1f, 4)
    f_full_index = FormatElement(0x23, 4)
    f_articles = FormatElement(0x27, 4)

    def parse(self, st):
        self.signature = read_str(st, self.f_signature)
        if self.signature != b'sdct':
            raise ValueError('Not a valid sdict dictionary')
        self.word_lang = read_str(st, self.f_input_lang)
        self.article_lang = read_str(st, self.f_output_lang)
        self.short_index_length = read_int(st, self.f_length_of_short_index)
        comp_and_index_levels_byte = read_byte(
            read_raw(st, self.f_compression)
        )
        self.compressionType = comp_and_index_levels_byte & 0b1111
        self.short_index_depth = comp_and_index_levels_byte >> 4
        self.num_of_words = read_int(st, self.f_num_of_words)
        self.title_offset = read_int(st, self.f_title)
        self.copyright_offset = read_int(st, self.f_copyright)
        self.version_offset = read_int(st, self.f_version)
        self.articles_offset = read_int(st, self.f_articles)
        self.short_index_offset = read_int(st, self.f_short_index)
        self.full_index_offset = read_int(st, self.f_full_index)


class Reader(object):
    def __init__(self, glos):
        self._glos = glos
        self.clear()

    def clear(self):
        self._file = None
        self._filename = ''
        self._encoding = ''
        self._header = Header()

    def open(self, filename, encoding='utf-8'):
        self._file = open(filename, 'rb')
        self._header.parse(self._file.read(43))
        self._compression = compressions[self._header.compressionType]
        self.short_index = self.readShortIndex()
        self._glos.setInfo(
            'name',
            self.readUnit(self._header.title_offset),
        )
        self._glos.setInfo(
            'version',
            self.readUnit(self._header.version_offset)
        )
        self._glos.setInfo(
            'copyright',
            self.readUnit(self._header.copyright_offset),
        )
        log.debug('SDict word count: %s' % len(self))  # correct? FIXME

    def close(self):
        self._file.close()
        self.clear()

    def __len__(self):
        return self._header.num_of_words

    def readUnit(self, pos):
        f = self._file
        f.seek(pos)
        record_length = read_int(f.read(4))
        return self._compression.decompress(f.read(record_length))

    def readShortIndex(self):
        self._file.seek(self._header.short_index_offset)
        s_index_depth = self._header.short_index_depth
        index_entry_len = (s_index_depth+1)*4
        short_index_str = self._file.read(
            index_entry_len * self._header.short_index_length
        )
        short_index_str = self._compression.decompress(short_index_str)
        index_length = self._header.short_index_length
        short_index = [{} for i in range(s_index_depth+2)]
        depth_range = range(s_index_depth)
        for i in range(index_length):
            entry_start = start_index = i*index_entry_len
            short_word = ''
            try:
                for j in depth_range:
                    # inlined unpack yields ~20% performance gain
                    # compared to calling read_int()
                    uchar_code = unpack(
                        '<I',
                        short_index_str[start_index:start_index+4]
                    )[0]
                    start_index += 4
                    if uchar_code == 0:
                        break
                    short_word += chr(uchar_code)
            except ValueError as ve:
                # If Python is built without wide unicode support (which is
                # the case on Maemo) it may not be possible to use some
                # unicode chars. It seems best to ignore such index items
                # The rest of the dictionary should be usable.
                log.error(
                    'Failed to decode short index item %s' % i +
                    ', will ignore: %s' % ve
                )
                continue
            pointer_start = entry_start+s_index_depth*4
            pointer = unpack(
                '<I',
                short_index_str[pointer_start:pointer_start+4]
            )[0]
            short_index[len(short_word)][short_word] = pointer
        return short_index

    def __iter__(self):
        pos = self._header.full_index_offset
        next_ptr = 0
        while True:
            pos += next_ptr
            item = self.readFullIndexItem(pos)
            if item is None:
                break
            (next_ptr, word, ptr) = item
            if word is None:
                break
            word = toStr(word)
            defi = self.readUnit(self._header.articles_offset + ptr)
            defi = toStr(defi)
            defi = defi.replace('<BR>', '\n').replace('<br>', '\n')
            yield self._glos.newEntry(word, defi)

    def readFullIndexItem(self, pointer):
        try:
            f = self._file
            f.seek(pointer)
            s = f.read(8)
            next_word = unpack('<H', s[:2])[0]
            article_pointer = unpack('<I', s[4:])[0]
            word = f.read(next_word - 8) if next_word else None
            return next_word, word, article_pointer
        except Exception as e:
            if pointer >= self._header.articles_offset:
                log.error(
                    'Warning: attempt to read word from '
                    'illegal position in dict file'
                )
                return None
            log.exception('')

    def readArticle(self, pointer):
        return self.readUnit(self._header.articles_offset + pointer)
