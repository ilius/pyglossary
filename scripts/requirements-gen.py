#!/usr/bin/python3

import sys
import tomllib as toml
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

requirements = {
	"prompt_toolkit",  # used for interactive cli
}
moduleNames = {
	"prompt_toolkit",  # used for interactive cli
}
# "tqdm" used for progressbar if installed
# "python-idzip" is used as dictzip for StarDict if installed
for p in plugins:
	requirements |= set(p.readDepends.values())
	requirements |= set(p.writeDepends.values())
	moduleNames |= set(p.readDepends)
	moduleNames |= set(p.writeDepends)

for reqFull in requirements:
	name = reqFull.strip().split(">")[0]
	try:
		dist = distribution(name)
	except PackageNotFoundError:
		print(f"{name} is not installed, installing...")
		pip.main(["install", name])
		dist = distribution(name)
	assert name == dist.name, f"{name=}, {dist.name=}"

with open("requirements.txt", "w", encoding="utf-8") as file:
	file.writelines(name + "\n" for name in sorted(requirements))


with open("pyproject.toml", mode="rb") as file:
	project = toml.load(file)

import_analyzer = project["tool"]["import-analyzer"]
exclude_toplevel_module: list[str] = import_analyzer["exclude_toplevel_module"]
# print(exclude_toplevel_module)

for modName in moduleNames:
	assert modName in exclude_toplevel_module, modName
