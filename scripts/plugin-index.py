#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from collections import OrderedDict as odict
from pathlib import Path

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from pyglossary.core import userPluginsDir

Glossary.init()

userPluginsDirPath = Path(userPluginsDir)
plugins = [
	p
	for p in Glossary.plugins.values()
	if userPluginsDirPath not in p.path.parents
]

data = []
for p in plugins:
	canRead = p.canRead
	canWrite = p.canWrite
	item = odict([
		("name", p.name),
		("description", p.description),
		("extensions", p.extensions),
		("singleFile", p.singleFile),
		("optionsProp", {
			name: opt.toDict()
			for name, opt in p.optionsProp.items()
		}),
		("canRead", canRead),
		("canWrite", canWrite),
	])
	if canRead:
		item["readOptions"] = p.getReadOptions()
	if canWrite:
		item["writeOptions"] = p.getWriteOptions()
	data.append(item)


jsonText = json.dumps(
	data,
	sort_keys=False,
	indent="\t",
	ensure_ascii=False,
)
with open(
	join(rootDir, "plugins-meta", "index.json"),
	mode="w",
	encoding="utf-8",
) as _file:
	_file.write(jsonText)
