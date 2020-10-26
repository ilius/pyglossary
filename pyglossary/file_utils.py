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
