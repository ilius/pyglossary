import re
from collections.abc import Generator
from typing import NamedTuple

__all__ = ["get_chinese_references"]


class ChineseWordReference(NamedTuple):
	text: str
	trad: str
	simp: str
	start: int
	end: int
	trad_start: int
	trad_end: int
	simp_start: int
	simp_end: int


def get_chinese_references(text: str) -> Generator[ChineseWordReference]:
	# Matches Chinese characters including A-Z, 0-9,
	# and full/half-width punctuation.
	han = r"[\u4E00-\u9FFF\uFF00-\uFFEFA-Z0-9]"

	# Matches trad|simp[pinyin] or both[pinyin].
	chinese_refs = rf"((?P<trad>{han}+)\|(?P<simp>{han}+)|(?P<both>{han}+))\[[^\]]+\]"
	chinese_matches = re.finditer(chinese_refs, text)

	for match in chinese_matches:
		if match.group("both") is not None:
			yield ChineseWordReference(
				text=match.group(0),
				trad=match.group("both"),
				simp=match.group("both"),
				start=match.start(),
				end=match.end(),
				trad_start=match.start("both"),
				trad_end=match.end("both"),
				simp_start=match.start("both"),
				simp_end=match.end("both"),
			)
		else:
			yield ChineseWordReference(
				text=match.group(0),
				trad=match.group("trad"),
				simp=match.group("simp"),
				start=match.start(),
				end=match.end(),
				trad_start=match.start("trad"),
				trad_end=match.end("trad"),
				simp_start=match.start("simp"),
				simp_end=match.end("simp"),
			)
