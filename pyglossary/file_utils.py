from itertools import (
	repeat,
	takewhile,
)


def fileCountLines(filename: str, newline: bytes = b"\n") -> int:
	with open(filename, "rb") as _file:
		bufgen = takewhile(
			lambda x: x, (_file.read(1024 * 1024) for _ in repeat(None)),
		)
		return sum(
			buf.count(newline) for buf in bufgen if buf
		)
