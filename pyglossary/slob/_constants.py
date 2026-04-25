# slob format constants (pyglossary)
from __future__ import annotations

from struct import calcsize

DEFAULT_COMPRESSION = "lzma2"

UTF8 = "utf-8"
MAGIC = b"!-1SLOB\x1f"

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

MIME_TEXT = "text/plain"
MIME_HTML = "text/html"
