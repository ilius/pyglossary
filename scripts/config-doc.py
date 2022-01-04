#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from pprint import pprint
from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.ui.base import UIBase

ui = UIBase()
ui.loadConfig(user=False)

# ui.configDefDict

template = Template("""${paramsTable}

${"## Configuration Files"}

The default configuration values are stored in [config.json](../config.json) file in source/installation directory.

The user configuration file - if exists - will override default configuration values.
The location of this file depends on the operating system:

- Linux or BSD: `~/.pyglossary/config.json`
- Mac: `~/Library/Preferences/PyGlossary/config.json`
- Windows: `C:\\Users\\USERNAME\\AppData\\Roaming\\PyGlossary\\config.json`

${"## Using as library"}

When you use PyGlossary as a library, neither of `config.json` files are loaded. So if you want to change the config, you should set `glos.config` property (which you can do only once for each instance of `Glossary`). For example:

```python
glos = Glossary()
glos.config = {
	"lower": True,
}
```
""")


def codeValue(x):
	s = str(x)
	if s:
		return "`" + s + "`"
	return ""


def renderCell(value):
	return str(value).replace("\n", "\\n").replace("\t", "\\t")


def renderTable(rows):
	"""
		rows[0] must be headers
	"""
	rows = [
		[
			renderCell(cell) for cell in row
		]
		for row in rows
	]
	width = [
		max(len(row[i]) for row in rows)
		for i in range(len(rows[0]))
	]
	rows = [
		[
			cell.ljust(width[i], " ")
			for i, cell in enumerate(row)
		]
		for rowI, row in enumerate(rows)
	]
	rows.insert(1, [
		"-" * colWidth
		for colWidth in width
	])
	return "\n".join([
		"| " + " | ".join(row) + " |"
		for row in rows
	])


def getCommandFlagsMD(name, opt):
	if name.startswith("color.enable.cmd."):
		return f"`--no-color`"

	if not opt.hasFlag:
		return ""
	flag = opt.customFlag
	if not flag:
		flag = name.replace('_', '-')

	if opt.falseComment:
		return f"`--{flag}`<br/>`--no-{flag}`"

	return f"`--{flag}`"

def optionComment(name, opt):
	comment = opt.comment

	if name.startswith("color.cmd."):
		if comment:
			comment += "<br/>"
		comment += "See [term_colors.md](./term_colors.md)"

	return comment


paramsTable = "## Configuration Parameters\n\n" + renderTable(
	[(
		"Name",
		"Command Flags",
		"Type",
		"Default",
		"Comment",
	)] + [
		(
			codeValue(name),
			getCommandFlagsMD(name, opt),
			opt.typ,
			codeValue(ui.config[name]),
			optionComment(name, opt),
		)
		for name, opt in ui.configDefDict.items()
		if not opt.disabled
	],
)

text = template.render(
	codeValue=codeValue,
	ui=ui,
	paramsTable=paramsTable,
)
with open(join(rootDir, "doc", "config.md"), mode="w") as _file:
	_file.write(text)
