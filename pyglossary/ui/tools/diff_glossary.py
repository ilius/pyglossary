#!/usr/bin/env python
# mypy: ignore-errors
from __future__ import annotations

import atexit
import difflib
import os
import os.path
import shlex
import sys
from subprocess import PIPE, Popen
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.glossary_v2 import Glossary
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

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType

__all__ = ["diffGlossary"]

Glossary.init()

log.setVerbosity(1)

entrySep = f"\n{'_' * 40}\n\n"

noInfo = os.getenv("GLOSSARY_DIFF_NO_INFO") == "1"


def formatInfoValueDiff(diff: Iterator[str]) -> str:
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


def diffGlossary(  # noqa: PLR0912, PLR0913
	filename1: str,
	filename2: str,
	format1: str | None = None,
	format2: str | None = None,
	header: str = "",
	pager: bool = True,
) -> None:
	glos1 = Glossary(ui=None)
	if not glos1.directRead(filename1, formatName=format1):
		return

	glos2 = Glossary(ui=None)

	if not glos2.directRead(filename2, formatName=format2):
		return

	if pager:
		pagerCmd = ["less", "-R"]
		if os.getenv("PAGER"):
			pagerCmd = shlex.split(os.getenv("PAGER"))
		proc = Popen(
			pagerCmd,
			stdin=PIPE,
		)

		def write(msg: str):
			proc.stdin.write(msg.encode("utf-8"))

	else:
		proc = None

		def write(msg: str):
			print(msg, end="")

	if header:
		write(header + "\n")

	iter1 = iter(glos1)
	iter2 = iter(glos2)

	# infoIter1 = iter(sorted(glos1.iterInfo()))
	# infoIter2 = iter(sorted(glos2.iterInfo()))

	if noInfo:
		infoIter1 = iter([])
		infoIter2 = iter([])
	else:
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

	def printEntry(color: str, prefix: str, index: int, entry: EntryType) -> None:
		formatted = (
			f"{color}{prefix}#{index} "
			+ formatEntry(entry).replace("\n", "\n" + color)
			+ entrySep
		)
		write(formatted)

	def printInfo(color: str, prefix: str, pair: tuple[str, str]) -> None:
		key, value = pair
		spaces = " " * (len(prefix) + 7)
		valueColor = color + spaces + value.replace("\n", "\n" + spaces + color)
		formatted = f"{color}{prefix} Info: {key}\n{valueColor}" + entrySep
		write(formatted)

	def printChangedEntry(entry1: EntryType, entry2: EntryType) -> None:
		defiDiff = formatDiff(xmlDiff(entry1.defi, entry2.defi))
		entry1._defi = defiDiff
		if index1 < 0:
			ids = ""
		elif index1 == index2:
			ids = f"#{index1}"
		else:
			ids = f"A#{index1} B#{index2}"
		formatted = f"=== {yellow}{ids}{reset} " + formatEntry(entry1) + entrySep
		write(formatted)

	def printChangedInfo(key: str, value1: str, value2: str) -> str:
		valueDiff = formatInfoValueDiff(xmlDiff(value1, value2))
		printInfo(yellow, "=== ", (key, valueDiff))

	infoPair1 = None
	infoPair2 = None

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

	def printAltsChangedEntry(
		entry1: EntryType,
		entry2: EntryType,
		showDefi: bool = True,
	) -> None:
		ids = f"#{index1}" if index1 == index2 else f"A#{index1} B#{index2}"

		header = f"=== {yellow}{ids}{reset} "

		altsDiff = difflib.ndiff(
			[f"Alt: {alt}\n" for alt in entry1.l_word[1:]],
			[f"Alt: {alt}\n" for alt in entry2.l_word[1:]],
			linejunk=None,
			charjunk=None,
		)
		if entry1.l_word[0] == entry2.l_word[0]:
			firstWordLine = f">> {entry1.l_word[0]}"
		else:
			firstWordLine = f">> {entry1.l_word[0]} (A)\n>> {entry2.l_word[0]} (B)"
		entryFormatted = "\n".join(
			[
				firstWordLine,
				formatDiff(altsDiff),
				entry1.defi if showDefi else "",
			],
		)
		formatted = header + entryFormatted + entrySep
		write(formatted)

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

		if entry1.defi == entry2.defi and (words1[0] in words2 or words2[0] in words1):
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

	def run():  # noqa: PLR0912
		nonlocal index1, index2

		while True:
			try:
				infoStep()
			except StopIteration:
				break
			except (OSError, BrokenPipeError):
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
			except (OSError, BrokenPipeError):
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

	try:
		run()
	except (OSError, BrokenPipeError):
		pass  # noqa: S110
	except Exception as e:
		print(e)
	finally:
		if proc:
			proc.communicate()
			# proc.wait()
			# proc.terminate()
			sys.stdin.flush()
			sys.stdout.flush()


# NOTE: make sure to set GIT_PAGER or config core.pager
# for example GIT_PAGER=less
# or GIT_PAGER='less -R -S -N'
def gitDiffMain() -> None:
	# print(sys.argv[1:])
	# arguments:
	# path old_file old_hex old_mode new_file new_hex new_mode
	old_hex = sys.argv[3][:7]
	new_hex = sys.argv[6][:7]

	filename1 = sys.argv[2]
	filename2 = sys.argv[1]
	header = f"{'_' * 80}\n\n### File: {filename2}  ({old_hex}..{new_hex})\n"

	resDir = filename2 + "_res"
	if os.path.isdir(resDir):
		resDirTmp = filename1 + "_res"
		os.symlink(os.path.realpath(resDir), resDirTmp)
		atexit.register(os.remove, resDirTmp)

	diffGlossary(
		filename1,
		filename2,
		format1=None,
		format2=None,
		pager=False,
		header=header,
	)


def main() -> None:
	import os

	if os.getenv("GIT_DIFF_PATH_COUNTER"):
		return gitDiffMain()

	filename1 = sys.argv[1]
	filename2 = sys.argv[2]
	format1 = None
	format2 = None
	if len(sys.argv) > 3:
		format1 = sys.argv[3]
	if len(sys.argv) > 4:
		format2 = sys.argv[4]
	filename1 = os.path.expanduser(filename1)
	filename2 = os.path.expanduser(filename2)
	diffGlossary(
		filename1,
		filename2,
		format1=format1,
		format2=format2,
		pager=True,
	)
	return None


if __name__ == "__main__":
	main()
