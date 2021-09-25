#!/usr/bin/python3

import sys
import os
import json
from os.path import join, dirname, abspath
from pprint import pprint
from mako.template import Template

rootDir = join(
	os.getenv("HOME"),
	"pyglossary",
)
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary

Glossary.init()

"""
Mako template engine:
	https://docs.makotemplates.org/en/latest/
	https://github.com/sqlalchemy/mako
	https://pypi.org/project/Mako/
	Package python3-mako in Debian repos
"""

hasIconSet = set([
	"aard2_slob",
	"appledict_bin",
	"appledict",
	"babylon_bgl",
	"cc_cedict",
	"csv",
	"dicformids",
	"dict_cc",
	"dict_cc_split",
	"digitalnk",
	"dsl",
	"epub2",
	"jmdict",
	"kobo",
	"lingoes_ldf",
	"octopus_mdict",
	"sql",
	"stardict",
	"tabfile",
	"wiktionary_dump",
	"zim",
])

def codeValue(x):
	s = str(x)
	if s:
		return "`" + s + "`"
	return ""

def yesNo(x):
	if x is True:
		return "Yes"
	if x is False:
		return "No"
	return ""

def iconImg(p):
	if p.lname not in hasIconSet:
		return ""
	return f'<img src="https://raw.githubusercontent.com/wiki/ilius/pyglossary/icons/{p.lname}.png" height="32"/>'

def kindEmoji(p):
	kind = p.pluginModule.kind
	if not kind:
		return ""
	return {
		"text": "📝",
		"binary": "🔢",
		"directory": "📁",
		"package": "📦",
	}[kind]


willNotSupportRead = set([
	"epub2",
	"kobo",
	"mobi",
	# "html_dir",
	"info",
	"sql",
])
willNotSupportWrite = set([
	"appledict_bin",
	"babylon_bgl",
	"cc_cedict",
	"cc_kedict",
	"freedict",
	"jmdict",
	"octopus_mdict",
	"wiktionary_dump",
	"xdxf",
])

def readCheck(p):
	if p.lname in willNotSupportRead:
		return "❌"
	return "✔" if p.canRead else ""


def writeCheck(p):
	if p.lname in willNotSupportWrite:
		return "❌"
	return "✔" if p.canRead else ""


template = Template("""
|   | Description |   | Read | Write| Doc Link |
|:-:| ----------- |:-:|:----:|:----:| -------- |
% for p in plugins:
| ${iconImg(p)} | ${p.description} | ${kindEmoji(p)} | ${readCheck(p)} | ${writeCheck(p)} | [${p.lname}.md](https://github.com/ilius/pyglossary/blob/master/doc/p/${p.lname}.md) |
% endfor

Legend:
- 📁	Directory
- 📝	Text file
- 📦	Package/archive file
- 🔢	Binary file
- ✔		Supported
- ❌ 	Will not be supported
""")

# wiki = module.wiki
# wiki_md = "―"
# if module.wiki:
# 	wiki_title = wiki.split("/")[-1].replace("_", " ")
# 	wiki_md = f"[{wiki_title}]({wiki})"

# website_md = "―"
# if module.website:
# 	website_md = module.website


text = template.render(
	plugins=Glossary.plugins.values(),
	iconImg=iconImg,
	kindEmoji=kindEmoji,
	readCheck=readCheck,
	writeCheck=writeCheck,
)
with open("Formats.md", mode="w") as _file:
	_file.write(text)

