#!/usr/bin/python3

import sys
from importlib.metadata import PackageNotFoundError, distribution
from os.path import abspath, dirname
from pathlib import Path

import pip

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.glossary import Glossary

Glossary.init(
	usePluginsJson=False,
	skipDisabledPlugins=False,
)

userPluginsDirPath = Path(userPluginsDir)
plugins = [
	p for p in Glossary.plugins.values() if userPluginsDirPath not in p.path.parents
]

requirements = set()
for p in plugins:
	module = p.module
	# print(module.__file__)
	p.checkModule(module)
	p.checkModuleMore(module)
	requirements |= set(p.readDepends.values())
	requirements |= set(p.writeDepends.values())

for reqFull in requirements:
	name = reqFull.strip().split(">")[0]
	try:
		dist = distribution(name)
	except PackageNotFoundError:
		print(f"{name} is not installed, installing...")
		pip.main(["install", name])
		dist = distribution(name)
	assert name == dist.name, f"{name=}, {dist.name=}"
