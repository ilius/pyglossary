#!/usr/bin/env python3

import sys
from os.path import abspath, dirname, join

from packaging.version import parse


def main():
	version = sys.argv[1]
	parse(version)
	versionQuoted = f'"{version}"'
	rootDir = dirname(dirname(abspath(__file__)))
	replaceVar(join(rootDir, "pyglossary/core.py"), "VERSION", versionQuoted)
	replaceVar(join(rootDir, "setup.py"), "VERSION", versionQuoted)
	replaceVar(join(rootDir, "pyproject.toml"), "version", versionQuoted)


def replaceVar(fname: str, name: str, value: str) -> None:
	prefix = name + " = "
	lines = []
	with open(fname, encoding="utf-8") as _file:
		for _line in _file:
			line = _line
			if line.startswith(prefix):
				line = f"{name} = {value}\n"
			lines.append(line)
	with open(fname, mode="w", encoding="utf-8") as _file:
		_file.writelines(lines)


main()
