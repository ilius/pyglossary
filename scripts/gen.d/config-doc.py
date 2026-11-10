#!/usr/bin/env python

import json
import re
import sys
from os.path import abspath, dirname, join

from mako.template import Template

myDir = dirname(abspath(__file__))
rootDir = dirname(dirname(myDir))
sys.path.insert(0, rootDir)

from pyglossary.ui.base import UIBase
from pyglossary.ui.config import configDefDict

ui = UIBase()
ui.loadConfig(user=False)

re_flag = re.compile("(\\s)(--[a-z\\-]+)")

template = Template(
	"""${paramsTable}

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
""",
)

with open(join(myDir, "term-colors.json"), encoding="utf-8") as _file:
	termColors = json.load(_file)


def codeValue(x):
	s = str(x)
	if s:
		return "``" + s + "``"
	return ""


def renderTable(rows):
	"""rows[0] must be headers."""
	lines = [".. list-table::", "   :header-rows: 1", ""]
	cellIndent = "       "
	for _rowI, row in enumerate(rows):
		for colI, cell in enumerate(row):
			prefix = "   * -" if colI == 0 else "     -"
			cellLines = cell.split("\n")
			if cellLines[0]:
				lines.append(f"{prefix} {cellLines[0]}")
			else:
				lines.append(prefix)
			lines.extend(cellIndent + line for line in cellLines[1:] if line.strip())
	return "\n".join(lines)


def getCommandFlagsMD(name, opt):
	if name.startswith("color.enable.cmd."):
		return "``--no-color``"

	if not opt.hasFlag:
		return ""
	flag = opt.customFlag
	if not flag:
		flag = name.replace("_", "-")

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


def defaultOptionValue(name, _opt, images):
	value = ui.config[name]
	valueMD = jsonCodeValue(value)

	if name.startswith("color.cmd."):
		hex_ = termColors[str(value)].lstrip("#")
		imageI = f"image{len(images)}"
		images.append(
			f".. |{imageI}| image:: https://via.placeholder.com/20/{hex_}/000000?text=+",
		)
		valueMD += f"\n|{imageI}|"

	return valueMD


title = "Configuration Parameters"
title += "\n" + len(title) * "-" + "\n"

images = []

paramsTable = (
	title
	+ "\n"
	+ renderTable(
		[
			(
				"Name",
				"Command Flags",
				"Type",
				"Default",
				"Comment",
			),
		]
		+ [
			(
				codeValue(name),
				getCommandFlagsMD(name, opt),
				opt.typ,
				defaultOptionValue(name, opt, images),
				optionComment(name, opt),
			)
			for name, opt in configDefDict.items()
			if not opt.disabled
		],
	)
)

text = template.render(
	codeValue=codeValue,
	ui=ui,
	paramsTable=paramsTable,
)

text += "\n"
for image in images:
	text += "\n" + image

with open(join(rootDir, "doc", "config.rst"), mode="w", encoding="utf-8") as _file:
	_file.write(text)
