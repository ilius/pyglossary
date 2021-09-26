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
${"##"} ${description} ${"##"}

${"### General Information ###"}
Name | Value
---- | -------
Name | ${name}
snake_case_name | ${lname}
Description | ${description}
Extensions | ${", ".join([codeValue(ext) for ext in extensions])}
Read support | ${yesNo(canRead)}
Write support | ${yesNo(canWrite)}
Single-file | ${yesNo(singleFile)}
Kind | ${kindEmoji(kind)} ${kind}
Wiki | ${wiki_md}
Website | ${website_md}


% if readOptions:
${"### Read options ###"}
Name | Default | Type | Comment
---- | ------- | ---- | -------
% for optName, default in readOptions.items():
`${optName}` | ${codeValue(default)} | ${optionsType[optName]} | ${optionsComment[optName]}
% endfor
% endif

% if writeOptions:
${"### Write options ###"}
Name | Default | Type | Comment
---- | ------- | ---- | -------
% for optName, default in writeOptions.items():
`${optName}` | ${codeValue(default)} | ${optionsType[optName]} | ${optionsComment[optName]}
% endfor
% endif

% if tools:
${"### Dictionary Applications/Tools ###"}
Name & Website | License | Platforms
-------------- | ------- | ---------
% for tool in tools:
[${tool["name"]}](${tool["web"]}) | ${tool["license"]} | ${", ".join(tool["platforms"])}
% endfor
% endif
""")

indexTemplate = Template("""
Name | Description | Doc Link
---- | ----------- | --------
% for p in plugins:
${p.name} | ${p.description} | [${p.lname}.md](./${p.lname}.md)
% endfor
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

def kindEmoji(kind):
	if not kind:
		return ""
	return {
		"text": "📝",
		"binary": "🔢",
		"directory": "📁",
		"package": "📦",
	}[kind]

for p in Glossary.plugins.values():
	module = p.pluginModule
	optionsProp = p.optionsProp

	wiki = module.wiki
	wiki_md = "―"
	if wiki:
		if wiki.startswith("https://github.com/"):
			wiki_title = "@" + wiki[len("https://github.com/"):]
		else:
			wiki_title = wiki.split("/")[-1].replace("_", " ")
		wiki_md = f"[{wiki_title}]({wiki})"

	website_md = "―"
	if module.website:
		website_md = module.website

	tools = getattr(module, "tools", [])

	text = template.render(
		codeValue=codeValue,
		yesNo=yesNo,
		kindEmoji=kindEmoji,
		name=p.name,
		lname=p.lname,
		description=p.description,
		extensions=p.extensions,
		canRead=p.canRead,
		canWrite=p.canWrite,
		singleFile=p.singleFile,
		kind=module.kind,
		wiki_md=wiki_md,
		website_md=website_md,
		optionsProp=optionsProp,
		readOptions=p.getReadOptions(),
		writeOptions=p.getWriteOptions(),
		optionsComment={
			optName: opt.comment.replace("\n", "<br />")
			for optName, opt in optionsProp.items()
		},
		optionsType={
			optName: opt.typ
			for optName, opt in optionsProp.items()
		},
		tools=tools,
	)
	with open(join("doc", "p", f"{p.lname}.md"), mode="w") as _file:
		_file.write(text)

indexText = indexTemplate.render(
	plugins=Glossary.plugins.values(),
)
with open(join("doc", "p", f"__index__.md"), mode="w") as _file:
	_file.write(indexText)

