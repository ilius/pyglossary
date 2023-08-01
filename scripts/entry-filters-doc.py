#!/usr/bin/python3

import sys
from os.path import abspath, dirname, join

from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.entry_filters import entryFiltersRules
from pyglossary.ui.base import UIBase

ui = UIBase()
ui.loadConfig(user=False)

template = Template("""${entryFiltersTable}
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


def renderCell(value):
	return str(value).replace("\n", "\\n").replace("\t", "\\t")


def renderTable(rows):
	"""rows[0] must be headers."""
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


def getCommandFlagsMD(name):
	if name is None:
		return ""
	opt = ui.configDefDict[name]
	flag = name.replace("_", "-")

	if opt.falseComment:
		return f"`--{flag}`<br/>`--no-{flag}`"

	return f"`--{flag}`"


for configParam, default, filterClass in entryFiltersRules:
	if configParam is None:
		continue
	assert ui.config[configParam] == default
	assert filterClass.name == configParam


entryFiltersTable = "## Entry Filters\n\n" + renderTable(
	[(
		"Name",
		"Default Enabled",
		"Command Flags",
		"Description",
	)] + [
		(
			codeValue(filterClass.name),
			yesNo(bool(default)),
			getCommandFlagsMD(configParam),
			filterClass.desc,
		)
		for configParam, default, filterClass in entryFiltersRules
	],
)

text = template.render(
	entryFiltersTable=entryFiltersTable,
)
with open(join(rootDir, "doc", "entry-filters.md"), mode="w") as _file:
	_file.write(text)
