# Multi-file sequential reader for slob (pyglossary)
from __future__ import annotations

import io
import os
from builtins import open as fopen
from io import BufferedIOBase
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
	from types import TracebackType


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

	def __enter__(self) -> Self:
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
