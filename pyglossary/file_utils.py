from __future__ import annotations

import sys
from itertools import (
	repeat,
	takewhile,
)

__all__ = ["fileCountLines"]


def fileCountLines(filename: str, newline: bytes = b"\n") -> int:
	with open(filename, "rb") as _file:
		bufgen = takewhile(
			lambda x: x,  # predicate
			(_file.read(1024 * 1024) for _ in repeat(None)),  # iterable
		)
		return sum(buf.count(newline) for buf in bufgen if buf)


if __name__ == "__main__":
	for filename in sys.argv[1:]:
		print(fileCountLines(filename), filename)  # noqa: T201
