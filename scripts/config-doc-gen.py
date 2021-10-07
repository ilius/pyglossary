#!/usr/bin/python3

import sys
import json
from os.path import join, dirname, abspath
from pprint import pprint
from mako.template import Template

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import userPluginsDir
from pyglossary.ui.base import UIBase

ui = UIBase()
ui.loadConfig(user=False)

# ui.configDefDict

template = Template("""
${"## Configuration Parameters ##"}

Name | Command Flags | Type | Default | Comment
---- | ------------- | ---- | ------- | -------
% for name, opt in ui.configDefDict.items():
% if not opt.disabled:
`${name}` | ${cmdFlags[name]} | ${opt.typ} | ${codeValue(ui.config[name])} | ${opt.comment}
% endif
% endfor

${"## Configuration Files ##"}
The default configuration values are stored in [config.json](../config.json) file in source/installation directory.

The user configuration file - if exists - will override default configuration values.
The location of this file depends on the operating system:

- Linux or BSD: `~/.pyglossary/config.json`
- Mac: `~/Library/Preferences/PyGlossary/config.json`
- Windows: `C:\\Users\\USERNAME\\AppData\\Roaming\\PyGlossary\\config.json`
""")

def codeValue(x):
	s = str(x)
	if s:
		return "`" + s + "`"
	return ""


def getCommandFlagsMD(name, opt):
	if not opt.cmd:
		return ""
	flag = opt.cmdFlag
	if not flag:
		flag = name.replace('_', '-')

	if opt.falseComment:
		return f"`--{flag}`<br/>`--no-{flag}`"

	return f"`--{flag}`"


cmdFlags = {}

for name, opt in ui.configDefDict.items():
	cmdFlags[name] = getCommandFlagsMD(name, opt)

text = template.render(
	codeValue=codeValue,
	ui=ui,
	cmdFlags=cmdFlags,
)
with open(join("doc", "config.md"), mode="w") as _file:
	_file.write(text)

