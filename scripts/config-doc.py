#!/usr/bin/env python

import json
import re
import sys
from os.path import abspath, dirname, join

from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.ui.base import UIBase

ui = UIBase()
ui.loadConfig(user=False)

# ui.configDefDict

re_flag = re.compile("(\\s)(--[a-z\\-]+)")

template = Template("""${paramsTable}

${"Configuration Files"}
${"-------------------"}

The default configuration values are stored in `config.json <./../config.json/>`_
file in source/installation directory.

The user configuration file - if exists - will override default configuration
values. The location of this file depends on the operating system:

- Linux or BSD: ``~/.pyglossary/config.json``
- Mac: ``~/Library/Preferences/PyGlossary/config.json``
- Windows: ``C:\\Users\\USERNAME\\AppData\\Roaming\\PyGlossary\\config.json``

${"Using as library"}
${"----------------"}

When you use PyGlossary as a library, neither of ``config.json`` files are
loaded. So if you want to change the config, you should set ``glos.config``
property (which you can do only once for each instance of ``Glossary``).
For example:

.. code:: python

	glos = Glossary()
	glos.config = {
		"lower": True,
	}
""")

with open(join(rootDir, "scripts/term-colors.json")) as _file:
	termColors = json.load(_file)


def codeValue(x):
	s = str(x)
	if s:
		return "``" + s + "``"
	return ""


def tableRowSep(width, c="-"):
	return "+" + c + f"{c}+{c}".join([
		c * w for w in width
	]) + c + "+"


def renderTable(rows):
	"""rows[0] must be headers."""
	colN = len(rows[0])
	width = [
		max(
			max(len(line) for line in row[i].split("\n"))
			for row in rows
		)
		for i in range(colN)
	]
	rowSep = tableRowSep(width, "-")
	headerSep = tableRowSep(width, "=")

	lines = [rowSep]
	for rowI, row in enumerate(rows):
		newRows = []
		for colI, cell in enumerate(row):
			for lineI, line in enumerate(cell.split("\n")):
				if lineI >= len(newRows):
					newRows.append([
						" " * width[colI]
						for colI in range(colN)
					])
				newRows[lineI][colI] = line.ljust(width[colI], " ")
		for row in newRows:
			lines.append("| " + " | ".join(row) + " |")
		if rowI == 0:
			lines.append(headerSep)
		else:
			lines.append(rowSep)

	# widthsStr = ", ".join([str(w) for w in width])
	# header = f".. table:: my table\n\t:widths: {widthsStr}\n\n"
	# return header + "\n".join(["\t" + line for line in lines])

	return "\n".join(lines)


def getCommandFlagsMD(name, opt):
	if name.startswith("color.enable.cmd."):
		return "``--no-color``"

	if not opt.hasFlag:
		return ""
	flag = opt.customFlag
	if not flag:
		flag = name.replace('_', '-')

	if opt.falseComment:
		return f"| ``--{flag}``\n| ``--no-{flag}``"
		# return f"- ``--{flag}``\n- ``--no-{flag}``"

	return f"``--{flag}``"


def optionComment(name, opt):
	comment = opt.comment

	comment = re_flag.sub("\\1``\\2``", comment)

	if name.startswith("color.cmd."):
		comment = f"| {comment}\n| See `term-colors.md <./term-colors.md/>`_"

	return comment  # noqa: RET504


def jsonCodeValue(value):
	# if isinstance(value, str):
	# 	return codeValue(value)
	return codeValue(json.dumps(value))


def defaultOptionValue(name, opt, images):
	value = ui.config[name]
	valueMD = jsonCodeValue(value)

	if name.startswith("color.cmd."):
		_hex = termColors[str(value)].lstrip("#")
		imageI = f"image{len(images)}"
		images.append(
			f".. |{imageI}| image:: https://via.placeholder.com/20/{_hex}/000000?text=+",
		)
		valueMD += f"\n|{imageI}|"

	return valueMD


title = "Configuration Parameters"
title += "\n" + len(title) * "-" + "\n"

images = []

paramsTable = title + renderTable(
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
			defaultOptionValue(name, opt, images),
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

text += "\n"
for image in images:
	text += "\n" + image

with open(join(rootDir, "doc", "config.rst"), mode="w") as _file:
	_file.write(text)
