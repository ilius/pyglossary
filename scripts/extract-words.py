#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Extracts words from entry terms from all glossaries inside a given directory.
Sorts them and writes them to words.txt
"""

import os
import sys
from collections.abc import Iterable
from os.path import join

from pyglossary.glossary_v2 import Error, Glossary

Glossary.init()

stripChars = " 0123456789!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~“”،؛؟۔￼↑"  # noqa: RUF001


def listFilesRecursive(direc: str, exclude: set[str]) -> Iterable[str]:
	"""
	Iterate over full paths of all files (directly/indirectly)
	inside given directory.
	"""
	for root, dirs, files in os.walk(direc, topdown=True):
		[dirs.remove(d) for d in list(dirs) if d in exclude]
		for fname in files:
			yield join(root, fname)


searchDir = "."
if len(sys.argv) > 1:
	searchDir = sys.argv[1]

words = set()

for fpath in listFilesRecursive(searchDir, {"res"}):
	try:
		inputArgs = Glossary.detectInputFormat(fpath)
	except Error:
		continue
	glos = Glossary()
	print("reading", inputArgs.filename)
	glos.directRead(inputArgs.filename)
	for entry in glos:
		if entry.isData():
			continue
		for term in entry.l_term:
			for word in term.split(" "):
				word2 = word.strip(stripChars)
				if word2:
					words.add(word2)


with open("words.txt", "w", encoding="utf-8") as file:
	file.writelines(word + "\n" for word in sorted(words))
