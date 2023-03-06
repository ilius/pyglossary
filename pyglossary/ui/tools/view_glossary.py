#!/usr/bin/env python

import sys
from subprocess import PIPE, Popen
from typing import Callable, Optional

from pyglossary.glossary_type import EntryType
from pyglossary.glossary_v2 import Glossary
from pyglossary.ui.tools.colors import reset, yellow
from pyglossary.ui.tools.format_entry import formatEntry

Glossary.init()


def viewGlossary(filename: str, format: "Optional[str]" = None) -> None:
	highlightEntry: "Optional[Callable[[EntryType], None]]" = None
	try:
		import pygments  # noqa: F401
	except ModuleNotFoundError:
		pass
	else:
		from pygments import highlight
		from pygments.formatters import Terminal256Formatter as Formatter
		from pygments.lexers import HtmlLexer, XmlLexer

		formatter = Formatter()
		h_lexer = HtmlLexer()
		x_lexer = XmlLexer()

		def highlightEntry(entry: "EntryType") -> None:
			entry.detectDefiFormat()
			if entry.defiFormat == "h":
				entry._defi = highlight(entry.defi, h_lexer, formatter)
				return
			if entry.defiFormat == "x":
				entry._defi = highlight(entry.defi, x_lexer, formatter)
				return

	glos = Glossary(ui=None)

	if not glos.directRead(filename, format=format):
		return

	proc = Popen(
		[
			"less",
			"-R",
		],
		stdin=PIPE,
	)
	index = 0

	def handleEntry(entry: "EntryType") -> None:
		nonlocal index
		if highlightEntry:
			highlightEntry(entry)
		str = (
			f"{yellow}#{index}{reset} " +
			formatEntry(entry) +
			"\n______________________________________________\n\n"
		)
		proc.stdin.write(str.encode("utf-8"))
		if (index + 1) % 50 == 0:
			sys.stdout.flush()
		index += 1

	try:
		for entry in glos:
			try:
				handleEntry(entry)
			except (BrokenPipeError, IOError):
				break
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
	filename = sys.argv[1]
	format = None
	if len(sys.argv) > 2:
		format = sys.argv[2]
	viewGlossary(filename, format=format)


if __name__ == "__main__":
	main()
