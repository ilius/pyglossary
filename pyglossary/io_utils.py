from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterator

__all__ = ["nullBinaryIO", "nullTextIO"]


class _NullBinaryIO(io.BufferedIOBase):  # noqa: PLR0904
	def __enter__(self, *args):
		raise NotImplementedError

	def __exit__(self, *args):
		raise NotImplementedError

	def close(self) -> None:
		pass

	def fileno(self) -> int:
		raise NotImplementedError

	def flush(self) -> None:
		raise NotImplementedError

	def isatty(self) -> bool:
		raise NotImplementedError

	def readable(self) -> bool:
		raise NotImplementedError

	def seek(self, pos: int, whence: int = 0) -> int:
		raise NotImplementedError

	def seekable(self) -> bool:
		raise NotImplementedError

	def tell(self) -> int:
		raise NotImplementedError

	def truncate(self, pos: int | None = None) -> int:
		raise NotImplementedError

	def writable(self) -> bool:
		raise NotImplementedError

	def detach(self) -> io.RawIOBase:
		raise NotImplementedError

	def read(self, n: int | None = None) -> bytes:
		raise NotImplementedError

	def read1(self, n: int | None = None) -> bytes:
		raise NotImplementedError

	def readinto(self, buffer) -> int:
		raise NotImplementedError

	def readinto1(self, buffer) -> int:
		raise NotImplementedError

	# data: "bytearray|memoryview|array[Any]|io.mmap|io._CData|io.PickleBuffer"
	def write(self, data: bytes) -> int:  # type: ignore
		raise NotImplementedError

	def __iter__(self) -> Iterator[bytes]:
		raise NotImplementedError

	def __next__(self) -> bytes:
		raise NotImplementedError

	def readline(self, size: int | None = -1) -> bytes:
		raise NotImplementedError

	def readlines(self, hint: int = -1) -> list[bytes]:
		raise NotImplementedError

	def writelines(self, lines: list[bytes]) -> None:  # type: ignore
		raise NotImplementedError


class _NullTextIO(io.TextIOBase):  # noqa: PLR0904
	def __enter__(self, *args):
		raise NotImplementedError

	def __exit__(self, *args):
		raise NotImplementedError

	def close(self) -> None:
		pass

	def fileno(self) -> int:
		raise NotImplementedError

	def flush(self) -> None:
		raise NotImplementedError

	def isatty(self) -> bool:
		raise NotImplementedError

	def readable(self) -> bool:
		raise NotImplementedError

	def seek(self, pos: int, whence: int = 0) -> int:
		raise NotImplementedError

	def seekable(self) -> bool:
		raise NotImplementedError

	def tell(self) -> int:
		raise NotImplementedError

	def truncate(self, pos: int | None = None) -> int:
		raise NotImplementedError

	def writable(self) -> bool:
		raise NotImplementedError

	def detach(self) -> io.IOBase:  # type: ignore
		raise NotImplementedError

	def read(self, n: int | None = None) -> str:
		raise NotImplementedError

	def read1(self, n: int | None = None) -> str:
		raise NotImplementedError

	def readinto(self, buffer) -> io.BufferedIOBase:
		raise NotImplementedError

	def readinto1(self, buffer) -> io.BufferedIOBase:
		raise NotImplementedError

	# data: "bytearray|memoryview|array[Any]|io.mmap|io._CData|io.PickleBuffer"
	def write(self, data: bytes) -> int:  # type: ignore
		raise NotImplementedError

	def __iter__(self) -> Iterator[str]:  # type: ignore
		raise NotImplementedError

	def __next__(self) -> str:  # type: ignore
		raise NotImplementedError

	def readline(self, size: int | None = -1) -> str:  # type: ignore
		raise NotImplementedError

	def readlines(self, hint: int = -1) -> list[str]:  # type: ignore
		raise NotImplementedError

	def writelines(self, lines: list[str]) -> None:  # type: ignore
		raise NotImplementedError


nullBinaryIO = _NullBinaryIO()
nullTextIO = _NullTextIO()
