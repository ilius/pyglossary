#!/usr/bin/env python
# -*- coding: utf-8 -*-
# readmdict.py from https://bitbucket.org/xwang/mdict-analysis
# Octopus MDict Dictionary File (.mdx) and Resource File (.mdd) Analyser
#
# Copyright (C) 2012, 2013, 2015, 2022 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
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

import logging
log = logging.getLogger(__name__)

from struct import pack, unpack
from io import BytesIO
import re
import sys

from .ripemd128 import ripemd128
from .pureSalsa20 import Salsa20

# zlib compression is used for engine version >=2.0
import zlib
# LZO compression is used for engine version < 2.0
try:
	import lzo
except ImportError:
	lzo = None

# xxhash is used for engine version >= 3.0
try:
	import xxhash
except ImportError:
	xxhash = None

# 2x3 compatible
if sys.hexversion >= 0x03000000:
	str, unicode = bytes, str


def _unescape_entities(text):
	"""
	unescape offending tags < > " &
	"""
	text = text.replace(b'&lt;', b'<')
	text = text.replace(b'&gt;', b'>')
	text = text.replace(b'&quot;', b'"')
	text = text.replace(b'&amp;', b'&')
	return text


def _fast_decrypt(data, key):
	"""
	XOR decryption
	"""
	b = bytearray(data)
	key = bytearray(key)
	previous = 0x36
	for i in range(len(b)):
		t = (b[i] >> 4 | b[i] << 4) & 0xff
		t = t ^ previous ^ (i & 0xff) ^ key[i % len(key)]
		previous = b[i]
		b[i] = t
	return bytes(b)


def _salsa_decrypt(ciphertext, encrypt_key):
	"""
	salsa20 (8 rounds) decryption
	"""
	s20 = Salsa20(key=encrypt_key, IV=b"\x00"*8, rounds=8)
	return s20.encryptBytes(ciphertext)


def _decrypt_regcode_by_userid(reg_code, userid):
	userid_digest = ripemd128(userid)
	s20 = Salsa20(key=userid_digest, IV=b"\x00"*8, rounds=8)
	encrypt_key = s20.encryptBytes(reg_code)
	return encrypt_key


class MDict(object):
	"""
	Base class which reads in header and key block.
	It has no public methods and serves only as code sharing base class.
	"""
	def __init__(self, fname, encoding='', passcode=None):
		self._fname = fname
		self._encoding = encoding.upper()
		self._encrypted_key = None

		self.header = self._read_header()

		# decrypt regcode to get the encrypted key
		if passcode is not None:
			regcode, userid = passcode
			if isinstance(userid, unicode):
				userid = userid.encode('utf8')
			self._encrypted_key = _decrypt_regcode_by_userid(regcode, userid)
		# MDict 3.0 encryption key derives from UUID
		elif self._version >= 3.0:
			if xxhash is None:
				raise RuntimeError('xxhash module is needed to read MDict 3.0 format')
			uuid = self.header[b'UUID']
			mid = (len(uuid) + 1) // 2
			self._encrypted_key = xxhash.xxh64_digest(uuid[:mid]) + xxhash.xxh64_digest(uuid[mid:])

		self._key_list = self._read_keys()

	def __repr__(self):
		return (
			f"MDict({self._fname!r}, "
			f"encoding={self._encoding!r}, "
			f"passcode={self._passcode})"
		)

	@property
	def filename(self):
		return self._fname

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

	def _read_int32(self, f):
		return unpack('>I', f.read(4))[0]

	def _parse_header(self, header):
		"""
		extract attributes from <Dict attr="value" ... >
		"""
		taglist = re.findall(rb'(\w+)="(.*?)"', header, re.DOTALL)
		tagdict = {}
		for key, value in taglist:
			tagdict[key] = _unescape_entities(value)
		return tagdict

	def _decode_block(self, block, decompressed_size):
		# block info: compression, encryption
		info = unpack('<L', block[:4])[0]
		compression_method =  info & 0xf
		encryption_method = (info >> 4) & 0xf
		encryption_size = (info >> 8) & 0xff

		# adler checksum of the block data used as the encryption key if none given
		adler32 = unpack('>I', block[4:8])[0]
		encrypted_key = self._encrypted_key
		if encrypted_key is None:
			encrypted_key = ripemd128(block[4:8])

		# block data
		data = block[8:]

		# decrypt
		if encryption_method == 0:
			decrypted_block = data
		elif encryption_method == 1:
			decrypted_block = _fast_decrypt(data[:encryption_size], encrypted_key) + data[encryption_size:]
		elif encryption_method == 2:
			decrypted_block = _salsa_decrypt(data[:encryption_size], encrypted_key) + data[encryption_size:]
		else:
			raise Exception('encryption method %d not supported' % encryption_method)

		# check adler checksum over decrypted data
		if self._version >= 3:
			assert(hex(adler32) == hex(zlib.adler32(decrypted_block) & 0xffffffff))

		# decompress
		if compression_method == 0:
			decompressed_block = decrypted_block
		elif compression_method == 1:
			if lzo is None:
				raise RuntimeError("LZO compression is not supported")
			header = b'\xf0' + pack('>I', decompressed_size)
			decompressed_block = lzo.decompress(header + decrypted_block)
		elif compression_method == 2:
			decompressed_block = zlib.decompress(decrypted_block)
		else:
			raise Exception('compression method %d not supported' % compression_method)

		# check adler checksum over decompressed data
		if self._version < 3:
			assert(hex(adler32) == hex(zlib.adler32(decompressed_block) & 0xffffffff))

		return decompressed_block

	def _decode_key_block_info(self, key_block_info_compressed):
		if self._version >= 2:
			# zlib compression
			assert(key_block_info_compressed[:4] == b'\x02\x00\x00\x00')
			# decrypt if needed
			if self._encrypt & 0x02:
				key = ripemd128(key_block_info_compressed[4:8] + pack(b'<L', 0x3695))
				key_block_info_compressed = key_block_info_compressed[:8] + _fast_decrypt(key_block_info_compressed[8:], key)
			# decompress
			key_block_info = zlib.decompress(key_block_info_compressed[8:])
			# adler checksum
			adler32 = unpack('>I', key_block_info_compressed[4:8])[0]
			assert(adler32 == zlib.adler32(key_block_info) & 0xffffffff)
		else:
			# no compression
			key_block_info = key_block_info_compressed
		# decode
		key_block_info_list = []
		num_entries = 0
		i = 0
		if self._version >= 2:
			byte_format = '>H'
			byte_width = 2
			text_term = 1
		else:
			byte_format = '>B'
			byte_width = 1
			text_term = 0

		while i < len(key_block_info):
			# number of entries in current key block
			num_entries += unpack(self._number_format, key_block_info[i:i+self._number_width])[0]
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

		#assert(num_entries == self._num_entries)

		return key_block_info_list

	def _decode_key_block(self, key_block_compressed, key_block_info_list):
		key_list = []
		i = 0
		for compressed_size, decompressed_size in key_block_info_list:
			key_block = self._decode_block(key_block_compressed[i:i+compressed_size], decompressed_size)
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
				delimiter = b'\x00\x00'
				width = 2
			else:
				delimiter = b'\x00'
				width = 1
			i = key_start_index + self._number_width
			while i < len(key_block):
				if key_block[i:i+width] == delimiter:
					key_end_index = i
					break
				i += width
			key_text = key_block[key_start_index+self._number_width:key_end_index]\
				.decode(self._encoding, errors='ignore').encode('utf-8').strip()
			key_start_index = key_end_index + width
			key_list += [(key_id, key_text)]
		return key_list

	def _read_header(self):
		f = open(self._fname, 'rb')
		# number of bytes of header text
		header_bytes_size = unpack('>I', f.read(4))[0]
		header_bytes = f.read(header_bytes_size)
		# 4 bytes: adler32 checksum of header, in little endian
		adler32 = unpack('<I', f.read(4))[0]
		assert(adler32 == zlib.adler32(header_bytes) & 0xffffffff)
		# mark down key block offset
		self._key_block_offset = f.tell()
		f.close()

		# header text in utf-16 encoding ending with '\x00\x00'
		if header_bytes[-2:] == b'\x00\x00':
			header_text = header_bytes[:-2].decode('utf-16').encode('utf-8')
		else:
			header_text = header_bytes[:-1]
		header_tag = self._parse_header(header_text)

		if not self._encoding:
			encoding = header_tag.get(b'Encoding', b'utf-8')
			if sys.hexversion >= 0x03000000:
				encoding = encoding.decode('utf-8')
			# GB18030 > GBK > GB2312
			if encoding in ['GBK', 'GB2312']:
				encoding = 'GB18030'
			self._encoding = encoding

		# encryption flag
		#	0x00 - no encryption, "Allow export to text" is checked in MdxBuilder 3.
		#	0x01 - encrypt record block, "Encryption Key" is given in MdxBuilder 3.
		#	0x02 - encrypt key info block, "Allow export to text" is unchecked in MdxBuilder 3.
		if b'Encrypted' not in header_tag or header_tag[b'Encrypted'] == b'No':
			self._encrypt = 0
		elif header_tag[b'Encrypted'] == b'Yes':
			self._encrypt = 1
		else:
			self._encrypt = int(header_tag[b'Encrypted'])

		# stylesheet attribute if present takes form of:
		#	style_number # 1-255
		#	style_begin  # or ''
		#	style_end	 # or ''
		# store stylesheet in dict in the form of
		# {'number' : ('style_begin', 'style_end')}
		self._stylesheet = {}
		if header_tag.get('StyleSheet'):
			lines = header_tag['StyleSheet'].splitlines()
			for i in range(0, len(lines), 3):
				self._stylesheet[lines[i]] = (lines[i+1], lines[i+2])

		# before version 2.0, number is 4 bytes integer
		# version 2.0 and above uses 8 bytes
		self._version = float(header_tag[b'GeneratedByEngineVersion'])
		if self._version < 2.0:
			self._number_width = 4
			self._number_format = '>I'
		else:
			self._number_width = 8
			self._number_format = '>Q'
			# version 3.0 uses UTF-8 only
			if self._version >= 3:
				self._encoding = 'UTF-8'

		return header_tag

	def _read_keys(self):
		if self._version >= 3:
			return self._read_keys_v3()
		else:
			# if no regcode is given, try brutal force (only for engine <= 2)
			if (self._encrypt & 0x01) and self._encrypted_key is None:
				print("Try Brutal Force on Encrypted Key Blocks")
				return self._read_keys_brutal()
			else:
				return self._read_keys_v1v2()

	def _read_keys_v3(self):
		f = open(self._fname, 'rb')
		f.seek(self._key_block_offset)

		# find all blocks offset
		while True:
			block_type = self._read_int32(f)
			block_size = self._read_number(f)
			block_offset = f.tell()
			# record data
			if block_type == 0x01000000:
				self._record_block_offset = block_offset
			# record index
			elif block_type == 0x02000000:
				self._record_index_offset = block_offset
			# key data
			elif block_type == 0x03000000:
				self._key_data_offset = block_offset
			# key index
			elif block_type == 0x04000000:
				self._key_index_offset = block_offset
			else:
				raise RuntimeError("Unknown block type %d" % block_type)
			f.seek(block_size, 1)
			# test the end of file
			if f.read(4):
				f.seek(-4, 1)
			else:
				break

		# read key data
		f.seek(self._key_data_offset)
		number = self._read_int32(f)
		total_size = self._read_number(f)
		key_list = []
		for i in range(number):
			decompressed_size = self._read_int32(f)
			compressed_size = self._read_int32(f)
			block_data = f.read(compressed_size)
			decompressed_block_data = self._decode_block(block_data, decompressed_size)
			key_list.extend(self._split_key_block(decompressed_block_data))

		f.close()
		self._num_entries = len(key_list)
		return key_list

	def _read_keys_v1v2(self):
		f = open(self._fname, 'rb')
		f.seek(self._key_block_offset)

		# the following numbers could be encrypted
		if self._version >= 2.0:
			num_bytes = 8 * 5
		else:
			num_bytes = 4 * 4
		block = f.read(num_bytes)

		if self._encrypt & 1:
			block = _salsa_decrypt(block, self._encrypted_key)

		# decode this block
		sf = BytesIO(block)
		# number of key blocks
		num_key_blocks = self._read_number(sf)
		# number of entries
		self._num_entries = self._read_number(sf)
		# number of bytes of key block info after decompression
		if self._version >= 2.0:
			key_block_info_decomp_size = self._read_number(sf)
		# number of bytes of key block info
		key_block_info_size = self._read_number(sf)
		# number of bytes of key block
		key_block_size = self._read_number(sf)

		# 4 bytes: adler checksum of previous 5 numbers
		if self._version >= 2.0:
			adler32 = unpack('>I', f.read(4))[0]
			assert adler32 == (zlib.adler32(block) & 0xffffffff)

		# read key block info, which indicates key block's compressed and decompressed size
		key_block_info = f.read(key_block_info_size)
		key_block_info_list = self._decode_key_block_info(key_block_info)
		assert(num_key_blocks == len(key_block_info_list))

		# read key block
		key_block_compressed = f.read(key_block_size)
		# extract key block
		key_list = self._decode_key_block(key_block_compressed, key_block_info_list)

		self._record_block_offset = f.tell()
		f.close()

		return key_list

	def _read_keys_brutal(self):
		f = open(self._fname, 'rb')
		f.seek(self._key_block_offset)

		# the following numbers could be encrypted, disregard them!
		if self._version >= 2.0:
			num_bytes = 8 * 5 + 4
			key_block_type = b'\x02\x00\x00\x00'
		else:
			num_bytes = 4 * 4
			key_block_type = b'\x01\x00\x00\x00'
		block = f.read(num_bytes)

		# key block info
		# 4 bytes '\x02\x00\x00\x00'
		# 4 bytes adler32 checksum
		# unknown number of bytes follows until '\x02\x00\x00\x00' which marks the beginning of key block
		key_block_info = f.read(8)
		if self._version >= 2.0:
			assert key_block_info[:4] == b'\x02\x00\x00\x00'
		while True:
			fpos = f.tell()
			t = f.read(1024)
			index = t.find(key_block_type)
			if index != -1:
				key_block_info += t[:index]
				f.seek(fpos + index)
				break
			else:
				key_block_info += t

		key_block_info_list = self._decode_key_block_info(key_block_info)
		key_block_size = sum(list(zip(*key_block_info_list))[0])

		# read key block
		key_block_compressed = f.read(key_block_size)
		# extract key block
		key_list = self._decode_key_block(key_block_compressed, key_block_info_list)

		self._record_block_offset = f.tell()
		f.close()

		self._num_entries = len(key_list)
		return key_list

	def items(self):
		"""Return a generator which in turn produce tuples in the form of (filename, content)
		"""
		return self._read_records()

	def _read_records(self):
		if self._version >= 3:
			yield from self._read_records_v3()
		else:
			yield from self._read_records_v1v2()

	def _read_records_v3(self):
		f = open(self._fname, 'rb')
		f.seek(self._record_block_offset)

		offset = 0
		i = 0
		size_counter = 0

		num_record_blocks = self._read_int32(f)
		num_bytes = self._read_number(f)
		for j in range(num_record_blocks):
			decompressed_size = self._read_int32(f)
			compressed_size = self._read_int32(f)
			record_block = self._decode_block(f.read(compressed_size), decompressed_size)

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
				yield key_text, self._treat_record_data(data)
			offset += len(record_block)
			size_counter += compressed_size

	def _read_records_v1v2(self):
		f = open(self._fname, 'rb')
		f.seek(self._record_block_offset)

		num_record_blocks = self._read_number(f)
		num_entries = self._read_number(f)
		assert(num_entries == self._num_entries)
		record_block_info_size = self._read_number(f)
		record_block_size = self._read_number(f)

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
			try:
				record_block = self._decode_block(record_block_compressed, decompressed_size)
			except zlib.error:
				log.error("zlib decompress error")
				log.debug(f"record_block_compressed = {record_block_compressed!r}")
				continue
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
				yield key_text, self._treat_record_data(data)
			offset += len(record_block)
			size_counter += compressed_size
		#assert(size_counter == record_block_size)

		f.close()

	def _treat_record_data(self, data):
		return data


class MDD(MDict):
	"""
	MDict resource file format (*.MDD) reader.
	>>> mdd = MDD('example.mdd')
	>>> len(mdd)
	208
	>>> for filename,content in mdd.items():
	... print filename, content[:10]
	"""
	def __init__(self, fname, passcode=None):
		MDict.__init__(self, fname, encoding='UTF-16', passcode=passcode)


class MDX(MDict):
	"""
	MDict dictionary file format (*.MDD) reader.
	>>> mdx = MDX('example.mdx')
	>>> len(mdx)
	42481
	>>> for key,value in mdx.items():
	... print key, value[:10]
	"""
	def __init__(self, fname, encoding='', substyle=False, passcode=None):
		MDict.__init__(self, fname, encoding, passcode)
		self._substyle = substyle

	def _substitute_stylesheet(self, txt):
		# substitute stylesheet definition
		txt_list = re.split(r'`\d+`', txt)
		txt_tag = re.findall(r'`\d+`', txt)
		txt_styled = txt_list[0]
		for j, p in enumerate(txt_list[1:]):
			key = txt_tag[j][1:-1]
			try:
				style = self._stylesheet[key]
			except KeyError:
				log.error('invalid stylesheet key "%s"'%key)
				continue
			if p and p[-1] == '\n':
				txt_styled = txt_styled + style[0] + p.rstrip() + style[1] + '\r\n'
			else:
				txt_styled = txt_styled + style[0] + p + style[1]
		return txt_styled

	def _treat_record_data(self, data):
		# convert to utf-8
		data = data.decode(self._encoding, errors='ignore').strip(u'\x00').encode('utf-8')
		# substitute styles
		if self._substyle and self._stylesheet:
			data = self._substitute_stylesheet(data)
		return data


if __name__ == '__main__':
	import sys
	import os
	import os.path
	import argparse
	import codecs

	def passcode(s):
		try:
			regcode, userid = s.split(',')
		except:
			raise argparse.ArgumentTypeError("Passcode must be regcode,userid")
		try:
			regcode = codecs.decode(regcode, 'hex')
		except:
			raise argparse.ArgumentTypeError("regcode must be a 32 bytes hexadecimal string")
		return regcode, userid

	parser = argparse.ArgumentParser()
	parser.add_argument('-x', '--extract', action="store_true",
						help='extract mdx to source format and extract files from mdd')
	parser.add_argument('-s', '--substyle', action="store_true",
						help='substitute style definition if present')
	parser.add_argument('-d', '--datafolder', default="data",
						help='folder to extract data files from mdd')
	parser.add_argument('-e', '--encoding', default="",
						help='folder to extract data files from mdd')
	parser.add_argument('-p', '--passcode', default=None, type=passcode,
						help='register_code,email_or_deviceid')
	parser.add_argument("filename", nargs='?', help="mdx file name")
	args = parser.parse_args()

	# use GUI to select file, default to extract
	if not args.filename:
		if sys.hexversion >= 0x03000000:
			import tkinter as tk
			import tkinter.filedialog as filedialog
		else:
			import Tkinter as tk
			import tkFileDialog as filedialog

		root = tk.Tk()
		root.withdraw()
		args.filename = filedialog.askopenfilename(parent=root)
		args.extract = True

	if not os.path.exists(args.filename):
		print("Please specify a valid MDX/MDD file")

	base, ext = os.path.splitext(args.filename)

	# read mdx file
	if ext.lower() == os.path.extsep + 'mdx':
		mdx = MDX(args.filename, args.encoding, args.substyle, args.passcode)
		if type(args.filename) is unicode:
			bfname = args.filename.encode('utf-8')
		else:
			bfname = args.filename
		print('======== %s ========' % bfname)
		print('  Number of Entries : %d' % len(mdx))
		for key, value in mdx.header.items():
			print('  %s : %s' % (key, value))
	else:
		mdx = None

	# find companion mdd file
	mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
	if os.path.exists(mdd_filename):
		mdd = MDD(mdd_filename, args.passcode)
		if type(mdd_filename) is unicode:
			bfname = mdd_filename.encode('utf-8')
		else:
			bfname = mdd_filename
		print('======== %s ========' % bfname)
		print('  Number of Entries : %d' % len(mdd))
		for key, value in mdd.header.items():
			print('  %s : %s' % (key, value))
	else:
		mdd = None

	if args.extract:
		# write out glos
		if mdx:
			output_fname = ''.join([base, os.path.extsep, 'txt'])
			tf = open(output_fname, 'wb')
			for key, value in mdx.items():
				tf.write(key)
				tf.write(b'\r\n')
				tf.write(value)
				if not value.endswith(b'\n'):
					tf.write(b'\r\n')
				tf.write(b'</>\r\n')
			tf.close()
			# write out style
			if mdx.header.get('StyleSheet'):
				style_fname = ''.join([base, '_style', os.path.extsep, 'txt'])
				sf = open(style_fname, 'wb')
				sf.write(b'\r\n'.join(mdx.header['StyleSheet'].splitlines()))
				sf.close()
		# write out optional data files
		if mdd:
			datafolder = os.path.join(os.path.dirname(args.filename), args.datafolder)
			if not os.path.exists(datafolder):
				os.makedirs(datafolder)
			for key, value in mdd.items():
				fname = key.decode('utf-8').replace('\\', os.path.sep)
				dfname = datafolder + fname
				if not os.path.exists(os.path.dirname(dfname)):
					os.makedirs(os.path.dirname(dfname))
				df = open(dfname, 'wb')
				df.write(value)
				df.close()
