from itertools import (
	takewhile,
	repeat,
)

from io import IOBase


def toBytes(s: "AnyStr") -> bytes:
	return bytes(s, "utf-8") if isinstance(s, str) else bytes(s)


def fileCountLines(filename: str, newline: str = "\n"):
	newline = toBytes(newline)  # required? FIXME
	f = open(filename, "rb")  # or "r"
	bufgen = takewhile(
		lambda x: x, (f.read(1024 * 1024) for _ in repeat(None))
	)
	return sum(
		buf.count(newline) for buf in bufgen if buf
	)


# TODO: make it sub-class of IOBase
class FileLineWrapper(object):
	def __init__(self, f: IOBase):
		self.f = f
		self.line = 0

	def close(self) -> None:
		self.f.close()

	def readline(self) -> str:
		self.line += 1
		return self.f.readline()

	def __iter__(self) -> "Iterator[str]":
		return iter(self.f)
