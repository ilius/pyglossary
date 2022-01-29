#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from pathlib import Path
from collections import OrderedDict
import toml
from pprint import pprint

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from pyglossary.core import userPluginsDir

Glossary.init(
	# usePluginsJson=False,
)

userPluginsDirPath = Path(userPluginsDir)
plugins = [
	p
	for p in Glossary.plugins.values()
	if userPluginsDirPath not in p.path.parents
]

toolsDir = join(rootDir, "plugins-meta", "tools")

for p in plugins:
	module = p.module
	optionsProp = p.optionsProp

	tools = OrderedDict()
	for tool in getattr(p.module, "tools", []):
		tools[tool.pop("name")] = tool

	# if not tools:
	# 	continue

	# pprint(tools)

	with open(join(toolsDir, f"{p.lname}.toml"), mode="w") as _file:
		toml.dump(tools, _file)


