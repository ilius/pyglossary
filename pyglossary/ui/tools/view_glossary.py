#!/usr/bin/env python

import sys
from subprocess import PIPE, Popen
from typing import Optional

from pyglossary import Glossary
from pyglossary.glossary_type import EntryType
from pyglossary.ui.tools.colors import reset, yellow
from pyglossary.ui.tools.format_entry import formatEntry

Glossary.init()


def viewGlossary(filename: str, format: "Optional[str]" = None) -> None:
	glos = Glossary(ui=None)

	if not glos.read(filename, format=format, direct=True):
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
