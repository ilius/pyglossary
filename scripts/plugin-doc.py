#!/usr/bin/python3

import sys
import tomllib as toml
from os.path import abspath, dirname, join
from pathlib import Path

from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.glossary import Glossary
from pyglossary.sort_keys import defaultSortKeyName

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

template = Template(
	"""${"##"} ${description}

${topTables}

% if readDependsLinks and readDependsLinks == writeDependsLinks:
${"### Dependencies for reading and writing"}

PyPI Links: ${readDependsLinks}

To install, run:

```sh
${readDependsCmd}
```
% else:
	% if readDependsLinks:
${"### Dependencies for reading"}

PyPI Links: ${readDependsLinks}

To install, run:

```sh
${readDependsCmd}
```
	% endif

	% if writeDependsLinks:
${"### Dependencies for writing"}

PyPI Links: ${writeDependsLinks}

To install, run

```sh
${writeDependsCmd}
```
	% endif
% endif

% if docTail:
${docTail.replace('(./doc/', '(../')}

% endif
${toolsTable}

% if relatedFormats:
${"### Related Formats"}

% for desc, lname in relatedFormats:
- [${desc}](./${lname}.md)
% endfor
% endif
""",
)


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


def renderLink(title, url):
	if "(" in title or ")" in title:
		url = f"<{url}>"
	title = title.replace("|", "-")
	return f"[{title}]({url})"


def pypiLink(pypiName):
	urlPath = pypiName.replace("==", "/")
	urlPath = urlPath.replace(">", "%3E")
	return renderLink(
		pypiName.replace("==", " "),
		f"https://pypi.org/project/{urlPath}",
	)


def makeDependsDoc(cls):
	if not (cls and getattr(cls, "depends", None)):
		return "", ""
	links = ", ".join([pypiLink(pypiName) for pypiName in cls.depends.values()])
	cmd = "pip3 install " + " ".join(
		cls.depends.values(),
	)
	return links, cmd


def sortKeyName(p):
	value = p.sortKeyName
	if value:
		return codeValue(value)
	return "(" + codeValue(defaultSortKeyName) + ")"


def renderCell(value):
	return str(value).replace("\n", "\\n").replace("\t", "\\t")


def renderTable(rows):
	"""rows[0] must be headers."""
	rows = [[renderCell(cell) for cell in row] for row in rows]
	width = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
	rows = [
		[cell.ljust(width[i], " ") for i, cell in enumerate(row)]
		for rowI, row in enumerate(rows)
	]
	rows.insert(1, ["-" * colWidth for colWidth in width])
	return "\n".join(["| " + " | ".join(row) + " |" for row in rows])


def renderTableNoPadding(rows):
	"""rows[0] must be headers."""
	rows = [[renderCell(cell) for cell in row] for row in rows]
	width = [len(x) for x in rows[0]]
	rows.insert(1, ["-" * colWidth for colWidth in width])
	return "\n".join(["| " + " | ".join(row) + " |" for row in rows])


def renderRWOptions(options):
	return renderTable(
		[("Name", "Default", "Type", "Comment")]
		+ [
			(
				optName,
				codeValue(default),
				optionsType[optName],
				optionsComment[optName],
			)
			for optName, default in options.items()
		],
	)


def pluginIsActive(p):
	if not p.enable:
		return False
	if not (p.canRead or p.canWrite):
		return False
	return userPluginsDirPath not in p.path.parents


def getToolSourceLink(tool):
	url = tool.get("source")
	if not url:
		return "―"
	_, title = url.split("://")
	if title.startswith("github.com/"):
		title = "@" + title[len("github.com/") :]
	return renderLink(title, url)


userPluginsDirPath = Path(userPluginsDir)
plugins = [p for p in Glossary.plugins.values() if pluginIsActive(p)]
pluginByName = Glossary.plugins

pluginsDir = join(rootDir, "pyglossary", "plugins")


for p in plugins:
	module = p.module
	optionsProp = p.optionsProp

	wiki = module.wiki
	wiki_md = "―"
	if wiki:
		if wiki.startswith("https://github.com/"):
			wiki_title = "@" + wiki[len("https://github.com/") :]
		else:
			wiki_title = wiki.split("/")[-1].replace("_", " ")
		wiki_md = renderLink(wiki_title, wiki)

	website_md = "―"
	website = module.website
	if website:
		if isinstance(website, str):
			website_md = website
		else:
			try:
				url, title = website
			except ValueError:
				raise ValueError(f"{website = }") from None
			website_md = renderLink(title, url)

	(
		readDependsLinks,
		readDependsCmd,
	) = makeDependsDoc(getattr(module, "Reader", None))

	(
		writeDependsLinks,
		writeDependsCmd,
	) = makeDependsDoc(getattr(module, "Writer", None))

	docTail = getattr(module, "docTail", [])

	toolsFile = join(pluginsDir, p.moduleName, "tools.toml")
	try:
		with open(toolsFile, "rb") as _file:
			tools_toml = toml.load(_file)
	except FileNotFoundError:
		tools = []
	except Exception as e:
		print(f"\nFile: {toolsFile}")
		raise e
	else:
		for toolName, tool in tools_toml.items():
			tool.update({"name": toolName})
		tools = tools_toml.values()

	table = [
		("Attribute", "Value"),
		("Name", p.name),
		("snake_case_name", p.lname),
		("Description", p.description),
		("Extensions", ", ".join([codeValue(ext) for ext in p.extensions])),
		("Read support", yesNo(p.canRead)),
		("Write support", yesNo(p.canWrite)),
		("Single-file", yesNo(p.singleFile)),
		("Kind", f"{kindEmoji(module.kind)} {module.kind}"),
	]

	if p.canWrite:
		table += [
			("Sort-on-write", p.sortOnWrite.desc),
			("Sort key", sortKeyName(p)),
		]

	table += [
		("Wiki", wiki_md),
		("Website", website_md),
	]

	generalInfoTable = "### General Information\n\n" + renderTable(table)
	topTables = generalInfoTable

	try:
		optionsType = {optName: opt.typ for optName, opt in optionsProp.items()}
	except Exception:
		print(f"{optionsProp = }")
		raise
	optionsComment = {
		optName: opt.comment.replace("\n", "<br />")
		for optName, opt in optionsProp.items()
	}

	readOptions = p.getReadOptions()
	if readOptions:
		topTables += "\n\n### Read options\n\n" + renderRWOptions(readOptions)

	writeOptions = p.getWriteOptions()
	if writeOptions:
		topTables += "\n\n### Write options\n\n" + renderRWOptions(writeOptions)

	toolsTable = ""
	if tools:
		toolsTable = "### Dictionary Applications/Tools\n\n" + renderTable(
			[
				(
					"Name & Website",
					"Source code",
					"License",
					"Platforms",
					"Language",
				),
			]
			+ [
				(
					f"[{tool['name']}]({tool['web']})",
					getToolSourceLink(tool),
					tool["license"],
					", ".join(tool["platforms"]),
					tool.get("plang", ""),
				)
				for tool in tools
			],
		)

	relatedFormatNames = getattr(module, "relatedFormats", [])
	relatedFormats = []
	for formatName in relatedFormatNames:
		assert formatName != p.name
		relatedPlug = pluginByName[formatName]
		relatedFormats.append((relatedPlug.description, relatedPlug.lname))

	text = template.render(
		description=p.description,
		codeValue=codeValue,
		yesNo=yesNo,
		topTables=topTables,
		optionsProp=optionsProp,
		readOptions=readOptions,
		writeOptions=writeOptions,
		optionsComment=optionsComment,
		optionsType=optionsType,
		readDependsLinks=readDependsLinks,
		readDependsCmd=readDependsCmd,
		writeDependsLinks=writeDependsLinks,
		writeDependsCmd=writeDependsCmd,
		docTail=docTail,
		toolsTable=toolsTable,
		relatedFormats=relatedFormats,
	)
	for _i in range(3):
		text = text.replace("\n\n\n", "\n\n")
	if text.endswith("\n\n"):
		text = text[:-1]
	with open(
		join(rootDir, "doc", "p", f"{p.lname}.md"),
		mode="w",
		encoding="utf-8",
		newline="\n",
	) as _file:
		_file.write(text)

indexText = renderTableNoPadding(
	[("Description", "Name", "Doc Link")]
	+ [
		(
			p.description,
			p.name,
			renderLink(f"{p.lname}.md", f"./{p.lname}.md"),
		)
		for p in plugins
	],
)

with open(
	join(rootDir, "doc", "p", "__index__.md"),
	mode="w",
	encoding="utf-8",
	newline="\n",
) as _file:
	_file.write(indexText + "\n")
