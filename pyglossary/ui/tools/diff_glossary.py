#!/usr/bin/env python

import difflib
import sys
from subprocess import PIPE, Popen
from typing import Iterator, Optional, Tuple

from pyglossary import Glossary
from pyglossary.entry import Entry
from pyglossary.glossary_type import EntryType
from pyglossary.ui.tools.colors import (
	green,
	red,
	reset,
	yellow,
)
from pyglossary.ui.tools.format_entry import formatEntry
from pyglossary.ui.tools.word_diff import (
	formatDiff,
	xmlDiff,
)

Glossary.init()


def formatInfoValueDiff(diff: "Iterator[str]") -> str:
	a = ""
	b = ""
	for part in diff:
		if part[0] == " ":
			a += part[2:]
			b += part[2:]
			continue
		if part[0] == "-":
			a += red + part[2:] + reset
			continue
		if part[0] == "+":
			b += green + part[2:] + reset
			continue
	return a + "\n" + b


def diffGlossary(
	filename1: str,
	filename2: str,
	format1: "Optional[str]" = None,
	format2: "Optional[str]" = None,
) -> None:
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

	# infoIter1 = iter(sorted(glos1.iterInfo()))
	# infoIter2 = iter(sorted(glos2.iterInfo()))

	infoIter1 = glos1.iterInfo()
	infoIter2 = glos2.iterInfo()

	index1 = -1
	index2 = -1

	def nextEntry1() -> None:
		nonlocal entry1, index1
		entry1 = next(iter1)
		index1 += 1

	def nextEntry2() -> None:
		nonlocal entry2, index2
		entry2 = next(iter2)
		index2 += 1

	def printEntry(color: str, prefix: str, index: int, entry: "EntryType") -> None:
		formatted = (
			f"{color}{prefix}#{index} " +
			formatEntry(entry).replace("\n", "\n" + color) +
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(formatted.encode("utf-8"))

	def printInfo(color: str, prefix: str, pair: "Tuple[str, str]") -> None:
		key, value = pair
		spaces = " " * (len(prefix) + 7)
		valueColor = color + spaces + value.replace("\n", "\n" + spaces + color)
		formatted = (
			f"{color}{prefix} Info: {key}\n"
			f"{valueColor}"
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(formatted.encode("utf-8"))

	def printChangedEntry(entry1: "EntryType", entry2: "EntryType") -> None:
		defiDiff = formatDiff(xmlDiff(entry1.defi, entry2.defi))
		entry1._defi = defiDiff
		if index1 < 0:
			ids = ""
		elif index1 == index2:
			ids = f"#{index1}"
		else:
			ids = f"A#{index1} B#{index2}"
		formatted = (
			f"=== {yellow}{ids}{reset} " +
			formatEntry(entry1) +
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(formatted.encode("utf-8"))


	def printChangedInfo(key: str, value1: str, value2: str) -> str:
		valueDiff = formatInfoValueDiff(xmlDiff(value1, value2))
		printInfo(yellow, "=== ", (key, valueDiff))


	infoPair1 = None
	infoPair2 = None

	def newInfoEntry(pair: "Tuple[str, str]") -> "EntryType":
		key, value = pair
		return Entry(f"Info: {key}", f"Value: {value}")

	def infoStep() -> None:
		nonlocal infoPair1, infoPair2
		if infoPair1 is None:
			infoPair1 = next(infoIter1)
		if infoPair2 is None:
			infoPair2 = next(infoIter2)

		if infoPair1 == infoPair2:
			infoPair1, infoPair2 = None, None
			return

		if infoPair1[0] == infoPair2[0]:
			printChangedInfo(infoPair1[0], infoPair1[1], infoPair2[1])
			infoPair1, infoPair2 = None, None
			return

		if infoPair1[0] < infoPair2[0]:
			printInfo(red, "--- A: ", infoPair1)
			infoPair1 = None
			return

		printInfo(green, "+++ B: ", infoPair2)
		infoPair2 = None

	def printAltsChangedEntry(entry1: "EntryType", entry2: "EntryType") -> None:
		if index1 == index2:
			ids = f"#{index1}"
		else:
			ids = f"A#{index1} B#{index2}"

		header = f"=== {yellow}{ids}{reset} "

		altsDiff = difflib.ndiff(
			[f"Alt: {alt}\n" for alt in entry1.l_word[1:]],
			[f"Alt: {alt}\n" for alt in entry2.l_word[1:]],
			linejunk=None,
			charjunk=None,
		)
		entryFormatted = "\n".join([
			f">>> {entry1.l_word[0]}",
			formatDiff(altsDiff),
			entry1.defi,
		])
		formatted = (
			header + entryFormatted +
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(formatted.encode("utf-8"))

	count = 0
	entry1 = None
	entry2 = None

	def step() -> None:
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

		if words1[0] == words2[0] and entry1.defi == entry2.defi:
			printAltsChangedEntry(entry1, entry2)
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
				infoStep()
			except StopIteration:
				break
			except (BrokenPipeError, IOError):
				break

		if infoPair1:
			printInfo(red, "--- A: ", infoPair1)
		if infoPair2:
			printInfo(green, "+++ B: ", infoPair2)

		for pair in infoIter1:
			printInfo(red, "--- A: ", pair)
		for pair in infoIter2:
			printInfo(green, "+++ B: ", pair)

		while True:
			try:
				step()
			except StopIteration:
				break
			except (BrokenPipeError, IOError):
				break

		if entry1:
			printEntry(red, "--- A", index1, entry1)
			index1 += 1
		if entry2:
			printEntry(green, "+++ B", index2, entry2)
			index2 += 1

		for entry in iter1:
			printEntry(red, "--- A", index1, entry)
			index1 += 1
		for entry in iter2:
			printEntry(green, "+++ B", index2, entry)
			index2 += 1
	except (BrokenPipeError, IOError):
		pass  # noqa: S110
	except Exception as e:
		print(e)
	finally:
		proc.communicate()
		# proc.wait()
		# proc.terminate()
		sys.stdin.flush()
		sys.stdout.flush()


def main() -> None:
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
