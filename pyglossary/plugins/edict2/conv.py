from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from io import BytesIO
from typing import TYPE_CHECKING, NamedTuple, cast

from lxml import etree as ET

from pyglossary.core import log

from .pinyin import convert
from .summarize import summarize
from .util import get_chinese_references

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence

	from pyglossary.lxml_types import T_htmlfile


__all__ = [
	"Article",
	"create_render_definition",
	"parse_line_simp",
	"parse_line_trad",
	"render_article",
	"render_definition_no_links",
	"render_definition_with_links",
	"render_syllables",
	"render_syllables_color",
	"render_syllables_no_color",
]


_re_line = re.compile(r"^([^ ]+) ([^ ]+) \[([^\]]+)\] /(.+)/$")

_COLORS = {
	"": "black",
	"1": "red",
	"2": "orange",
	"3": "green",
	"4": "blue",
	"5": "black",
}


def parse_line_trad(line: str) -> tuple[str, str, str, list[str]] | None:
	line = line.strip()
	match = _re_line.match(line)
	if match is None:
		return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "ü")
	return trad, simp, pinyin, eng.split("/")


def parse_line_simp(line: str) -> tuple[str, str, str, list[str]] | None:
	line = line.strip()
	match = _re_line.match(line)
	if match is None:
		return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "ü")
	return simp, trad, pinyin, eng.split("/")


class Article(NamedTuple):
	first: str
	second: str
	pinyin: str
	eng: list[str]

	def names(self) -> list[str]:
		if self.first == self.second:
			return [self.first]
		return [self.first, self.second]

	def definition_summaries(self) -> list[str]:
		return list(map(summarize, self.eng))


def render_syllables(
	hf: T_htmlfile,
	syllables: Sequence[str],
	tones: Sequence[str],
	color: bool = True,
) -> None:
	if color and len(syllables) != len(tones):
		log.warning(f"unmatched tones: {syllables=}, {tones=}")
		color = False

	colors = _COLORS if color else defaultdict(lambda: "")

	with hf.element("div", style="display: inline-block"):
		for index, syllable in enumerate(syllables):
			tone = tones[index] if len(syllables) == len(tones) else ""
			with hf.element("font", color=colors[tone]):
				if index > 0:
					if syllable[0].isupper() and tone:
						# Add a space before a capitalized syllable.
						hf.write(" ")
					elif unicodedata.normalize("NFD", syllable[0])[0] in "aeiou" and tone:
						# Add an apostrophe before a vowel.
						hf.write("'")
				hf.write(syllable)


def render_syllables_no_color(
	hf: T_htmlfile,
	syllables: Sequence[str],
	tones: Sequence[str],
) -> None:
	render_syllables(
		hf=hf,
		syllables=syllables,
		tones=tones,
		color=False,
	)


def render_syllables_color(
	hf: T_htmlfile,
	syllables: Sequence[str],
	tones: Sequence[str],
) -> None:
	render_syllables(
		hf=hf,
		syllables=syllables,
		tones=tones,
		color=True,
	)


def render_definition_no_links(hf: T_htmlfile, definition: str) -> None:
	with hf.element("li"):
		hf.write(definition)


def render_definition_with_links(
	hf: T_htmlfile,
	traditional_title: bool,
	definition: str,
) -> None:
	chinese_refs = get_chinese_references(definition)
	get_chinese = (
		(lambda match: match.trad) if traditional_title else (lambda match: match.simp)
	)

	match = None
	with hf.element("li"):
		try:
			match = next(chinese_refs)
			hf.write(definition[0 : match.start])
			with hf.element("a", href=f"bword://{get_chinese(match)}"):
				hf.write(match.text)

		except StopIteration:
			hf.write(definition)
			return

		for next_match in chinese_refs:
			hf.write(definition[match.end : next_match.start])
			match = next_match
			with hf.element(
				"a",
				href=f"bword://{get_chinese(match)}",
			):
				hf.write(match.text)

		hf.write(definition[match.end :])


def create_render_definition(
	traditional_title: bool,
	link_references: bool,
) -> Callable[[T_htmlfile, str], None]:
	if not link_references:
		return render_definition_no_links

	def func(hf: T_htmlfile, definition: str) -> None:
		render_definition_with_links(
			hf=hf,
			definition=definition,
			traditional_title=traditional_title,
		)

	return func


# @lru_cache(maxsize=128)
def _convert_pinyin(pinyin: str) -> tuple[Sequence[str], Sequence[str]]:
	return tuple(zip(*map(convert, pinyin.split()), strict=False))  # type: ignore


def render_article(
	render_syllables: Callable[[T_htmlfile, str], None],
	render_definition: Callable[[T_htmlfile, str], None],
	article: Article,
) -> tuple[list[str], str]:
	names = article.names()

	# pinyin_tones = [convert(syl) for syl in pinyin.split()]
	pinyin_list, tones = _convert_pinyin(article.pinyin)

	f = BytesIO()
	with ET.htmlfile(f, encoding="utf-8") as hf_:  # noqa: PLR1702
		hf = cast("T_htmlfile", hf_)
		with hf.element("div", style="border: 1px solid; padding: 5px"):
			with hf.element("div"):
				with hf.element("big"):
					render_syllables(hf, names[0], tones)

				if len(names) > 1:
					hf.write("\xa0/\xa0")  # "\xa0" --> "&#160;" == "&nbsp;"
					render_syllables(hf, names[1], tones)

				hf.write(ET.Element("br"))

				with hf.element("big"):
					render_syllables(hf, pinyin_list, tones)

			with hf.element("div"):
				with hf.element("ul"):
					for defn in article.eng:
						render_definition(hf, defn)

	return names, f.getvalue().decode("utf-8")
