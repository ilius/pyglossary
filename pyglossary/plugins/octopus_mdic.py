# -*- coding: utf-8 -*-
## octopus_mdic.py
## Read Octopus MDict dictionary format, mdx(dictionary)/mdd(data)
##
## Copyright (C) 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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

from struct import unpack
import zlib
import os
from xml.etree.ElementTree import XMLParser

enable = True
format = 'OctopusMdic'
description = 'Octopus MDic'
extentions = ['.mdx']
readOptions = ['resPath']
writeOptions = []

def readmdd(fname):
    f = open(fname, 'rb')

    ################################################################################
    #      Header Block
    ################################################################################

    # 4 bytes integer : number of bytes of header text
    header_text_size = unpack('>I', f.read(4))[0]
    # text in utf-16
    header_text = f.read(header_text_size)[:-2]
    parser = XMLParser(encoding='utf-16')
    parser.feed(header_text)
    header_tag = parser.close()

    # 4 bytes unknown
    flag1 = f.read(4).encode('hex')

    ################################################################################
    #      Key Block
    ################################################################################

    # 8 bytes long long : number of key blocks
    num_key_blocks = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of entries
    num_entries =  unpack('>Q', f.read(8))[0]
    # 8 bytes long long : unkown
    unknown = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of unknown block 1
    unknown_block_1_size = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of key block
    key_block_size = unpack('>Q', f.read(8))[0]

    # 4 bytes : unknown
    unknown = f.read(4)

    # read unknown block 1
    unknown_block_1 = f.read(unknown_block_1_size)

    # read key block
    key_block_compressed = f.read(key_block_size)

    # extract key block
    key_block_list = []

    # \x02\x00\x00\x00 leads each key block
    for block in key_block_compressed.split('\x02\x00\x00\x00')[1:]:
        # decompress key block
        key_block = zlib.decompress(block[4:])
        # extract one single key block
        key_start_index = 0
        while key_start_index < len(key_block):
            # 8 bytes long long : the corresponding record's offset
            # in record block
            key_id = unpack('>Q', key_block[key_start_index:key_start_index+8])[0]
            # key text ends with '\x00\x00'
            for key_end_index in range(key_start_index + 8, len(key_block), 2):
                if key_block[key_end_index:key_end_index + 2] == '\x00\x00':
                    break

            key_text = key_block[key_start_index+8:key_end_index]
            key_start_index = key_end_index + 2
            key_block_list += [(key_id, key_text.decode('utf-16').encode('utf-8'))]

    ################################################################################
    #      Record Block
    ################################################################################

    # 8 bytes long long : number of record blocks
    num_record_blocks = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of entries
    num_entries = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of record blocks info section
    num_record_block_info_bytes = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of byets of actual record blocks
    total_record_block_bytes = unpack('>Q', f.read(8))[0]

    # record block info section
    record_block_info_list = []
    for i in range(num_record_blocks):
        # 8 bytes long long : number of bytes of record block
        current_record_block_size = unpack('>Q', f.read(8))[0]
        # 8 bytes long long : number of bytes of record block decompressed
        decompressed_block_size = unpack('>Q', f.read(8))[0]
        record_block_info_list += [(current_record_block_size, decompressed_block_size)]

    # actual record block
    record_block = ''
    for current_record_block_size, decompressed_block_size in record_block_info_list:
        current_record_block = f.read(current_record_block_size)
        current_record_block_text = zlib.decompress(current_record_block[8:])
        assert(len(current_record_block_text) == decompressed_block_size)
        record_block = record_block + current_record_block_text

    # merge record block and key_block_list
    data = []
    for i, (key_start, key_text) in enumerate(key_block_list):
        if i < len(key_block_list)-1:
            key_end = key_block_list[i+1][0]
        else:
            key_end = None
        data.append((key_text, record_block[key_start:key_end]))

    return data

def readmdx(glos, fname):
    f = open(fname, 'rb')

    ################################################################################
    #      Header Block
    ################################################################################

    # integer : number of bytes of header text
    header_text_size = unpack('>I', f.read(4))[0]
    # text in utf-16 encoding
    header_text = f.read(header_text_size)[:-2]
    parser = XMLParser(encoding='utf-16')
    parser.feed(header_text)
    header_tag = parser.close()
    glos.setInfo('title', header_tag.attrib.get('Title', os.path.basename(fname)).encode('utf-8'))
    glos.setInfo('description', header_tag.attrib.get('Description', u'').encode('utf-8'))
    encoding = header_tag.attrib.get('Encoding', 'utf-8')

    # 4 bytes unknown
    flag1 = f.read(4).encode('hex')

    ################################################################################
    #      Key Block
    ################################################################################

    # 8 bytes long long : number of key blocks
    num_key_blocks = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of entries
    num_entries =  unpack('>Q', f.read(8))[0]
    # 8 bytes long long : unkown
    num1 = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of unknown block 1
    unknown_block_1_size = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of key block
    key_block_size = unpack('>Q', f.read(8))[0]

    # 4 bytes unknown
    unknown = f.read(4)

    # read unknown block 1
    unknown_block_1 = f.read(unknown_block_1_size)
    # read key block
    key_block_compressed = f.read(key_block_size)

    # extract key block
    key_list = []

    # \x02\x00\x00\x00 leads each key block
    key_block_list = key_block_compressed.split('\x02\x00\x00\x00')
    for block in key_block_list[1:]:
        # decompress key block
        key_block = zlib.decompress(block[4:])
        # extract one single key block
        key_start_index = 0
        while key_start_index < len(key_block):
            # 8 bytes long long : the corresponding record's offset
            # in record block
            key_id = unpack('>Q', key_block[key_start_index:key_start_index+8])[0]
            # key text ends with '\x00'
            key_end_index = key_start_index + 8
            for a in key_block[key_start_index+8:]:
                key_end_index += 1
                if a == '\x00':
                    break
            key_text = key_block[key_start_index+8:key_end_index-1]
            key_start_index = key_end_index
            key_list += [(key_id, key_text)]

    ################################################################################
    #      Record Block
    ################################################################################

    # 8 bytes long long : number of record blocks
    num_record_blocks = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of entries
    num_entries = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of record blocks info section
    num_record_block_info_bytes = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of byets of actual record blocks
    total_record_block_bytes = unpack('>Q', f.read(8))[0]

    # record block info section
    record_block_info_list = []
    for i in range(num_record_blocks):
        # 8 bytes long long : number of bytes of current record block
        current_record_block_size = unpack('>Q', f.read(8))[0]
        # 8 bytes long long : number of bytes if current record block decompressed
        decompressed_block_size = unpack('>Q', f.read(8))[0]
        record_block_info_list += [(current_record_block_size, decompressed_block_size)]

    # actual record block data
    record_block = []
    for current_record_block_size, unknown_size in record_block_info_list:
        current_record_block = f.read(current_record_block_size)
        current_record_block_text = zlib.decompress(current_record_block[8:])
        #assert(len(current_record_block_text) == decompressed_block_size)
        # image source path should be relative and not start with "/"
        current_record_block_text.replace('src="/', 'src="')
        record_block += current_record_block_text.split('\x00')[:-1]

    # merge key_block and record_block
    glos.data = []
    for key, record in zip(key_list, record_block):
        glos.data.append((key[1], record,))
    f.close()

def read(glos, filename, **options):
    # read mdx dictionary
    readmdx(glos, filename)

    # find companion mdd file
    base,ext = os.path.splitext(filename)
    mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
    if (os.path.exists(mdd_filename)):
        data = readmdd(mdd_filename)
    else:
        data = None

    # write out optional data files
    if data:
        datafolder = options.get('resPath', base + '_files')
        if not os.path.exists(datafolder):
            os.makedirs(datafolder)
        for entry in data:
            fname = ''.join([datafolder, entry[0].replace('\\', os.path.sep)]);
            if not os.path.exists(os.path.dirname(fname)):
                os.makedirs(os.path.dirname(fname))
            f = open(fname, 'wb')
            f.write(entry[1])
            f.close()
