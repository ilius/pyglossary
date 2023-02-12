#!/usr/bin/python3

import json
import sys
from collections import OrderedDict as odict
from os.path import abspath, dirname, join
from pathlib import Path

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.flags import DEFAULT_NO
from pyglossary.glossary import Glossary

Glossary.init(
	usePluginsJson=False,
	skipDisabledPlugins=False,
)

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
		("module", p.module.__name__),
		("lname", p.lname),
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
	if p.sortOnWrite != DEFAULT_NO:
		item["sortOnWrite"] = p.sortOnWrite
	if p.sortKeyName:
		item["sortKeyName"] = p.sortKeyName
	if canRead:
		item["readOptions"] = p.getReadOptions()
	if canWrite:
		item["writeOptions"] = p.getWriteOptions()
	if not p.enable:
		item["enable"] = False
	if p.readDepends:
		item["readDepends"] = p.readDepends
	if p.writeDepends:
		item["writeDepends"] = p.writeDepends
	if p.readCompressions:
		item["readCompressions"] = p.readCompressions

	data.append(item)


jsonText = json.dumps(
	data,
	sort_keys=False,
	indent="\t",
	ensure_ascii=True,
)
with open(
	join(rootDir, "plugins-meta", "index.json"),
	mode="w",
	encoding="utf-8",
) as _file:
	_file.write(jsonText)
