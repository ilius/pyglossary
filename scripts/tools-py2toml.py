#!/usr/bin/python3

import sys
from collections import OrderedDict
from os.path import abspath, dirname, join
from pathlib import Path

import toml

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.glossary import Glossary

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
