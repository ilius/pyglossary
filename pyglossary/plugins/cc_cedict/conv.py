import re
import os
from .pinyin import convert
from .summarize import summarize
from formats_common import pip

line_reg = re.compile(r"^([^ ]+) ([^ ]+) \[([^\]]+)\] /(.+)/$")

jinja_env = None

script_dir = os.path.dirname(__file__)

COLORS = {
	"": "black",
	"1": "red",
	"2": "orange",
	"3": "green",
	"4": "blue",
	"5": "black",
}


def load_jinja():
	global jinja_env
	try:
		import jinja2
	except ModuleNotFoundError as e:
		e.msg += f", run `{pip} install jinja2` to install"
		raise e
	from plugin_lib.jinja2htmlcompress import HTMLCompress
	jinja_env = jinja2.Environment(
		loader=jinja2.FileSystemLoader(script_dir),
		extensions=[HTMLCompress],
	)

def parse_line(line):
	line = line.strip()
	match = line_reg.match(line)
	if match is None: return None
	trad, simp, pinyin, eng = match.groups()
	pinyin = pinyin.replace("u:", "v")
	eng = eng.split("/")
	return trad, simp, pinyin, eng

def make_entry(trad, simp, pinyin, eng):
	eng_names = list(map(summarize, eng))
	names = [simp, trad, pinyin] + eng_names
	article = render_article(trad, simp, pinyin, eng)
	return names, article

def render_article(trad, simp, pinyin, eng):
	if jinja_env is None:
		load_jinja()

	# pinyin_tones = [convert(syl) for syl in pinyin.split()]
	nice_pinyin = []
	tones = []
	for syllable in pinyin.split():
		nice_syllable, tone = convert(syllable)
		nice_pinyin.append(nice_syllable)
		tones.append(tone)

	template = jinja_env.get_template("article.html")
	return template.render(
		zip=zip,
		COLORS=COLORS,
		trad=trad,
		simp=simp,
		pinyin=nice_pinyin,
		tones=tones,
		defns=eng,
	)

