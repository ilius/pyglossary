#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from pathlib import Path
from pprint import pprint
from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from pyglossary.core import userPluginsDir

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
Attribute | Value
--------- | -------
Name | ${name}
snake_case_name | ${lname}
Description | ${description}
Extensions | ${", ".join([codeValue(ext) for ext in extensions])}
Read support | ${yesNo(canRead)}
Write support | ${yesNo(canWrite)}
Single-file | ${yesNo(singleFile)}
Kind | ${kindEmoji(kind)} ${kind}
Sort-on-write | ${sortOnWrite}
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

% if readDependsLinks and readDependsLinks == writeDependsLinks:
${"### Dependencies for reading and writing ###"}
PyPI Links: ${readDependsLinks}

To install, run:

    ${readDependsCmd}

% else:
	% if readDependsLinks:
${"### Dependencies for reading ###"}
PyPI Links: ${readDependsLinks}

To install, run:

    ${readDependsCmd}

	% endif

	% if writeDependsLinks:
${"### Dependencies for writing ###"}
PyPI Links: ${writeDependsLinks}

To install, run

    ${writeDependsCmd}

	% endif
% endif

% if extraDocs:
% for title, text in extraDocs:
${f"### {title} ###"}
${text.replace('(./doc/', '(../')}

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
Description | Name | Doc Link
----------- | ---- | --------
% for p in plugins:
${p.description} | ${p.name} | [${p.lname}.md](./${p.lname}.md)
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


def makeDependsDoc(cls):
	if not (cls and getattr(cls, "depends", None)):
		return "", ""
	links = ", ".join([
		f"[{pypiName.replace('==', ' ')}](https://pypi.org/project/{pypiName.replace('==', '/')})"
		for pypiName in cls.depends.values()
	])
	cmd = "pip3 install " + " ".join(
		cls.depends.values()
	)
	return links, cmd

userPluginsDirPath = Path(userPluginsDir)
plugins = [
	p
	for p in Glossary.plugins.values()
	if userPluginsDirPath not in p.path.parents
]


for p in plugins:
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
	website = module.website
	if website:
		if isinstance(website, str):
			website_md = website
		else:
			try:
				url, title = website
			except ValueError:
				raise ValueError(f"website = {website!r}")
			title = title.replace("|", "\\|")
			website_md = f"[{title}]({url})"

	(
		readDependsLinks,
		readDependsCmd,
	) = makeDependsDoc(getattr(module, "Reader", None))

	(
		writeDependsLinks,
		writeDependsCmd,
	) = makeDependsDoc(getattr(module, "Writer", None))

	extraDocs = getattr(module, "extraDocs", [])

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
		sortOnWrite=p.sortOnWrite.desc,
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
		readDependsLinks=readDependsLinks,
		readDependsCmd=readDependsCmd,
		writeDependsLinks=writeDependsLinks,
		writeDependsCmd=writeDependsCmd,
		extraDocs=extraDocs,
		tools=tools,
	)
	with open(join("doc", "p", f"{p.lname}.md"), mode="w") as _file:
		_file.write(text)

indexText = indexTemplate.render(
	plugins=sorted(
		plugins,
		key=lambda p: p.description.lower(),
	),
)
with open(join("doc", "p", f"__index__.md"), mode="w") as _file:
	_file.write(indexText)

