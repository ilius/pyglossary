import re
import os
from .pinyin import convert
from .summarize import summarize
from .jinja2htmlcompress import HTMLCompress
import jinja2

line_reg = re.compile(r'^([^ ]+) ([^ ]+) \[([^\]]+)\] /(.+)/$')
def parse_line(line):
    line = line.strip()
    match = line_reg.match(line)
    if match is None:
        print("bad line:")
        print(line)
    trad, simp, pinyin, eng = match.groups()
    pinyin = pinyin.replace('u:', 'v')
    eng = eng.split('/')
    return trad, simp, pinyin, eng

def make_entry(trad, simp, pinyin, eng):
    eng_names = list(map(summarize, eng))
    names = [simp, trad, pinyin] + eng_names
    article = render_article(trad, simp, pinyin, eng)
    return names, article

script_dir = os.path.dirname(__file__)
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(script_dir),
    extensions=[HTMLCompress])
COLORS = {'': 'black', '1': 'red', '2': 'orange', '3': 'green', '4': 'blue', '5': 'black'}
def render_article(trad, simp, pinyin, eng):
    pinyin_tones = [convert(syl) for syl in pinyin.split()]
    nice_pinyin = []
    tones = []
    for syllable in pinyin.split():
        nice_syllable, tone = convert(syllable)
        nice_pinyin.append(nice_syllable)
        tones.append(tone)
    args = dict(COLORS=COLORS, trad=trad, simp=simp,
        pinyin=nice_pinyin, tones=tones, defns=eng)

    template = jinja_env.get_template("article.html")
    return template.render(zip=zip, **args)

