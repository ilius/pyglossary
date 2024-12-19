#!/usr/bin/env python
# mypy: ignore-errors
from __future__ import annotations

import argparse
import os.path
import shlex
import sys
from subprocess import PIPE, Popen
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

	from pyglossary.glossary_types import EntryType, GlossaryType

from pyglossary.core import log
from pyglossary.glossary_v2 import Glossary
from pyglossary.ui.tools.colors import reset, yellow
from pyglossary.ui.tools.format_entry import formatEntry

Glossary.init()

log.setVerbosity(1)

noColor = bool(os.getenv("NO_COLOR"))
if noColor:
	yellow = reset = ""  # noqa: F811


def getEntryHighlighter() -> Callable[[EntryType], None] | None:
	if noColor:
		return None
	try:
		import pygments  # noqa: F401
	except ModuleNotFoundError:
		return None

	from pygments import highlight
	from pygments.formatters import Terminal256Formatter as Formatter
	from pygments.lexers import HtmlLexer, XmlLexer

	formatter = Formatter()
	h_lexer = HtmlLexer()
	x_lexer = XmlLexer()

	def highlightEntry(entry: EntryType) -> None:
		entry.detectDefiFormat()
		if entry.defiFormat == "h":
			entry._defi = highlight(entry.defi, h_lexer, formatter)
			return
		if entry.defiFormat == "x":
			entry._defi = highlight(entry.defi, x_lexer, formatter)
			return

	return highlightEntry


def viewGlossary(
	filename: str,
	formatName: str | None = None,
	glos: GlossaryType | None = None,
	noRes: bool = False,
) -> None:
	highlightEntry = getEntryHighlighter()

	if glos is None:
		glos = Glossary(ui=None)

	if not glos.directRead(filename, formatName=formatName):
		return

	pagerCmd = ["less", "-R"]
	if os.getenv("PAGER"):
		pagerCmd = shlex.split(os.getenv("PAGER"))
	proc = Popen(
		pagerCmd,
		stdin=PIPE,
	)
	index = 0

	entrySep = "_" * 50

	def handleEntry(entry: EntryType) -> None:
		nonlocal index
		if noRes and entry.isData():
			return
		if highlightEntry:
			highlightEntry(entry)
		entryStr = (
			f"{yellow}#{index}{reset} " + formatEntry(entry) + "\n" + entrySep + "\n\n"
		)
		proc.stdin.write(entryStr.encode("utf-8"))
		if (index + 1) % 50 == 0:
			sys.stdout.flush()
		index += 1

	try:
		for entry in glos:
			try:
				handleEntry(entry)
			except (OSError, BrokenPipeError):
				break
	except (OSError, BrokenPipeError):
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
	parser = argparse.ArgumentParser(
		prog=sys.argv[0],
		add_help=True,
		# allow_abbrev=False,
	)
	parser.add_argument(
		"--format",
		dest="formatName",
		default=None,
		help="format name",
	)
	parser.add_argument(
		"--no-res",
		dest="noRes",
		action="store_true",
		default=False,
		help="do not automatically show resources / files",
	)
	parser.add_argument(
		"filename",
		action="store",
		default="",
		nargs=1,
	)
	args = parser.parse_args()

	viewGlossary(
		os.path.expanduser(args.filename[0]),
		formatName=args.formatName,
		noRes=args.noRes,
	)


if __name__ == "__main__":
	main()
