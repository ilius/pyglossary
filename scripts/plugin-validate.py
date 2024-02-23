#!/usr/bin/python3

import sys
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

data = []
for p in plugins:
    module = p.module
    # print(module.__file__)
    p.checkModule(module)
    p.checkModuleMore(module)
