import re
from typing import TYPE_CHECKING, cast

from pyglossary.core import log

from .pinyin import convert
from .summarize import summarize

if TYPE_CHECKING:
	from collections.abc import Sequence

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


def parse_line(line: str) -> "tuple[str, str, str, list[str]] | None":
	line = line.strip()
	match = line_reg.match(line)
	if match is None:
		return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "v")
	return trad, simp, pinyin, eng.split("/")


def make_entry( # noqa: PLR0913
	trad: str,
	simp: str,
	pinyin: str,
	eng: list[str],
	traditional_title: bool,
	colorize_tones: bool,
) -> "tuple[list[str], str]":
	eng_names = list(map(summarize, eng))
	names = [
		trad if traditional_title else simp,
		simp if traditional_title else trad,
		pinyin,
	] + eng_names
	article = render_article(trad, simp, pinyin, eng, traditional_title, colorize_tones)
	return names, article


def colorize(
	hf: "T_htmlfile",
	syllables: "Sequence[str]",
	tones: "Sequence[str]",
	colorize_tones: bool,
) -> None:

	if len(syllables) != len(tones) or not colorize_tones:

		if len(syllables) != len(tones):
			log.warning(f"unmatched tones: {syllables=}, {tones=}")

		with hf.element("div", style="display: inline-block"):
			for syllable in syllables:
				with hf.element("font", color=""):
					hf.write(syllable)
		return

	with hf.element("div", style="display: inline-block"):
		for syllable, tone in zip(syllables, tones, strict=False):
			with hf.element("font", color=COLORS[tone]):
				hf.write(syllable)


def render_article( # noqa: PLR0913
	trad: str,
	simp: str,
	pinyin: str,
	eng: list[str],
	traditional_title: bool,
	colorize_tones: bool,
) -> str:
	from io import BytesIO

	from lxml import etree as ET

	# pinyin_tones = [convert(syl) for syl in pinyin.split()]
	pinyin_list = []
	tones = []
	for syllable in pinyin.split():
		nice_syllable, tone = convert(syllable)
		pinyin_list.append(nice_syllable)
		tones.append(tone)

	f = BytesIO()
	with ET.htmlfile(f, encoding="utf-8") as hf:  # noqa: PLR1702
		with hf.element("div", style="border: 1px solid; padding: 5px"):
			with hf.element("div"):
				with hf.element("big"):
					colorize(
						cast("T_htmlfile", hf),
						trad if traditional_title else simp,
						tones,
						colorize_tones,
					)
				if trad != simp:
					hf.write("\xa0/\xa0")  # "\xa0" --> "&#160;" == "&nbsp;"
					colorize(
						cast("T_htmlfile", hf),
						simp if traditional_title else trad,
						tones,
						colorize_tones,
					)
				hf.write(ET.Element("br"))
				with hf.element("big"):
					colorize(
						cast("T_htmlfile", hf),
						pinyin_list,
						tones,
						colorize_tones,
					)

			with hf.element("div"):
				with hf.element("ul"):
					for defn in eng:
						with hf.element("li"):
							hf.write(defn)

	return f.getvalue().decode("utf-8")
