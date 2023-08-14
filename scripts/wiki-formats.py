#!/usr/bin/env python3

import os
import sys
from os.path import join
from pathlib import Path

from mako.template import Template

rootDir = join(
	os.getenv("HOME"),
	"pyglossary",
)
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.glossary import Glossary

Glossary.init(
	# usePluginsJson=False,
)

"""
Mako template engine:
	https://docs.makotemplates.org/en/latest/
	https://github.com/sqlalchemy/mako
	https://pypi.org/project/Mako/
	Package python3-mako in Debian repos
"""

hasIconSet = {
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
	"mobi",
	"octopus_mdict",
	"sql",
	"stardict",
	"tabfile",
	"wiktionary_dump",
	"zim",
}

def pluginIsActive(p):
	if not p.enable:
		return False
	if not (p.canRead or p.canWrite):
		return False
	if userPluginsDirPath in p.path.parents:
		return False
	return True


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
	return (
		'<img src="https://raw.githubusercontent.com/wiki/'
		f'ilius/pyglossary/icons/{p.lname}.png" height="32"/>'
	)


def kindEmoji(p):
	kind = p.module.kind
	if not kind:
		return ""
	return {
		"text": "📝",
		"binary": "🔢",
		"directory": "📁",
		"package": "📦",
	}[kind]


willNotSupportRead = {
	"epub2",
	"kobo",
	"mobi",
	# "html_dir",
	"info",
	"sql",
}
willNotSupportWrite = {
	"appledict_bin",
	"babylon_bgl",
	"cc_cedict",
	"cc_kedict",
	"freedict",
	"jmdict",
	"octopus_mdict",
	"wiktionary_dump",
	"xdxf",
	"wiktextract",
	"jmnedict",
}


def readCheck(p):
	if p.lname in willNotSupportRead:
		return "❌"
	return "✔" if p.canRead else ""


def writeCheck(p):
	if p.lname in willNotSupportWrite:
		return "❌"
	return "✔" if p.canWrite else ""


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


userPluginsDirPath = Path(userPluginsDir)
plugins = [
	p
	for p in Glossary.plugins.values()
	if pluginIsActive(p)
]

text = template.render(
	plugins=plugins,
	iconImg=iconImg,
	kindEmoji=kindEmoji,
	readCheck=readCheck,
	writeCheck=writeCheck,
)
with open("Formats.md", mode="w", encoding="utf-8") as _file:
	_file.write(text)
