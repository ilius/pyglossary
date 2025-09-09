#!/usr/bin/python3

import sys
from importlib.metadata import distribution
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

depSet = {
	"prompt_toolkit",  # used for interactive cli
}
# "tqdm" used for progressbar if installed
# "python-idzip" is used as dictzip for StarDict if installed
for p in plugins:
	depSet |= set(p.readDepends.values())
	depSet |= set(p.writeDepends.values())

for dep in depSet:
	name = dep.strip().split(">")[0]
	distName = distribution(name).name
	assert name == distName, f"{name=}, {distName=}"

with open("requirements.txt", "w", encoding="utf-8") as file:
	file.writelines(name + "\n" for name in sorted(depSet))
