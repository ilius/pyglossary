# -*- coding: utf-8 -*-
"""
MDict Writer - Ported from mdict-utils for PyGlossary
Creates MDX (dictionary) and MDD (data) files in the MDict format.

Original code from: https://github.com/zhansliu/mdict-utils
Adapted for PyGlossary by removing external dependencies.
"""



import struct
import zlib
import operator
import sys
import datetime
import functools
import locale
import re
import string

from pyglossary.core import log

# Import cryptographic functions
try:
    from .ripemd128 import ripemd128
    from .pure_salsa20 import Salsa20
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False
    log.warning("Cryptographic functions not available - encryption disabled")

try:
    # Optional LZO compression support
    import lzo
    HAVE_LZO = True
except ImportError:
    HAVE_LZO = False

# HTML escaping for headers
from html import escape



class ParameterError(Exception):
    """Raised when some parameter to MdxWriter is invalid or uninterpretable."""
    pass


def _mdx_compress(data, compression_type=2):
	"""Compress data using the specified MDX compression type."""
	# Handle LZO fallback - if LZO requested but not available, use zlib
	actual_compression_type = compression_type
	if compression_type == 1 and not HAVE_LZO:  # LZO requested but not available
		actual_compression_type = 2  # Fall back to zlib
		log.warning("LZO compression requested but not available, falling back to zlib")

	header = struct.pack(b"<L", actual_compression_type) + \
	         struct.pack(b">L", zlib.adler32(data) & 0xffffffff)

	if actual_compression_type == 0:  # no compression
		return header + data
	elif actual_compression_type == 2:  # zlib
		return header + zlib.compress(data, level=6)  # balanced compression ratio (0=no, 9=max compression)
	elif actual_compression_type == 1:  # lzo (should not reach here due to fallback above)
		if HAVE_LZO:
			return header + lzo.compress(data)[5:]  # python-lzo adds a 5-byte header
		else:
			# This should not happen due to fallback above, but just in case
			return header + zlib.compress(data, level=6)
	else:
		raise ParameterError("Unknown compression type")


def _fast_encrypt(data, key):
    """Fast encryption algorithm used in MDX."""
    b = bytearray(data)
    key = bytearray(key)
    previous = 0x36
    for i in range(len(b)):
        t = b[i] ^ previous ^ (i & 0xff) ^ key[i % len(key)]
        previous = b[i] = ((t >> 4) | (t << 4)) & 0xff
    return bytes(b)


def _mdx_encrypt(comp_block):
    """Encrypt compressed MDX block."""
    if not HAVE_CRYPTO:
        return comp_block
    key = ripemd128(comp_block[4:8] + struct.pack(b"<L", 0x3695))
    return comp_block[0:8] + _fast_encrypt(comp_block[8:], key)


def _salsa_encrypt(plaintext, dict_key):
    """Salsa20 encryption for MDX headers."""
    if not HAVE_CRYPTO:
        return plaintext
    assert isinstance(dict_key, bytes)
    assert isinstance(plaintext, bytes)
    encrypt_key = ripemd128(dict_key)
    s20 = Salsa20(key=encrypt_key, IV=b"\x00" * 8, rounds=8)
    return s20.encryptBytes(plaintext)


def _hexdump(bytes_blob):
    """Returns a hexadecimal representation of bytes_blob."""
    return "".join("{:02X}".format(c) for c in bytes_blob)


def encrypt_key(dict_key, **kwargs):
    """
    Generates a hexadecimal key for use with the official MDict program.
    """
    if not HAVE_CRYPTO:
        raise NotImplementedError("Cryptographic functions not available")

    if (("email" not in kwargs and "device_id" not in kwargs) or
        ("email" in kwargs and "device_id" in kwargs)):
        raise ParameterError("Expected exactly one of email and device_id as keyword argument")

    if "email" in kwargs:
        owner_info_digest = ripemd128(kwargs["email"].encode("ascii"))
    else:
        owner_info_digest = ripemd128(kwargs["device_id"].encode("ascii"))

    dict_key_digest = ripemd128(dict_key)

    s20 = Salsa20(key=owner_info_digest, IV=b"\x00" * 8, rounds=8)
    output_key = s20.encryptBytes(dict_key_digest)
    return _hexdump(output_key)


class _OffsetTableEntry:
    """Represents one key/record pair in the MDX format."""
    def __init__(self, key, key_null, key_len, offset, record_null, record_size=None, record_pos=None, encoding=None, is_mdd=None):
        self.key = key
        self.key_null = key_null
        self.key_len = key_len
        self.offset = offset
        self.record_null = record_null
        # Extended fields for compatibility
        self.record_size = record_size
        self.record_pos = record_pos
        self.encoding = encoding
        self.is_mdd = is_mdd

    def get_record_null(self):
        """Get the record data, handling different input formats."""
        if hasattr(self, 'record_pos') and self.record_pos is not None and self.record_pos > 0:
            # Extended format - need to read from file
            with open(self.record_null, 'rb') as f:
                f.seek(self.record_pos)
                return f.read(self.record_size - 1) + b'\0'
        else:
            # Simple format - record_null is already the data (string)
            if isinstance(self.record_null, str):
                # Convert string to bytes with null terminator
                return (self.record_null + '\0').encode(self.encoding or 'utf-8')
            else:
                # Already bytes
                return self.record_null


class MDictWriter:
    """Writer for MDX (dictionary) and MDD (data) files with proper MDict sorting."""

    def __init__(self, d, title, description,
                 key_size=32768, record_size=65536,
                 encrypt_index=False,
                 encoding="utf8",
                 compression_type=2,
                 version="2.0",
                 encrypt_key=None,
                 register_by=None,
                 user_email=None,
                 user_device_id=None,
                 is_mdd=False,
                 compact="No",
                 compat="No"):
        """
        Prepares the records for MDX/MDD file creation.

        d: dictionary mapping keys to values (strings for MDX, bytes for MDD)
        title: dictionary title
        description: dictionary description
        key_size: key block size in KB (used for key blocks)
        record_size: record block size in KB (used for record blocks and as base block_size)
        encoding: text encoding ("utf8", "utf16", "gbk", "big5")
        compression_type: 0=none, 1=lzo, 2=zlib
        version: format version ("2.0" or "1.2")
        is_mdd: True for MDD files, False for MDX files
        """
        self._key_block_size = key_size
        self._record_block_size = record_size
        self._num_entries = len(d)
        self._title = title
        self._description = description
        self._encrypt_index = encrypt_index
        self._encrypt = (encrypt_key is not None)
        self._encrypt_key = encrypt_key
        if register_by not in ["email", "device_id", None]:
            raise ParameterError("Unknown register_by type")
        self._register_by = register_by
        self._user_email = user_email
        self._user_device_id = user_device_id
        self._compression_type = compression_type
        self._is_mdd = is_mdd
        self._compact = compact
        self._compat = compat

        # Set up encoding parameters
        if not is_mdd:
            encoding = encoding.lower()
            if encoding in ["utf8", "utf-8"]:
                self._python_encoding = "utf_8"
                self._encoding = "UTF-8"
                self._encoding_length = 1
            elif encoding in ["utf16", "utf-16"]:
                self._python_encoding = "utf_16_le"
                self._encoding = "UTF-16"
                self._encoding_length = 2
            elif encoding == "gbk":
                self._python_encoding = "gbk"
                self._encoding = "GBK"
                self._encoding_length = 1
            elif encoding == "big5":
                self._python_encoding = "big5"
                self._encoding = "BIG5"
                self._encoding_length = 1
            else:
                raise ParameterError("Unknown encoding")
        else:
            self._python_encoding = "utf_16_le"
            self._encoding_length = 2

        if version not in ["2.0", "1.2"]:
            raise ParameterError("Unknown version")
        self._version = version

        # Check input format: dict, list of tuples, list of dicts, or other
        if isinstance(d, list) and d and isinstance(d[0], tuple) and len(d[0]) == 2:
            # List of tuples format: [(key, value), ...] - used for MDX text with potential duplicates
            self._input_is_simple = True
            extended_d = []
            for key, value in d:
                # For simple format, we store the data directly
                extended_d.append({
                    'key': key,
                    'path': value,  # Store value directly
                    'pos': 0,       # Not used for simple format
                    'size': len((value + '\0').encode(self._python_encoding))
                })
            self._build_offset_table(extended_d)
        elif isinstance(d, list):
            # Extended format (list of dicts) - used for MDD data
            self._input_is_simple = False
            self._build_offset_table(d)
        elif d and isinstance(next(iter(d.values())), str):
            # Simple format dict[str, str] - used for MDX text
            self._input_is_simple = True
            extended_d = []
            for key, value in d.items():
                # For simple format, we store the data directly
                extended_d.append({
                    'key': key,
                    'path': value,  # Store value directly
                    'pos': 0,       # Not used for simple format
                    'size': len((value + '\0').encode(self._python_encoding))
                })
            self._build_offset_table(extended_d)
        else:
            # Other dict format or empty
            self._input_is_simple = False
            self._build_offset_table(d)

        # Set block size for key blocks and build them
        self._block_size = self._key_block_size
        self._build_key_blocks()
        self._build_keyb_index()

        # Set block size for record blocks and build them
        self._block_size = self._record_block_size
        self._build_record_blocks()
        self._build_recordb_index()

    def _build_offset_table(self, items):
        """One key own multi entry, so d is list"""
        def mdict_cmp(item1, item2):
            # sort following mdict standard
            key1 = item1['key'].lower()
            key2 = item2['key'].lower()
            if not self._is_mdd:
                key1 = regex_strip.sub('', key1)
                key2 = regex_strip.sub('', key2)
            # locale key
            key1 = locale.strxfrm(key1)
            key2 = locale.strxfrm(key2)
            if key1 > key2:
                return 1
            elif key1 < key2:
                return -1
            # reverse
            if len(key1) > len(key2):
                return -1
            elif len(key1) < len(key2):
                return 1
            key1 = key1.rstrip(string.punctuation)
            key2 = key2.rstrip(string.punctuation)
            if key1 > key2:
                return -1
            elif key1 < key2:
                return 1

            # https://github.com/digitalpalidictionary/dpd-db: link to link bug prevention (08.03.2023)
            # When keys are identical, handle @@@LINK= entries specially
            if not self._is_mdd:  # Only for MDX files, not MDD
                value1 = item1['path'].lower() if isinstance(item1['path'], str) else ""
                value2 = item2['path'].lower() if isinstance(item2['path'], str) else ""

                # If both are @@@LINK= entries, maintain stable order
                if value1.startswith("@@@link=") and value2.startswith("@@@link="):
                    return 0  # Don't change order to prevent link loops

                # If one is a link but the other isn't, put links at lower positions
                if value1.startswith("@@@link="):
                    return 1   # value1 (link) goes after value2 (definition)
                if value2.startswith("@@@link="):
                    return -1  # value2 (link) goes after value1 (definition)

            return 0

        pattern = '[%s ]+' % string.punctuation
        regex_strip = re.compile(pattern)

        items.sort(key=functools.cmp_to_key(mdict_cmp))

        self._offset_table = []
        offset = 0
        for record in items:
            key = record['key']
            key_enc = key.encode(self._python_encoding)
            key_null = (key + "\0").encode(self._python_encoding)
            key_len = len(key_enc) // self._encoding_length

            self._offset_table.append(_OffsetTableEntry(
                key=key_enc,
                key_null=key_null,
                key_len=key_len,
                record_null=record['path'],
                record_size=record['size'],
                record_pos=record['pos'],
                offset=offset,
                encoding=self._python_encoding,
                is_mdd=self._is_mdd,
            ))
            offset += record['size']
        self._total_record_len = offset

    def _build_key_blocks(self):
        """Build compressed key blocks."""
        self._block_size = self._key_block_size
        self._key_blocks = self._split_blocks(_MdxKeyBlock)

    def _build_record_blocks(self):
        """Build compressed record blocks."""
        self._block_size = self._record_block_size
        self._record_blocks = self._split_blocks(_MdxRecordBlock)

    def _build_recordb_index(self):
        pass

    def _write_record_sect(self, outfile, callback=None):
        # outfile: a file-like object, opened in binary mode.
        if self._version == "2.0":
            record_format = b">QQQQ"
            index_format = b">QQ"
        else:
            record_format = b">LLLL"
            index_format = b">LL"
        # fill ZERO
        record_pos = outfile.tell()
        outfile.write(struct.pack(record_format, 0, 0, 0, 0))
        outfile.write((struct.pack(index_format, 0, 0)) * len(self._record_blocks))

        recordblocks_total_size = 0
        recordb_index = []
        for b in self._record_blocks:
            b.prepare()
            recordblocks_total_size += len(b.get_block())
            recordb_index.append(b.get_index_entry())
            outfile.write(b.get_block())
            callback and callback(len(b._offset_table))
            b.clean()
        end_pos = outfile.tell()
        self._recordb_index = b''.join(recordb_index)
        self._recordb_index_size = len(self._recordb_index)
        # fill REAL value
        outfile.seek(record_pos)
        outfile.write(struct.pack(record_format,
                                  len(self._record_blocks),
                                  self._num_entries,
                                  self._recordb_index_size,
                                  recordblocks_total_size))
        outfile.write(self._recordb_index)
        outfile.seek(end_pos)

    def write(self, outfile, callback=None):
        self._write_header(outfile)
        self._write_key_sect(outfile)
        self._write_record_sect(outfile, callback=callback)

    def _write_header(self, f):
        # disable encrypt
        encrypted = "No"
        register_by_str = ""
        # regcode = ""

        if not self._is_mdd:
            header_string = (
                """<Dictionary """
                """GeneratedByEngineVersion="{version}" """
                """RequiredEngineVersion="{version}" """
                """Encrypted="{encrypted}" """
                """Encoding="{encoding}" """
                """Format="Html" """
                """Stripkey="Yes" """
                """CreationDate="{date.year}-{date.month}-{date.day}" """
                """Compact="Yes" """
                """Compat="Yes" """
                """KeyCaseSensitive="No" """
                """Description="{description}" """
                """Title="{title}" """
                """DataSourceFormat="106" """
                """StyleSheet="" """
                """Left2Right="Yes" """
                """RegisterBy="{register_by_str}" """
                # """RegCode="{regcode}" """
                """/>\r\n\x00"""
            ).format(
                version=self._version,
                encrypted=encrypted,
                encoding=self._encoding,
                date=datetime.date.today(),
                description=escape(self._description, quote=True),
                title=escape(self._title, quote=True),
                register_by_str=register_by_str,
                # regcode=regcode,
            ).encode("utf_16_le")
        else:
            header_string = (
                """<Library_Data """
                """GeneratedByEngineVersion="{version}" """
                """RequiredEngineVersion="{version}" """
                """Encrypted="{encrypted}" """
                """Encoding="" """
                """Format="" """
                """CreationDate="{date.year}-{date.month}-{date.day}" """
                # """Compact="No" """
                # """Compat="No" """
                """KeyCaseSensitive="No" """
                """Stripkey="No" """
                """Description="{description}" """
                """Title="{title}" """
                # """DataSourceFormat="106" """
                # """StyleSheet="" """
                """RegisterBy="{register_by_str}" """
                # """RegCode="{regcode}" """
                """/>\r\n\x00"""
            ).format(
                version=self._version,
                encrypted=encrypted,
                date=datetime.date.today(),
                description=escape(self._description, quote=True),
                title=escape(self._title, quote=True),
                register_by_str=register_by_str,
                # regcode=regcode
            ).encode("utf_16_le")
        f.write(struct.pack(b">L", len(header_string)))
        f.write(header_string)
        f.write(struct.pack(b"<L", zlib.adler32(header_string) & 0xffffffff))

    def _split_blocks(self, block_type):
        """Split entries into compressed blocks."""
        this_block_start = 0
        cur_size = 0
        blocks = []
        for ind in range(len(self._offset_table) + 1):
            if ind != len(self._offset_table):
                t = self._offset_table[ind]
            else:
                t = None

            if ind == 0:
                flush = False  # nothing to flush yet
            elif ind == len(self._offset_table):
                flush = True  # always flush the last block
            elif cur_size + block_type._len_block_entry(t) > self._block_size:
                flush = True  # block would be too large
            else:
                flush = False

            if flush:
                blocks.append(block_type(
                    self._offset_table[this_block_start:ind],
                    self._compression_type,
                    self._version))
                cur_size = 0
                this_block_start = ind

            if t is not None:
                cur_size += block_type._len_block_entry(t)
        return blocks

    def _build_key_blocks(self):
        """Build compressed key blocks."""
        self._key_blocks = self._split_blocks(_MdxKeyBlock)

    def _build_record_blocks(self):
        """Build compressed record blocks."""
        self._record_blocks = self._split_blocks(_MdxRecordBlock)

    def _build_keyb_index(self):
        """Build the key block index."""
        decomp_data = b"".join(b.get_index_entry() for b in self._key_blocks)
        self._keyb_index_decomp_size = len(decomp_data)
        if self._version == "2.0":
            self._keyb_index = _mdx_compress(decomp_data, self._compression_type)
            if self._encrypt_index:
                self._keyb_index = _mdx_encrypt(self._keyb_index)
            self._keyb_index_comp_size = len(self._keyb_index)
        elif self._encrypt_index:
            raise ParameterError("Key index encryption not supported in version 1.2")
        else:
            self._keyb_index = decomp_data

    def _build_recordb_index(self):
        """Build the record block index."""
        self._recordb_index = b"".join(
            b.get_index_entry() for b in self._record_blocks)
        self._recordb_index_size = len(self._recordb_index)

    def _write_key_sect(self, outfile):
        """Write the key section to file."""
        keyblocks_total_size = sum(len(b.get_block()) for b in self._key_blocks)
        if self._version == "2.0":
            preamble = struct.pack(b">QQQQQ",
                len(self._key_blocks),
                self._num_entries,
                self._keyb_index_decomp_size,
                self._keyb_index_comp_size,
                keyblocks_total_size)
            preamble_checksum = struct.pack(b">L", zlib.adler32(preamble))
            if self._encrypt:
                preamble = _salsa_encrypt(preamble, self._encrypt_key)
            outfile.write(preamble)
            outfile.write(preamble_checksum)
        else:
            preamble = struct.pack(b">LLLL",
                len(self._key_blocks),
                self._num_entries,
                self._keyb_index_decomp_size,
                keyblocks_total_size)
            if self._encrypt:
                preamble = _salsa_encrypt(preamble, self._encrypt_key)
            outfile.write(preamble)

        outfile.write(self._keyb_index)
        for b in self._key_blocks:
            outfile.write(b.get_block())

    def _write_record_sect(self, outfile):
        """Write the record section to file."""
        recordblocks_total_size = sum(len(b.get_block()) for b in self._record_blocks)
        if self._version == "2.0":
            format_str = b">QQQQ"
        else:
            format_str = b">LLLL"
        outfile.write(struct.pack(format_str,
            len(self._record_blocks),
            self._num_entries,
            self._recordb_index_size,
            recordblocks_total_size))
        outfile.write(self._recordb_index)
        for b in self._record_blocks:
            outfile.write(b.get_block())

    def write(self, outfile):
        """Write the complete MDX/MDD file."""
        self._write_header(outfile)
        self._write_key_sect(outfile)
        self._write_record_sect(outfile)

    def _write_header(self, f):
        """Write the XML header."""
        encrypted = 0
        if self._encrypt_index:
            encrypted = encrypted | 2
        if self._encrypt:
            encrypted = encrypted | 1

        if self._encrypt and self._register_by == "email":
            register_by_str = "EMail"
            if self._user_email is not None:
                regcode = encrypt_key(self._encrypt_key, email=self._user_email)
            else:
                regcode = ""
        elif self._encrypt and self._register_by == "device_id":
            register_by_str = "DeviceID"
            if self._user_device_id is not None:
                regcode = encrypt_key(self._encrypt_key, device_id=self._user_device_id)
            else:
                regcode = ""
        else:
            register_by_str = ""
            regcode = ""

        if not self._is_mdd:
            header_string = (
                '<Dictionary '
                'GeneratedByEngineVersion="{version}" '
                'RequiredEngineVersion="{version}" '
                'Encrypted="{encrypted}" '
                'Encoding="{encoding}" '
                'Format="Html" '
                'CreationDate="{date.year}-{date.month}-{date.day}" '
                'Compact="{compact}" '
                'Compat="{compat}" '
                'KeyCaseSensitive="No" '
                'Description="{description}" '
                'Title="{title}" '
                'DataSourceFormat="106" '
                'StyleSheet="" '
                'RegisterBy="{register_by_str}" '
                'RegCode="{regcode}"/>\r\n\x00'
            ).format(
                version=self._version,
                encrypted=encrypted,
                encoding=self._encoding,
                date=datetime.date.today(),
                compact=self._compact,
                compat=self._compat,
                description=escape(self._description, quote=True),
                title=escape(self._title, quote=True),
                register_by_str=register_by_str,
                regcode=regcode
            ).encode("utf_16_le")
        else:
            header_string = (
                '<Library_Data '
                'GeneratedByEngineVersion="{version}" '
                'RequiredEngineVersion="{version}" '
                'Encrypted="{encrypted}" '
                'Format="" '
                'CreationDate="{date.year}-{date.month}-{date.day}" '
                'Compact="No" '
                'Compat="No" '
                'KeyCaseSensitive="No" '
                'Description="{description}" '
                'Title="{title}" '
                'DataSourceFormat="106" '
                'StyleSheet="" '
                'RegisterBy="{register_by_str}" '
                'RegCode="{regcode}"/>\r\n\x00'
            ).format(
                version=self._version,
                encrypted=encrypted,
                date=datetime.date.today(),
                description=escape(self._description, quote=True),
                title=escape(self._title, quote=True),
                register_by_str=register_by_str,
                regcode=regcode
            ).encode("utf_16_le")

        f.write(struct.pack(b">L", len(header_string)))
        f.write(header_string)
        f.write(struct.pack(b"<L", zlib.adler32(header_string) & 0xffffffff))


class _MdxBlock:
    """Abstract base class for MDX blocks."""

    def __init__(self, offset_table, compression_type, version):
        """Build compressed block data."""
        decomp_data = b"".join(
            type(self)._block_entry(t, version)
            for t in offset_table)
        self._decomp_size = len(decomp_data)
        self._comp_data = _mdx_compress(decomp_data, compression_type)
        self._comp_size = len(self._comp_data)
        self._version = version

    def get_block(self):
        """Return the compressed block data."""
        return self._comp_data

    def get_index_entry(self):
        """Return the index entry for this block."""
        raise NotImplementedError()

    @staticmethod
    def _block_entry(t, version):
        """Return data for a single entry."""
        raise NotImplementedError()

    @staticmethod
    def _len_block_entry(t):
        """Return approximate size of an entry."""
        raise NotImplementedError()


class _MdxRecordBlock(_MdxBlock):
    """Represents a record block."""

    def __init__(self, offset_table, compression_type, version):
        """Initialize record block."""
        _MdxBlock.__init__(self, offset_table, compression_type, version)

    def prepare(self):
        """Prepare block for writing (no-op for now)."""
        pass

    def clean(self):
        """Clean up after writing."""
        if hasattr(self, '_comp_data'):
            self._comp_data = None

    def get_index_entry(self):
        """Return record block index entry."""
        if self._version == "2.0":
            format_str = b">QQ"
        else:
            format_str = b">LL"
        return struct.pack(format_str, self._comp_size, self._decomp_size)

    @staticmethod
    def _block_entry(t, version):
        """Return record data for entry."""
        return t.get_record_null()

    @staticmethod
    def _len_block_entry(t):
        """Return record size."""
        return t.record_size if hasattr(t, 'record_size') and t.record_size else len(t.get_record_null())


class _MdxKeyBlock(_MdxBlock):
    """Represents a key block."""

    def __init__(self, offset_table, compression_type, version):
        """Initialize key block."""
        _MdxBlock.__init__(self, offset_table, compression_type, version)
        self._num_entries = len(offset_table)
        if version == "2.0":
            self._first_key = offset_table[0].key_null
            self._last_key = offset_table[-1].key_null
        else:
            self._first_key = offset_table[0].key
            self._last_key = offset_table[-1].key
        self._first_key_len = offset_table[0].key_len
        self._last_key_len = offset_table[-1].key_len

    @staticmethod
    def _block_entry(t, version):
        """Return key data for entry."""
        if version == "2.0":
            format_str = b">Q"
        else:
            format_str = b">L"
        return struct.pack(format_str, t.offset) + t.key_null

    @staticmethod
    def _len_block_entry(t):
        """Return approximate key entry size."""
        return 8 + len(t.key_null)  # Approximate for version 2.0

    def get_index_entry(self):
        """Return key block index entry."""
        if self._version == "2.0":
            long_format = b">Q"
            short_format = b">H"
        else:
            long_format = b">L"
            short_format = b">B"
        return (
            struct.pack(long_format, self._num_entries)
            + struct.pack(short_format, self._first_key_len)
            + self._first_key
            + struct.pack(short_format, self._last_key_len)
            + self._last_key
            + struct.pack(long_format, self._comp_size)
            + struct.pack(long_format, self._decomp_size)
        )
