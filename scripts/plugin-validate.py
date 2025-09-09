#!/usr/bin/python3
from __future__ import annotations

import subprocess
import sys
from importlib.metadata import PackageNotFoundError, distribution
from os.path import abspath, dirname
from pathlib import Path
from typing import TYPE_CHECKING

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)


from pyglossary.core import userPluginsDir
from pyglossary.glossary import Glossary

if TYPE_CHECKING:
	from importlib.metadata import Distribution

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


def getPackageDistribution(name: str) -> Distribution:
	try:
		return distribution(name)
	except PackageNotFoundError:
		pass
	print(f"{name} is not installed, installing...")
	subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", name])
	return distribution(name)


for reqFull in requirements:
	name = reqFull.strip().split(">")[0]
	dist = getPackageDistribution(name)
	assert name == dist.name, f"{name=}, {dist.name=}"
