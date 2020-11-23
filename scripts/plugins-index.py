#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from collections import OrderedDict as odict

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary

Glossary.init()

data = []
for p in Glossary.plugins.values():
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
with open("plugins.json", mode="w", encoding="utf-8") as _file:
	_file.write(jsonText)
