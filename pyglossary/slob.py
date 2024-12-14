# slob.py
# Copyright (C) 2020-2023 Saeed Rasooli
# Copyright (C) 2019 Igor Tkach <itkach@gmail.com>
# 	as part of https://github.com/itkach/slob
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
from __future__ import annotations

import encodings
import io
import operator
import os
import pickle
import sys
import tempfile
import typing
import warnings
from abc import abstractmethod
from bisect import bisect_left
from builtins import open as fopen
from datetime import datetime, timezone
from functools import cache, lru_cache
from io import BufferedIOBase, IOBase
from os.path import isdir
from struct import calcsize, pack, unpack
from threading import RLock
from types import MappingProxyType, TracebackType
from typing import (
	TYPE_CHECKING,
	Any,
	Generic,
	NamedTuple,
	TypeVar,
	cast,
)
from uuid import UUID, uuid4

import icu  # type: ignore
from icu import Collator, Locale, UCollAttribute, UCollAttributeValue

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator, Mapping, Sequence

	from .icu_types import T_Collator

__all__ = [
	"MAX_TEXT_LEN",
	"MAX_TINY_TEXT_LEN",
	"MIME_HTML",
	"MIME_TEXT",
	"MultiFileReader",
	"UnknownEncoding",
	"Writer",
	"encodings",
	"fopen",
	"open",
	"read_byte_string",
	"read_header",
	"sortkey",
]

DEFAULT_COMPRESSION = "lzma2"

UTF8 = "utf-8"
MAGIC = b"!-1SLOB\x1f"


class Compression(NamedTuple):
	compress: Callable[..., bytes]  # first arg: bytes
	decompress: Callable[[bytes], bytes]


class Ref(NamedTuple):
	key: str
	bin_index: int
	item_index: int
	fragment: str


class Header(NamedTuple):
	magic: bytes
	uuid: UUID
	encoding: str
	compression: str
	tags: MappingProxyType[str, str]
	content_types: Sequence[str]
	blob_count: int
	store_offset: int
	refs_offset: int
	size: int


U_CHAR = ">B"
U_CHAR_SIZE = calcsize(U_CHAR)
U_SHORT = ">H"
U_SHORT_SIZE = calcsize(U_SHORT)
U_INT = ">I"
U_INT_SIZE = calcsize(U_INT)
U_LONG_LONG = ">Q"
U_LONG_LONG_SIZE = calcsize(U_LONG_LONG)


def calcmax(len_size_spec: str) -> int:
	return 2 ** (calcsize(len_size_spec) * 8) - 1


MAX_TEXT_LEN = calcmax(U_SHORT)
MAX_TINY_TEXT_LEN = calcmax(U_CHAR)
MAX_LARGE_BYTE_STRING_LEN = calcmax(U_INT)
MAX_BIN_ITEM_COUNT = calcmax(U_SHORT)


PRIMARY: int = Collator.PRIMARY
SECONDARY: int = Collator.SECONDARY
TERTIARY: int = Collator.TERTIARY
QUATERNARY: int = Collator.QUATERNARY
IDENTICAL: int = Collator.IDENTICAL


class CompressionModule(typing.Protocol):
	# gzip.compress(data, compresslevel=9, *, mtime=None)
	# bz2.compress(data, compresslevel=9)
	# zlib.compress(data, /, level=-1, wbits=15)
	# lzma.compress(data, format=1, check=-1, preset=None, filters=None)
	@staticmethod
	def compress(data: bytes, compresslevel: int = 9) -> bytes:
		raise NotImplementedError

	# gzip.decompress(data)
	# bz2.decompress(data)
	# zlib.decompress(data, /, wbits=15, bufsize=16384)
	# lzma.decompress(data, format=0, memlimit=None, filters=None)
	@staticmethod
	def decompress(
		data: bytes,
		**kwargs: Mapping[str, Any],
	) -> bytes:
		raise NotImplementedError


def init_compressions() -> dict[str, Compression]:
	def ident(x: bytes) -> bytes:
		return x

	compressions: dict[str, Compression] = {
		"": Compression(ident, ident),
	}
	for name in ("bz2", "zlib"):
		m: CompressionModule
		try:
			m = cast("CompressionModule", __import__(name))
		except ImportError:
			warnings.showwarning(
				message=f"{name} is not available",
				category=ImportWarning,
				filename=__file__,
				lineno=0,
			)
			continue

		def compress_new(x: bytes, m: CompressionModule = m) -> bytes:
			return m.compress(x, 9)

		compressions[name] = Compression(compress_new, m.decompress)

	try:
		import lzma
	except ImportError:
		warnings.warn("lzma is not available", stacklevel=1)
	else:
		filters = [{"id": lzma.FILTER_LZMA2}]
		compressions["lzma2"] = Compression(
			lambda s: lzma.compress(
				s,
				format=lzma.FORMAT_RAW,
				filters=filters,
			),
			lambda s: lzma.decompress(
				s,
				format=lzma.FORMAT_RAW,
				filters=filters,
			),
		)
	return compressions


COMPRESSIONS = init_compressions()


del init_compressions


MIME_TEXT = "text/plain"
MIME_HTML = "text/html"


class FileFormatException(Exception):
	pass


class UnknownFileFormat(FileFormatException):
	pass


class UnknownCompression(FileFormatException):
	pass


class UnknownEncoding(FileFormatException):
	pass


class IncorrectFileSize(FileFormatException):
	pass


@cache
def sortkey(
	strength: int,
	maxlength: int | None = None,
) -> Callable:
	# pass empty locale to use root locale
	# if you pass no arg, it will use system locale
	c: T_Collator = Collator.createInstance(Locale(""))
	c.setStrength(strength)
	c.setAttribute(
		UCollAttribute.ALTERNATE_HANDLING,
		UCollAttributeValue.SHIFTED,
	)
	if maxlength is None:
		return c.getSortKey
	return lambda x: c.getSortKey(x)[:maxlength]


class MultiFileReader(BufferedIOBase):
	def __init__(
		self,
		*args: str,
	) -> None:
		filenames: list[str] = list(args)
		files = []
		ranges = []
		offset = 0
		for name in filenames:
			size = os.stat(name).st_size
			ranges.append(range(offset, offset + size))
			files.append(fopen(name, "rb"))
			offset += size
		self.size = offset
		self._ranges = ranges
		self._files = files
		self._fcount = len(self._files)
		self._offset = -1
		self.seek(0)

	def __enter__(self) -> MultiFileReader:
		return self

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_val: BaseException | None,
		exc_tb: TracebackType | None,
	) -> None:
		self.close()

	def close(self) -> None:
		for f in self._files:
			f.close()
		self._files.clear()
		self._ranges.clear()

	@property
	def closed(self) -> bool:
		return len(self._ranges) == 0

	def isatty(self) -> bool:  # noqa: PLR6301
		return False

	def readable(self) -> bool:  # noqa: PLR6301
		return True

	def seek(
		self,
		offset: int,
		whence: int = io.SEEK_SET,
	) -> int:
		if whence == io.SEEK_SET:
			self._offset = offset
		elif whence == io.SEEK_CUR:
			self._offset += offset
		elif whence == io.SEEK_END:
			self._offset = self.size + offset
		else:
			raise ValueError(f"Invalid value for parameter whence: {whence!r}")
		return self._offset

	def seekable(self) -> bool:  # noqa: PLR6301
		return True

	def tell(self) -> int:
		return self._offset

	def writable(self) -> bool:  # noqa: PLR6301
		return False

	def read(self, n: int | None = -1) -> bytes:
		file_index = -1
		actual_offset = 0
		for i, r in enumerate(self._ranges):
			if self._offset in r:
				file_index = i
				actual_offset = self._offset - r.start
				break
		result = b""
		to_read = self.size if n == -1 or n is None else n
		while -1 < file_index < self._fcount:
			f = self._files[file_index]
			f.seek(actual_offset)
			read = f.read(to_read)
			read_count = len(read)
			self._offset += read_count
			result += read
			to_read -= read_count
			if to_read > 0:
				file_index += 1
				actual_offset = 0
			else:
				break
		return result


class KeydItemDict:
	def __init__(
		self,
		blobs: Sequence[Blob | Ref],
		strength: int,
		maxlength: int | None = None,
	) -> None:
		self.blobs = blobs
		self.sortkey = sortkey(strength, maxlength=maxlength)

	def __len__(self) -> int:
		return len(self.blobs)

	# https://docs.python.org/3/library/bisect.html
	# key= parameter to bisect_left is added in Python 3.10
	def __getitem__(self, key: str) -> Iterator[Blob | Ref]:
		blobs = self.blobs
		key_as_sk = self.sortkey(key)
		i = bisect_left(
			blobs,
			key_as_sk,
			key=lambda blob: self.sortkey(blob.key),
		)
		if i == len(blobs):
			return
		while i < len(blobs):
			if self.sortkey(blobs[i].key) == key_as_sk:
				yield blobs[i]
			else:
				break
			i += 1

	def __contains__(self, key: str) -> bool:
		try:
			next(self[key])
		except StopIteration:
			return False
		return True


class Blob:
	def __init__(  # noqa: PLR0913
		self,
		content_id: int,
		key: str,
		fragment: str,
		read_content_type_func: Callable[[], str],
		read_func: Callable,
	) -> None:
		# print(f"read_func is {type(read_func)}")
		# read_func is <class 'functools._lru_cache_wrapper'>
		self._content_id = content_id
		self._key = key
		self._fragment = fragment
		self._read_content_type = read_content_type_func
		self._read = read_func

	@property
	def identity(self) -> int:
		return self._content_id

	@property
	def key(self) -> str:
		return self._key

	@property
	def fragment(self) -> str:
		return self._fragment

	@property
	def content_type(self) -> str:
		return self._read_content_type()

	@property
	def content(self) -> bytes:
		return self._read()

	def __str__(self) -> str:
		return self.key

	def __repr__(self) -> str:
		return f"<{self.__class__.__module__}.{self.__class__.__name__} {self.key}>"


def read_byte_string(f: IOBase, len_spec: str) -> bytes:
	length = unpack(len_spec, f.read(calcsize(len_spec)))[0]
	return f.read(length)


class StructReader:
	def __init__(
		self,
		file: IOBase,
		encoding: str | None = None,
	) -> None:
		self._file = file
		self.encoding = encoding

	def read_int(self) -> int:
		s = self.read(U_INT_SIZE)
		return unpack(U_INT, s)[0]

	def read_long(self) -> int:
		b = self.read(U_LONG_LONG_SIZE)
		return unpack(U_LONG_LONG, b)[0]

	def read_byte(self) -> int:
		s = self.read(U_CHAR_SIZE)
		return unpack(U_CHAR, s)[0]

	def read_short(self) -> int:
		return unpack(U_SHORT, self._file.read(U_SHORT_SIZE))[0]

	def _read_text(self, len_spec: str) -> str:
		if self.encoding is None:
			raise ValueError("self.encoding is None")
		max_len = 2 ** (8 * calcsize(len_spec)) - 1
		byte_string = read_byte_string(self._file, len_spec)
		if len(byte_string) == max_len:
			terminator = byte_string.find(0)
			if terminator > -1:
				byte_string = byte_string[:terminator]
		return byte_string.decode(self.encoding)

	def read_tiny_text(self) -> str:
		return self._read_text(U_CHAR)

	def read_text(self) -> str:
		return self._read_text(U_SHORT)

	def read(self, n: int) -> bytes:
		return self._file.read(n)

	def write(self, data: bytes) -> int:
		return self._file.write(data)

	def seek(self, pos: int) -> None:
		self._file.seek(pos)

	def tell(self) -> int:
		return self._file.tell()

	def close(self) -> None:
		self._file.close()

	def flush(self) -> None:
		self._file.flush()


class StructWriter:
	def __init__(
		self,
		file: io.BufferedWriter,
		encoding: str | None = None,
	) -> None:
		self._file = file
		self.encoding = encoding

	def write_int(self, value: int) -> None:
		self._file.write(pack(U_INT, value))

	def write_long(self, value: int) -> None:
		self._file.write(pack(U_LONG_LONG, value))

	def write_byte(self, value: int) -> None:
		self._file.write(pack(U_CHAR, value))

	def write_short(self, value: int) -> None:
		self._file.write(pack(U_SHORT, value))

	def _write_text(
		self,
		text: str,
		len_size_spec: str,
		encoding: str | None = None,
		pad_to_length: int | None = None,
	) -> None:
		if encoding is None:
			encoding = self.encoding
			if encoding is None:
				raise ValueError("encoding is None")
		text_bytes = text.encode(encoding)
		length = len(text_bytes)
		max_length = calcmax(len_size_spec)
		if length > max_length:
			raise ValueError(f"Text is too long for size spec {len_size_spec}")
		self._file.write(
			pack(
				len_size_spec,
				pad_to_length or length,
			),
		)
		self._file.write(text_bytes)
		if pad_to_length:
			for _ in range(pad_to_length - length):
				self._file.write(pack(U_CHAR, 0))

	def write_tiny_text(
		self,
		text: str,
		encoding: str | None = None,
		editable: bool = False,
	) -> None:
		pad_to_length = 255 if editable else None
		self._write_text(
			text,
			U_CHAR,
			encoding=encoding,
			pad_to_length=pad_to_length,
		)

	def write_text(
		self,
		text: str,
		encoding: str | None = None,
	) -> None:
		self._write_text(text, U_SHORT, encoding=encoding)

	def close(self) -> None:
		self._file.close()

	def flush(self) -> None:
		self._file.flush()

	@property
	def name(self) -> str:
		return self._file.name

	def tell(self) -> int:
		return self._file.tell()

	def write(self, data: bytes) -> int:
		return self._file.write(data)


def read_header(file: MultiFileReader) -> Header:
	file.seek(0)

	magic = file.read(len(MAGIC))
	if magic != MAGIC:
		raise UnknownFileFormat(f"magic {magic!r} != {MAGIC!r}")

	uuid = UUID(bytes=file.read(16))
	encoding = read_byte_string(file, U_CHAR).decode(UTF8)
	if encodings.search_function(encoding) is None:
		raise UnknownEncoding(encoding)

	reader = StructReader(file, encoding)
	compression = reader.read_tiny_text()
	if compression not in COMPRESSIONS:
		raise UnknownCompression(compression)

	def read_tags() -> dict[str, str]:
		count = reader.read_byte()
		return {reader.read_tiny_text(): reader.read_tiny_text() for _ in range(count)}

	tags = read_tags()

	def read_content_types() -> Sequence[str]:
		content_types: list[str] = []
		count = reader.read_byte()
		for _ in range(count):
			content_type = reader.read_text()
			content_types.append(content_type)
		return tuple(content_types)

	content_types = read_content_types()

	blob_count = reader.read_int()
	store_offset = reader.read_long()
	size = reader.read_long()
	refs_offset = reader.tell()

	return Header(
		magic=magic,
		uuid=uuid,
		encoding=encoding,
		compression=compression,
		tags=MappingProxyType(tags),
		content_types=content_types,
		blob_count=blob_count,
		store_offset=store_offset,
		refs_offset=refs_offset,
		size=size,
	)


def meld_ints(a: int, b: int) -> int:
	return (a << 16) | b


def unmeld_ints(c: int) -> tuple[int, int]:
	bstr = bin(c).lstrip("0b").zfill(48)
	a, b = bstr[-48:-16], bstr[-16:]
	return int(a, 2), int(b, 2)


class Slob:
	def __init__(
		self,
		*filenames: str,
	) -> None:
		self._f = MultiFileReader(*filenames)

		try:
			self._header = read_header(self._f)
			if self._f.size != self._header.size:
				raise IncorrectFileSize(
					f"File size should be {self._header.size}, "
					f"{self._f.size} bytes found",
				)
		except FileFormatException:
			self._f.close()
			raise

		self._refs = RefList(
			self._f,
			self._header.encoding,
			offset=self._header.refs_offset,
		)

		self._g = MultiFileReader(*filenames)
		self._store = Store(
			self._g,
			self._header.store_offset,
			COMPRESSIONS[self._header.compression].decompress,
			self._header.content_types,
		)

	def __enter__(self) -> Slob:
		return self

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_val: BaseException | None,
		exc_tb: TracebackType | None,
	) -> None:
		self.close()

	@property
	def identity(self) -> str:
		return self._header.uuid.hex

	@property
	def content_types(self) -> Sequence[str]:
		return self._header.content_types

	@property
	def tags(self) -> MappingProxyType[str, str]:
		return self._header.tags

	@property
	def blob_count(self) -> int:
		return self._header.blob_count

	@property
	def compression(self) -> str:
		return self._header.compression

	@property
	def encoding(self) -> str:
		return self._header.encoding

	def __len__(self) -> int:
		return len(self._refs)

	def __getitem__(self, i: int) -> Any:
		# this is called by bisect_left
		return self.getBlobByIndex(i)

	def __iter__(self) -> Iterator[Blob]:
		for i in range(len(self._refs)):
			yield self.getBlobByIndex(i)

	def count(self) -> int:
		# just to comply with Sequence and make type checker happy
		raise NotImplementedError

	def index(self, x: Blob) -> int:
		# just to comply with Sequence and make type checker happy
		raise NotImplementedError

	def getBlobByIndex(self, i: int) -> Blob:
		ref = self._refs[i]

		def read_func() -> bytes:
			return self._store.get(ref.bin_index, ref.item_index)[1]

		read_func = lru_cache(maxsize=None)(read_func)

		def read_content_type_func() -> str:
			return self._store.content_type(ref.bin_index, ref.item_index)

		content_id = meld_ints(ref.bin_index, ref.item_index)
		return Blob(
			content_id=content_id,
			key=ref.key,
			fragment=ref.fragment,
			read_content_type_func=read_content_type_func,
			read_func=read_func,
		)

	def get(self, blob_id: int) -> tuple[str, bytes]:
		"""Returns (content_type: str, content: bytes)."""
		bin_index, bin_item_index = unmeld_ints(blob_id)
		return self._store.get(bin_index, bin_item_index)

	@cache
	def as_dict(
		self: Slob,
		strength: int = TERTIARY,
		maxlength: int | None = None,
	) -> KeydItemDict:
		return KeydItemDict(
			cast("Sequence", self),
			strength=strength,
			maxlength=maxlength,
		)

	def close(self) -> None:
		self._f.close()
		self._g.close()


def open(*filenames: str) -> Slob:  # noqa: A001
	return Slob(*filenames)


class BinMemWriter:
	def __init__(self) -> None:
		self.content_type_ids: list[int] = []
		self.item_dir: list[bytes] = []
		self.items: list[bytes] = []
		self.current_offset = 0

	def add(self, content_type_id: int, blob_bytes: bytes) -> None:
		self.content_type_ids.append(content_type_id)
		self.item_dir.append(pack(U_INT, self.current_offset))
		length_and_bytes = pack(U_INT, len(blob_bytes)) + blob_bytes
		self.items.append(length_and_bytes)
		self.current_offset += len(length_and_bytes)

	def __len__(self) -> int:
		return len(self.item_dir)

	def finalize(
		self,
		fout: BufferedIOBase,
		compress: Callable[[bytes], bytes],
	) -> None:
		count = len(self)
		fout.write(pack(U_INT, count))
		for content_type_id in self.content_type_ids:
			fout.write(pack(U_CHAR, content_type_id))
		content = b"".join(self.item_dir + self.items)
		compressed = compress(content)
		fout.write(pack(U_INT, len(compressed)))
		fout.write(compressed)
		self.content_type_ids.clear()
		self.item_dir.clear()
		self.items.clear()


ItemT = TypeVar("ItemT")


class ItemList(Generic[ItemT]):
	def __init__(
		self,
		reader: StructReader,
		offset: int,
		count_or_spec: str | int,
		pos_spec: str,
	) -> None:
		self.lock = RLock()
		self.reader = reader
		reader.seek(offset)
		count: int
		if isinstance(count_or_spec, str):
			count_spec = count_or_spec
			count = unpack(count_spec, reader.read(calcsize(count_spec)))[0]
		elif isinstance(count_or_spec, int):
			count = count_or_spec
		else:
			raise TypeError(f"invalid {count_or_spec = }")
		self._count: int = count
		self.pos_offset = reader.tell()
		self.pos_spec = pos_spec
		self.pos_size = calcsize(pos_spec)
		self.data_offset = self.pos_offset + self.pos_size * count

	def __len__(self) -> int:
		return self._count

	def pos(self, i: int) -> int:
		with self.lock:
			self.reader.seek(self.pos_offset + self.pos_size * i)
			return unpack(self.pos_spec, self.reader.read(self.pos_size))[0]

	def read(self, pos: int) -> ItemT:
		with self.lock:
			self.reader.seek(self.data_offset + pos)
			return self._read_item()

	@abstractmethod
	def _read_item(self) -> ItemT:
		pass

	def __getitem__(self, i: int) -> ItemT:
		if i >= len(self) or i < 0:
			raise IndexError("index out of range")
		return self.read(self.pos(i))


class RefList(ItemList[Ref]):
	def __init__(
		self,
		f: IOBase,
		encoding: str,
		offset: int = 0,
		count: int | None = None,
	) -> None:
		super().__init__(
			reader=StructReader(f, encoding),
			offset=offset,
			count_or_spec=U_INT if count is None else count,
			pos_spec=U_LONG_LONG,
		)

	@lru_cache(maxsize=512)
	def __getitem__(
		self,
		i: int,
	) -> Ref:
		if i >= len(self) or i < 0:
			raise IndexError("index out of range")
		return cast("Ref", self.read(self.pos(i)))

	def _read_item(self) -> Ref:
		key = self.reader.read_text()
		bin_index = self.reader.read_int()
		item_index = self.reader.read_short()
		fragment = self.reader.read_tiny_text()
		return Ref(
			key=key,
			bin_index=bin_index,
			item_index=item_index,
			fragment=fragment,
		)

	@cache
	def as_dict(
		self: RefList,
		strength: int = TERTIARY,
		maxlength: int | None = None,
	) -> KeydItemDict:
		return KeydItemDict(
			cast("Sequence", self),
			strength=strength,
			maxlength=maxlength,
		)


class Bin(ItemList[bytes]):
	def __init__(
		self,
		count: int,
		bin_bytes: bytes,
	) -> None:
		super().__init__(
			reader=StructReader(io.BytesIO(bin_bytes)),
			offset=0,
			count_or_spec=count,
			pos_spec=U_INT,
		)

	def _read_item(self) -> bytes:
		content_len = self.reader.read_int()
		return self.reader.read(content_len)


class StoreItem(NamedTuple):
	content_type_ids: list[int]
	compressed_content: bytes


class Store(ItemList[StoreItem]):
	def __init__(
		self,
		file: IOBase,
		offset: int,
		decompress: Callable[[bytes], bytes],
		content_types: Sequence[str],
	) -> None:
		super().__init__(
			reader=StructReader(file),
			offset=offset,
			count_or_spec=U_INT,
			pos_spec=U_LONG_LONG,
		)
		self.decompress = decompress
		self.content_types = content_types

	@lru_cache(maxsize=32)
	def __getitem__(
		self,
		i: int,
	) -> StoreItem:
		if i >= len(self) or i < 0:
			raise IndexError("index out of range")
		return cast("StoreItem", self.read(self.pos(i)))

	def _read_item(self) -> StoreItem:
		bin_item_count = self.reader.read_int()
		packed_content_type_ids = self.reader.read(bin_item_count * U_CHAR_SIZE)
		content_type_ids = []
		for i in range(bin_item_count):
			content_type_id = unpack(U_CHAR, packed_content_type_ids[i : i + 1])[0]
			content_type_ids.append(content_type_id)
		content_length = self.reader.read_int()
		content = self.reader.read(content_length)
		return StoreItem(
			content_type_ids=content_type_ids,
			compressed_content=content,
		)

	def _content_type(
		self,
		bin_index: int,
		item_index: int,
	) -> tuple[str, StoreItem]:
		store_item = self[bin_index]
		content_type_id = store_item.content_type_ids[item_index]
		content_type = self.content_types[content_type_id]
		return content_type, store_item

	def content_type(
		self,
		bin_index: int,
		item_index: int,
	) -> str:
		return self._content_type(bin_index, item_index)[0]

	@lru_cache(maxsize=16)
	def _decompress(self, bin_index: int) -> bytes:
		store_item = self[bin_index]
		return self.decompress(store_item.compressed_content)

	def get(
		self,
		bin_index: int,
		item_index: int,
	) -> tuple[str, bytes]:
		content_type, store_item = self._content_type(bin_index, item_index)
		content = self._decompress(bin_index)
		count = len(store_item.content_type_ids)
		store_bin = Bin(count, content)
		content = store_bin[item_index]
		return (content_type, content)


class WriterEvent(NamedTuple):
	name: str
	data: Any


class Writer:
	def __init__(  # noqa: PLR0913
		self,
		filename: str,
		workdir: str | None = None,
		encoding: str = UTF8,
		compression: str | None = DEFAULT_COMPRESSION,
		min_bin_size: int = 512 * 1024,
		max_redirects: int = 5,
		observer: Callable[[WriterEvent], None] | None = None,
		version_info: bool = True,
	) -> None:
		self.filename = filename
		self.observer = observer
		if os.path.exists(self.filename):
			raise SystemExit(f"File {self.filename!r} already exists")

		# make sure we can write
		with fopen(self.filename, "wb"):
			pass

		self.encoding = encoding

		if encodings.search_function(self.encoding) is None:
			raise UnknownEncoding(self.encoding)

		self.workdir = workdir

		self.tmpdir = tmpdir = tempfile.TemporaryDirectory(
			prefix=f"{os.path.basename(filename)}-",
			dir=workdir,
		)

		self.f_ref_positions = self._wbfopen("ref-positions")
		self.f_store_positions = self._wbfopen("store-positions")
		self.f_refs = self._wbfopen("refs")
		self.f_store = self._wbfopen("store")

		self.max_redirects = max_redirects
		if max_redirects:
			self.aliases_path = os.path.join(tmpdir.name, "aliases")
			self.f_aliases = Writer(
				self.aliases_path,
				workdir=tmpdir.name,
				max_redirects=0,
				compression=None,
				version_info=False,
			)

		if compression is None:
			compression = ""
		if compression not in COMPRESSIONS:
			raise UnknownCompression(compression)

		self.compress = COMPRESSIONS[compression].compress

		self.compression = compression
		self.content_types: dict[str, int] = {}

		self.min_bin_size = min_bin_size

		self.current_bin: BinMemWriter | None = None

		created_at = (
			os.getenv("SLOB_TIMESTAMP") or datetime.now(timezone.utc).isoformat()
		)

		self.blob_count = 0
		self.ref_count = 0
		self.bin_count = 0
		self._tags = {
			"created.at": created_at,
		}
		if version_info:
			self._tags.update(
				{
					"version.python": sys.version.replace("\n", " "),
					"version.pyicu": icu.VERSION,
					"version.icu": icu.ICU_VERSION,
				},
			)
		self.tags = MappingProxyType(self._tags)

	def _wbfopen(self, name: str) -> StructWriter:
		return StructWriter(
			fopen(os.path.join(self.tmpdir.name, name), "wb"),
			encoding=self.encoding,
		)

	def tag(self, name: str, value: str = "") -> None:
		if len(name.encode(self.encoding)) > MAX_TINY_TEXT_LEN:
			self._fire_event("tag_name_too_long", (name, value))
			return

		if len(value.encode(self.encoding)) > MAX_TINY_TEXT_LEN:
			self._fire_event("tag_value_too_long", (name, value))
			value = ""

		self._tags[name] = value

	@staticmethod
	def key_is_too_long(actual_key, fragment) -> bool:
		return len(actual_key) > MAX_TEXT_LEN or len(fragment) > MAX_TINY_TEXT_LEN

	@staticmethod
	def _split_key(
		key: str | tuple[str, str],
	) -> tuple[str, str]:
		if isinstance(key, str):
			actual_key = key
			fragment = ""
		else:
			actual_key, fragment = key
		return actual_key, fragment

	def add(
		self,
		blob: bytes,
		*keys: str,
		content_type: str = "",
	) -> None:
		if len(blob) > MAX_LARGE_BYTE_STRING_LEN:
			self._fire_event("content_too_long", blob)
			return

		if len(content_type) > MAX_TEXT_LEN:
			self._fire_event("content_type_too_long", content_type)
			return

		actual_keys = []

		for key in keys:
			actual_key, fragment = self._split_key(key)
			if self.key_is_too_long(actual_key, fragment):
				self._fire_event("key_too_long", key)
			else:
				actual_keys.append((actual_key, fragment))

		if not actual_keys:
			return

		current_bin = self.current_bin

		if current_bin is None:
			current_bin = self.current_bin = BinMemWriter()
			self.bin_count += 1

		if content_type not in self.content_types:
			self.content_types[content_type] = len(self.content_types)

		current_bin.add(self.content_types[content_type], blob)
		self.blob_count += 1
		bin_item_index = len(current_bin) - 1
		bin_index = self.bin_count - 1

		for actual_key, fragment in actual_keys:
			self._write_ref(actual_key, bin_index, bin_item_index, fragment)

		if (
			current_bin.current_offset > self.min_bin_size
			or len(current_bin) == MAX_BIN_ITEM_COUNT
		):
			self._write_current_bin()

	def add_alias(self, key: str, target_key: str) -> None:
		if not self.max_redirects:
			raise NotImplementedError
		if self.key_is_too_long(*self._split_key(key)):
			self._fire_event("alias_too_long", key)
			return
		if self.key_is_too_long(*self._split_key(target_key)):
			self._fire_event("alias_target_too_long", target_key)
			return
		self.f_aliases.add(pickle.dumps(target_key), key)

	def _fire_event(
		self,
		name: str,
		data: Any = None,
	) -> None:
		if self.observer:
			self.observer(WriterEvent(name, data))

	def _write_current_bin(self) -> None:
		current_bin = self.current_bin
		if current_bin is None:
			return
		self.f_store_positions.write_long(self.f_store.tell())
		current_bin.finalize(
			self.f_store._file,
			self.compress,
		)
		self.current_bin = None

	def _write_ref(
		self,
		key: str,
		bin_index: int,
		item_index: int,
		fragment: str = "",
	) -> None:
		self.f_ref_positions.write_long(self.f_refs.tell())
		self.f_refs.write_text(key)
		self.f_refs.write_int(bin_index)
		self.f_refs.write_short(item_index)
		self.f_refs.write_tiny_text(fragment)
		self.ref_count += 1

	def _sort(self) -> None:
		self._fire_event("begin_sort")
		f_ref_positions_sorted = self._wbfopen("ref-positions-sorted")
		self.f_refs.flush()
		self.f_ref_positions.close()
		with MultiFileReader(self.f_ref_positions.name, self.f_refs.name) as f:
			ref_list = RefList(f, self.encoding, count=self.ref_count)
			sortkey_func = sortkey(IDENTICAL)
			for i in sorted(
				range(len(ref_list)),
				key=lambda j: sortkey_func(ref_list[j].key),
			):
				ref_pos = ref_list.pos(i)
				f_ref_positions_sorted.write_long(ref_pos)
		f_ref_positions_sorted.close()
		os.remove(self.f_ref_positions.name)
		os.rename(f_ref_positions_sorted.name, self.f_ref_positions.name)
		self.f_ref_positions = StructWriter(
			fopen(self.f_ref_positions.name, "ab"),
			encoding=self.encoding,
		)
		self._fire_event("end_sort")

	def _resolve_aliases(self) -> None:  # noqa: PLR0912
		self._fire_event("begin_resolve_aliases")
		self.f_aliases.finalize()

		def read_key_frag(item: Blob, default_fragment: str) -> tuple[str, str]:
			key_frag = pickle.loads(item.content)
			if isinstance(key_frag, str):
				return key_frag, default_fragment
			to_key, fragment = key_frag
			return to_key, fragment

		with MultiFileReader(
			self.f_ref_positions.name,
			self.f_refs.name,
		) as f_ref_list:
			ref_list = RefList(f_ref_list, self.encoding, count=self.ref_count)
			ref_dict = ref_list.as_dict()
			with Slob(self.aliases_path) as aliasesSlob:
				aliases = aliasesSlob.as_dict()
				path = os.path.join(self.tmpdir.name, "resolved-aliases")
				alias_writer = Writer(
					path,
					workdir=self.tmpdir.name,
					max_redirects=0,
					compression=None,
					version_info=False,
				)

				for item in aliasesSlob:
					from_key = item.key
					keys = set()
					keys.add(from_key)
					to_key, fragment = read_key_frag(item, item.fragment)
					count = 0
					while count <= self.max_redirects:
						# is target key itself a redirect?
						try:
							alias_item: Blob = next(aliases[to_key])
						except StopIteration:
							break
						orig_to_key = to_key
						to_key, fragment = read_key_frag(
							alias_item,
							fragment,
						)
						count += 1
						keys.add(orig_to_key)
					if count > self.max_redirects:
						self._fire_event("too_many_redirects", from_key)
					target_ref: Ref
					try:
						target_ref = cast("Ref", next(ref_dict[to_key]))
					except StopIteration:
						self._fire_event("alias_target_not_found", to_key)
					else:
						for key in keys:
							ref = Ref(
								key=key,
								bin_index=target_ref.bin_index,
								item_index=target_ref.item_index,
								# last fragment in the chain wins
								fragment=target_ref.fragment or fragment,
							)
							alias_writer.add(pickle.dumps(ref), key)

				alias_writer.finalize()

		with Slob(path) as resolved_aliases_reader:
			previous = None
			targets = set()

			for item in resolved_aliases_reader:
				ref = pickle.loads(item.content)
				if previous is not None and ref.key != previous.key:
					for bin_index, item_index, fragment in sorted(targets):
						self._write_ref(previous.key, bin_index, item_index, fragment)
					targets.clear()
				targets.add((ref.bin_index, ref.item_index, ref.fragment))
				previous = ref

			for bin_index, item_index, fragment in sorted(targets):
				self._write_ref(previous.key, bin_index, item_index, fragment)

		self._sort()
		self._fire_event("end_resolve_aliases")

	def finalize(self) -> None:
		self._fire_event("begin_finalize")
		if self.current_bin is not None:
			self._write_current_bin()

		self._sort()
		if self.max_redirects:
			self._resolve_aliases()

		files = (
			self.f_ref_positions,
			self.f_refs,
			self.f_store_positions,
			self.f_store,
		)
		for f in files:
			f.close()

		buf_size = 10 * 1024 * 1024

		def write_tags(tags: MappingProxyType[str, Any], f: StructWriter) -> None:
			f.write(pack(U_CHAR, len(tags)))
			for key, value in tags.items():
				f.write_tiny_text(key)
				f.write_tiny_text(value, editable=True)

		with fopen(self.filename, mode="wb") as output_file:
			out = StructWriter(output_file, self.encoding)
			out.write(MAGIC)
			out.write(uuid4().bytes)
			out.write_tiny_text(self.encoding, encoding=UTF8)
			out.write_tiny_text(self.compression)

			write_tags(self.tags, out)

			def write_content_types(
				content_types: dict[str, int],
				f: StructWriter,
			) -> None:
				count = len(content_types)
				f.write(pack(U_CHAR, count))
				types = sorted(content_types.items(), key=operator.itemgetter(1))
				for content_type, _ in types:
					f.write_text(content_type)

			write_content_types(self.content_types, out)

			out.write_int(self.blob_count)
			store_offset = (
				out.tell()
				+ U_LONG_LONG_SIZE  # this value
				+ U_LONG_LONG_SIZE  # file size value
				+ U_INT_SIZE  # ref count value
				+ os.stat(self.f_ref_positions.name).st_size
				+ os.stat(self.f_refs.name).st_size
			)
			out.write_long(store_offset)
			out.flush()

			file_size = (
				out.tell()  # bytes written so far
				+ U_LONG_LONG_SIZE  # file size value
				+ 2 * U_INT_SIZE  # ref count and bin count
			)
			file_size += sum(os.stat(f.name).st_size for f in files)
			out.write_long(file_size)

			def mv(src: StructWriter, out: StructWriter) -> None:
				fname = src.name
				self._fire_event("begin_move", fname)
				with fopen(fname, mode="rb") as f:
					while True:
						data = f.read(buf_size)
						if len(data) == 0:
							break
						out.write(data)
						out.flush()
				os.remove(fname)
				self._fire_event("end_move", fname)

			out.write_int(self.ref_count)
			mv(self.f_ref_positions, out)
			mv(self.f_refs, out)

			out.write_int(self.bin_count)
			mv(self.f_store_positions, out)
			mv(self.f_store, out)

		self.f_ref_positions = None  # type: ignore # noqa: PGH003
		self.f_refs = None  # type: ignore # noqa: PGH003
		self.f_store_positions = None  # type: ignore # noqa: PGH003
		self.f_store = None  # type: ignore # noqa: PGH003

		self.tmpdir.cleanup()
		self._fire_event("end_finalize")

	def size_header(self) -> int:
		size = 0
		size += len(MAGIC)
		size += 16  # uuid bytes
		size += U_CHAR_SIZE + len(self.encoding.encode(UTF8))
		size += U_CHAR_SIZE + len(self.compression.encode(self.encoding))

		size += U_CHAR_SIZE  # tag length
		size += U_CHAR_SIZE  # content types count

		# tags and content types themselves counted elsewhere

		size += U_INT_SIZE  # blob count
		size += U_LONG_LONG_SIZE  # store offset
		size += U_LONG_LONG_SIZE  # file size
		size += U_INT_SIZE  # ref count
		size += U_INT_SIZE  # bin count

		return size

	def size_tags(self) -> int:
		size = 0
		for key in self.tags:
			size += U_CHAR_SIZE + len(key.encode(self.encoding))
			size += 255
		return size

	def size_content_types(self) -> int:
		size = 0
		for content_type in self.content_types:
			size += U_CHAR_SIZE + len(content_type.encode(self.encoding))
		return size

	def size_data(self) -> int:
		files = (
			self.f_ref_positions,
			self.f_refs,
			self.f_store_positions,
			self.f_store,
		)
		return sum(os.stat(f.name).st_size for f in files)

	def __enter__(self) -> Slob:
		return cast("Slob", self)

	def close(self) -> None:
		for _file in (
			self.f_ref_positions,
			self.f_refs,
			self.f_store_positions,
			self.f_store,
		):
			if _file is None:
				continue
			self._fire_event("WARNING: closing without finalize()")
			try:
				_file.close()
			except Exception:
				pass
		if self.tmpdir and isdir(self.tmpdir.name):
			self.tmpdir.cleanup()
		self.tmpdir = None  # type: ignore # noqa: PGH003

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_val: BaseException | None,
		exc_tb: TracebackType | None,
	) -> None:
		"""
		It used to call self.finalize() here
		that was bad!
		__exit__ is not meant for doing so much as finalize() is doing!
		so make sure to call writer.finalize() after you are done!.
		"""
		self.close()
