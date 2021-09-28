import re
import os
from .pinyin import convert
from .summarize import summarize
from pyglossary.plugins.formats_common import pip, log

line_reg = re.compile(r"^([^ ]+) ([^ ]+) \[([^\]]+)\] /(.+)/$")

script_dir = os.path.dirname(__file__)

COLORS = {
	"": "black",
	"1": "red",
	"2": "orange",
	"3": "green",
	"4": "blue",
	"5": "black",
}


def parse_line(line):
	line = line.strip()
	match = line_reg.match(line)
	if match is None:
		return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "v")
	eng = eng.split("/")
	return trad, simp, pinyin, eng


def make_entry(trad, simp, pinyin, eng, traditional_title):
	eng_names = list(map(summarize, eng))
	names = [
		trad if traditional_title else simp,
		simp if traditional_title else trad,
		pinyin
	] + eng_names
	article = render_article(trad, simp, pinyin, eng, traditional_title)
	return names, article


def colorize(hf, syllables, tones):
	if len(syllables) != len(tones):
		log.warn(f"unmatched tones: syllables={syllables!r}, tones={tones}")
		with hf.element("div", style="display: inline-block"):
			for syllable in syllables:
				with hf.element("font", color=""):
					hf.write(syllable)
		return

	with hf.element("div", style="display: inline-block"):
		for syllable, tone in zip(syllables, tones):
			with hf.element("font", color=COLORS[tone]):
				hf.write(syllable)


def render_article(trad, simp, pinyin, eng, traditional_title):
	from lxml import etree as ET
	from io import BytesIO

	# pinyin_tones = [convert(syl) for syl in pinyin.split()]
	pinyin_list = []
	tones = []
	for syllable in pinyin.split():
		nice_syllable, tone = convert(syllable)
		pinyin_list.append(nice_syllable)
		tones.append(tone)

	f = BytesIO()
	with ET.htmlfile(f, encoding="utf-8") as hf:
		with hf.element("div", style="border: 1px solid; padding: 5px"):
			with hf.element("div"):
				with hf.element("big"):
					colorize(hf, trad if traditional_title else simp, tones)
				if trad != simp:
					hf.write("\xa0/\xa0")  # "\xa0" --> "&#160;" == "&nbsp;"
					colorize(hf, simp if traditional_title else trad, tones)
				hf.write(ET.Element("br"))
				with hf.element("big"):
					colorize(hf, pinyin_list, tones)

			with hf.element("div"):
				with hf.element("ul"):
					for defn in eng:
						with hf.element("li"):
							hf.write(defn)

	article = f.getvalue().decode("utf-8")
	return article
