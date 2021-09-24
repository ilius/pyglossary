#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from pprint import pprint
from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
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

template = Template("""
${"### General Information ###"}
Name | ${name}
---- | -------
Description | ${description}
Extensions | ${", ".join([codeValue(ext) for ext in extensions])}
Read support | ${yesNo(canRead)}
Write support | ${yesNo(canWrite)}
Single-file | ${yesNo(singleFile)}
Wiki | ${wiki_md}
Website | ${website_md}


% if canRead:
${"### Read options ###"}
Name | Default | Type | Comment
---- | ---- | ------- | -------
% for optName, default in readOptions.items():
`${optName}` | ${codeValue(default)} | ${optionsType[optName]} | ${optionsComment[optName]}
% endfor
% endif

% if canWrite:
${"### Write options ###"}
Name | Default | Type | Comment
---- | ---- | ------- | -------
% for optName, default in writeOptions.items():
`${optName}` | ${codeValue(default)} | ${optionsType[optName]} | ${optionsComment[optName]}
% endfor
% endif
""")

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

data = []
for p in Glossary.plugins.values():
	module = p.pluginModule
	optionsProp = p.optionsProp

	wiki = module.wiki
	wiki_md = "―"
	if module.wiki:
		wiki_title = wiki.split("/")[-1].replace("_", " ")
		wiki_md = f"[{wiki_title}]({wiki})"

	website_md = "―"
	if module.website:
		website_md = module.website

	data = {
		"codeValue": codeValue,
		"yesNo": yesNo,
		"name": p.name,
		"description": p.description,
		"extensions": p.extensions,
		"canRead": p.canRead,
		"canWrite": p.canWrite,
		"singleFile": p.singleFile,
		"wiki_md": wiki_md,
		"website_md": website_md,
		"optionsProp": optionsProp,
		"readOptions": p.getReadOptions(),
		"writeOptions": p.getWriteOptions(),
		"optionsComment": {
			optName: opt.comment.replace("\n", "<br />")
			for optName, opt in optionsProp.items()
		},
		"optionsType": {
			optName: opt.typ
			for optName, opt in optionsProp.items()
		},
	}
	text = template.render(**data)
	with open(join("doc", "p", f"{p.lname}.md"), mode="w") as _file:
		_file.write(text)

