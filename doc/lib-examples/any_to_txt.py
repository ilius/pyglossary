#!/usr/bin/env python3

import sys

from pyglossary import Glossary

# Glossary.init() must be called only once, so make sure you put it
# in the right place
Glossary.init()

glos = Glossary()
glos.convert(
	inputFilename=sys.argv[1],
	outputFilename=f"{sys.argv[1]}.txt",
	# although it can detect format for *.txt, you can still pass outputFormat
	outputFormat="Tabfile",
	# you can pass readOptions or writeOptions as a dict
	# writeOptions={"encoding": "utf-8"},
)
