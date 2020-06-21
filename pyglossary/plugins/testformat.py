# -*- coding: utf-8 -*-

from formats_common import *

enable = False
format = "Test"
description = "Test Format File(.test)"
extensions = [".test", ".tst"]

# key is option/argument name, value is instance of Option
optionsProp = {}

depends = {}


def read(glos: GlossaryType, filename: str) -> bool:
	log.info(f"reading from format {format} using plugin")
	count = 100
	# get number of entries from input file(depending on your format)
	for i in range(count):
		# here get word and definition from file(depending on your format)
		word = f"word_{i}"
		defi = f"definition {i}"
		glos.addEntry(word, defi)
	# here read info from file and set to Glossary object
	glos.setInfo("name", "Test")
	glos.setInfo("description", "Test glossary craeted by a PyGlossary plugin")
	glos.setInfo("author", "Me")
	glos.setInfo("copyright", "GPL")
	return True  # reading input file was succesfull


def write(glos: GlossaryType, filename: str) -> bool:
	log.info(f"writing to format {format} using plugin")
	for entry in glos:
		word = entry.getWord()
		defi = entry.getDefi()
		# here write word and defi to the output file (depending on
		# your format)
	# here read info from Glossaey object
	name = glos.getInfo("name")
	desc = glos.getInfo("description")
	author = glos.getInfo("author")
	copyright = glos.getInfo("copyright")
	# if an info key doesn't exist, getInfo returns empty string
	# now write info to the output file (depending on your output format)
	return True  # writing output file was succesfull
