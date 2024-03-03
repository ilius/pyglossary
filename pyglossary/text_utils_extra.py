import re

b_pattern_bar_us = re.compile(r"((?<!\\)(?:\\\\)*)\\\|".encode("ascii"))

__all__ = [
	"chBaseIntToStr",
	"formatHMS",
	"unescapeBarBytes",
]


def unescapeBarBytes(st: bytes) -> bytes:
	r"""Unscapes vertical bar (\|)."""
	# str.replace is probably faster than re.sub
	return b_pattern_bar_us.sub(b"\\1|", st).replace(b"\\\\", b"\\")


def chBaseIntToStr(number: int, base: int) -> str:
	"""Reverse function of int(str, base) and long(str, base)."""
	import string

	if not 2 <= base <= 36:
		raise ValueError("base must be in 2..36")
	abc = string.digits + string.ascii_letters
	result = ""
	if number < 0:
		number = -number
		sign = "-"
	else:
		sign = ""
	while True:
		number, rdigit = divmod(number, base)
		result = abc[rdigit] + result
		if number == 0:
			return sign + result
	return ""


def formatHMS(h: int, m: int, s: int) -> str:
	if h == 0:
		if m == 0:
			return f"{s:02d}"
		return f"{m:02d}:{s:02d}"
	return f"{h:02d}:{m:02d}:{s:02d}"
