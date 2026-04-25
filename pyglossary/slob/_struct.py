# Binary struct helpers for slob (pyglossary)
from __future__ import annotations

import io
from struct import calcsize, pack, unpack
from typing import TYPE_CHECKING

from ._constants import (
	U_CHAR,
	U_CHAR_SIZE,
	U_INT,
	U_INT_SIZE,
	U_LONG_LONG,
	U_LONG_LONG_SIZE,
	U_SHORT,
	U_SHORT_SIZE,
	calcmax,
)

if TYPE_CHECKING:
	from io import IOBase


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
