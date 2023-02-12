#!/usr/bin/env python

import os
import signal
import sys
from subprocess import PIPE, Popen

from pyglossary import Glossary
from pyglossary.ui.tools.format_entry import formatEntry
from pyglossary.ui.tools.word_diff import *

Glossary.init()


def diffGlossary(filename1, filename2, format1=None, format2=None):
	glos1 = Glossary(ui=None)
	if not glos1.read(filename1, format=format1, direct=True):
		return

	glos2 = Glossary(ui=None)

	if not glos2.read(filename2, format=format2, direct=True):
		return

	proc = Popen(
		[
			"less",
			"-R",
		],
		stdin=PIPE,
	)

	iter1 = iter(glos1)
	iter2 = iter(glos2)

	index1 = -1
	index2 = -1

	def nextEntry1():
		nonlocal entry1, index1
		entry1 = next(iter1)
		index1 += 1

	def nextEntry2():
		nonlocal entry2, index2
		entry2 = next(iter2)
		index2 += 1

	def printEntry(color: str, prefix: str, index: int, entry: "EntryType"):
		str = (
			f"{color}{prefix}#{index} " +
			formatEntry(entry).replace("\n", "\n" + color) +
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(str.encode("utf-8"))

	def printChangedEntry(entry1, entry2):
		defiDiff = formatDiff(xmlDiff(entry1.defi, entry2.defi))
		entry1._defi = defiDiff
		if index1 == index2:
			ids = f"#{index1}"
		else:
			ids = f"A#{index1} B#{index2}"
		str = (
			f"=== {yellow}{ids}{reset} " +
			formatEntry(entry1) +
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(str.encode("utf-8"))

	count = 0
	entry1 = None
	entry2 = None

	def step():
		nonlocal count, entry1, entry2
		if entry1 is None:
			nextEntry1()
		if entry2 is None:
			nextEntry2()

		words1 = entry1.l_word
		words2 = entry2.l_word
		if words1 == words2:
			if entry1.defi == entry2.defi:
				entry1, entry2 = None, None
				return
			printChangedEntry(entry1, entry2)
			entry1, entry2 = None, None
			return

		if words1 < words2:
			printEntry(red, "--- A", index1, entry1)
			entry1 = None
		else:
			printEntry(green, "+++ B", index2, entry2)
			entry2 = None

		if (count + 1) % 50 == 0:
			sys.stdout.flush()
		count += 1

	try:
		while True:
			try:
				step()
			except StopIteration:
				break
			except (BrokenPipeError, IOError):
				break
		for entry in iter1:
			printEntry(red, "--- A", index1, entry)
			index1 += 1
		for entry in iter2:
			printEntry(green, "+++ B", index2, entry)
			index2 += 1
	except (BrokenPipeError, IOError):
		pass  # noqa
	except Exception as e:
		print(e)
	finally:
		proc.communicate()
		# proc.wait()
		# proc.terminate()
		sys.stdin.flush()
		sys.stdout.flush()


def main():
	filename1 = sys.argv[1]
	filename2 = sys.argv[2]
	format1 = None
	format2 = None
	if len(sys.argv) > 3:
		format1 = sys.argv[3]
	if len(sys.argv) > 4:
		format2 = sys.argv[4]
	diffGlossary(filename1, filename2, format1=format1, format2=format2)


if __name__ == "__main__":
	main()
