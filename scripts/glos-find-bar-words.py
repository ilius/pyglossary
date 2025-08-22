#!/usr/bin/python3

import sys
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary import Glossary


def hasBar(entry):
	return any("|" in word for word in entry.l_term)


Glossary.init(
	# usePluginsJson=False,
)

for direct in (True, False):
	print(f"\n-------- {direct=}")

	glos = Glossary()
	glos.config = {
		"enable_alts": True,
	}
	glos.read(
		filename=sys.argv[1],
		direct=direct,
	)
	for entry in glos:
		if hasBar(entry):
			print(f"+++ {entry.l_term!r} -> {entry.defi[:60]}")
			continue

		# print(f"--- {entry.l_term!r} -> {entry.defi[:60]}")
