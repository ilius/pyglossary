#!/usr/bin/python3

import sys
import tomllib as toml
from os.path import abspath, dirname
from pathlib import Path

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


moduleNames = {
	"prompt_toolkit",  # used for interactive cli
}
# "tqdm" used for progressbar if installed
# "python-idzip" is used as dictzip for StarDict if installed
for p in plugins:
	moduleNames |= set(p.readDepends)
	moduleNames |= set(p.writeDepends)


with open("pyproject.toml", mode="rb") as file:
	project = toml.load(file)

import_analyzer = project["tool"]["import-analyzer"]
exclude_toplevel_module: list[str] = import_analyzer["exclude_toplevel_module"]
# print(exclude_toplevel_module)

for modName in moduleNames:
	assert modName in exclude_toplevel_module, modName
