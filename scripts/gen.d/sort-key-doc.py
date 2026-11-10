#!/usr/bin/python3

import sys
from os.path import abspath, dirname, join
from pathlib import Path

from mako.template import Template

rootDir = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.flags import ALWAYS, DEFAULT_YES, INTERNAL
from pyglossary.glossary_v2 import Glossary
from pyglossary.sort_keys import defaultSortKeyName, namedSortKeyList

Glossary.init(
	# usePluginsJson=False,
)

localeIntro = (
	"You can pass an [ICU Locale name/identifier]"
	"(https://unicode-org.github.io/icu/userguide/locale/) "
	"as part of `sortKey` / `--sort-key` value, after a `:` symbol. For example:"
)

template = Template(
	"""<!--
This document is generated from source code. Do NOT edit.
To update, modify plugins/*/__init__.py or pyglossary/sort_keys.py, then run ./scripts/gen
-->

# Sort Key

${"##"} Supported `sortKey` names / `--sort-key` argument values

${sortKeyTable}

${"##"} Sort Locale

${localeIntro}

- `--sort-key=:fa_IR.UTF-8`: Persian (then case-insensitive Latin)
- `--sort-key=headword:fa_IR.UTF-8`: Persian (then case-sensitive Latin)
- `--sort-key=headword:es`: case-sensitive Spanish
- `--sort-key=headword_lower:es`: case-insensitive Spanish
- `--sort-key=:es`: Spanish (case-insensitive by default)
- `--sort-key=:latn-arab`: first Latin, then Arabic
- `--sort-key=:fa-u-kr-latn-arab`: first Latin, then Persian
""",
)

# writers whose default sort uses the sort key (see plugin_prop / flags)
defaultWriteSortOnWrite = (ALWAYS, DEFAULT_YES, INTERNAL)


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


def renderTable(rows, align):
	"""
	rows[0] must be headers.

	align: list of "left" or "center" per column.
	"""
	rows = [[renderCell(cell) for cell in row] for row in rows]
	width = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
	sepRow = []
	for i, colWidth in enumerate(width):
		if align[i] == "center":
			sepRow.append(":" + "-" * (colWidth - 2) + ":")
		else:
			sepRow.append("-" * colWidth)
	rows = [[cell.ljust(width[i]) for i, cell in enumerate(row)] for row in rows]
	rows.insert(1, sepRow)
	return "\n".join(["| " + " | ".join(row) + " |" for row in rows])


userPluginsDirPath = Path(userPluginsDir)


def pluginIsActive(p):
	return userPluginsDirPath not in p.path.parents


def defaultForFormats(sortKeyName):
	"""Return links to writer plugins whose default sort is `sortKeyName`."""
	links = []
	for p in sorted(Glossary.plugins.values(), key=lambda p: p.lname):
		if not pluginIsActive(p):
			continue
		if not p.canWrite:
			continue
		if p.sortKeyName != sortKeyName:
			continue
		if p.sortOnWrite not in defaultWriteSortOnWrite:
			continue
		links.append(f"[{p.description}](./p/{p.lname}.md)")
	if sortKeyName == defaultSortKeyName:
		links.insert(0, "All other formats (given `--sort`)")
	return ", ".join(links)


rows = [
	(
		"Name/Value",
		"Description",
		"Default for formats",
		"Supports locale",
	),
]
rows += [
	(
		codeValue(item.name),
		item.desc,
		defaultForFormats(item.name),
		yesNo(item.locale is not None),
	)
	for item in namedSortKeyList
]

sortKeyTable = renderTable(
	rows,
	align=["left", "left", "left", "center"],
)

text = template.render(
	sortKeyTable=sortKeyTable,
	localeIntro=localeIntro,
)
with open(
	join(rootDir, "doc", "sort-key.md"),
	mode="w",
	encoding="utf-8",
) as _file:
	_file.write(text)
