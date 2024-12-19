from __future__ import annotations

import re
from io import BytesIO
from typing import TYPE_CHECKING, NamedTuple, cast

from lxml import etree as ET

from pyglossary.core import log

from .pinyin import convert
from .summarize import summarize

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence

	from pyglossary.lxml_types import T_htmlfile


line_reg = re.compile(r"^([^ ]+) ([^ ]+) \[([^\]]+)\] /(.+)/$")

COLORS = {
	"": "black",
	"1": "red",
	"2": "orange",
	"3": "green",
	"4": "blue",
	"5": "black",
}


def parse_line_trad(line: str) -> tuple[str, str, str, list[str]] | None:
	line = line.strip()
	match = line_reg.match(line)
	if match is None:
		return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "v")
	return trad, simp, pinyin, eng.split("/")


def parse_line_simp(line: str) -> tuple[str, str, str, list[str]] | None:
	line = line.strip()
	match = line_reg.match(line)
	if match is None:
		return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "v")
	return simp, trad, pinyin, eng.split("/")


class Article(NamedTuple):
	first: str
	second: str
	pinyin: str
	eng: list[str]

	def names(self) -> list[str]:
		return [self.first, self.second, self.pinyin] + list(map(summarize, self.eng))


def render_syllables_no_color(
	hf: T_htmlfile,
	syllables: Sequence[str],
	_tones: Sequence[str],
) -> None:
	with hf.element("div", style="display: inline-block"):
		for syllable in syllables:
			with hf.element("font", color=""):
				hf.write(syllable)


def render_syllables_color(
	hf: T_htmlfile,
	syllables: Sequence[str],
	tones: Sequence[str],
) -> None:
	if len(syllables) != len(tones):
		log.warning(f"unmatched tones: {syllables=}, {tones=}")
		render_syllables_no_color(hf, syllables, tones)
		return

	with hf.element("div", style="display: inline-block"):
		for index, syllable in enumerate(syllables):
			with hf.element("font", color=COLORS[tones[index]]):
				hf.write(syllable)


# @lru_cache(maxsize=128)
def convert_pinyin(pinyin: str) -> tuple[Sequence[str], Sequence[str]]:
	return tuple(zip(*map(convert, pinyin.split()), strict=False))  # type: ignore


def render_article(
	render_syllables: Callable,
	article: Article,
) -> tuple[list[str], str]:
	names = article.names()

	# pinyin_tones = [convert(syl) for syl in pinyin.split()]
	pinyin_list, tones = convert_pinyin(article.pinyin)

	f = BytesIO()
	with ET.htmlfile(f, encoding="utf-8") as _hf:  # noqa: PLR1702
		hf = cast("T_htmlfile", _hf)
		with hf.element("div", style="border: 1px solid; padding: 5px"):
			with hf.element("div"):
				with hf.element("big"):
					render_syllables(hf, names[0], tones)

				if names[1] != names[0]:
					hf.write("\xa0/\xa0")  # "\xa0" --> "&#160;" == "&nbsp;"
					render_syllables(hf, names[1], tones)

				hf.write(ET.Element("br"))

				with hf.element("big"):
					render_syllables(hf, pinyin_list, tones)

			with hf.element("div"):
				with hf.element("ul"):
					for defn in article.eng:
						with hf.element("li"):
							hf.write(defn)

	return names, f.getvalue().decode("utf-8")
