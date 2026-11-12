#!/usr/bin/env python3
"""
Report (or fix) the numeric entry-count prefix of a test fixture.

Example:
	python scripts/fixture-count.py tests/data/14-en-en.tei --rename

"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pyglossary.glossary_v2 import Glossary

PREFIX_RE = re.compile(r"^(\d+)(-.*)$")


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("path", help="fixture file to inspect")
	parser.add_argument(
		"--format",
		default=None,
		help="reader format name (auto-detected from extension by default)",
	)
	parser.add_argument(
		"--rename",
		action="store_true",
		help="rename the file so its prefix matches the actual entry count",
	)
	args = parser.parse_args()

	path = Path(args.path)
	Glossary.init()
	glos = Glossary(ui=None)
	if not glos.directRead(str(path), formatName=args.format):
		print(f"failed to read {path}", file=sys.stderr)
		return 1

	count = sum(1 for _ in glos)
	m = PREFIX_RE.match(path.name)
	if not m:
		print(f"{path}: {count} entries (no numeric prefix)")
		return 0

	old_prefix, rest = m.groups()
	expected = str(count).zfill(len(old_prefix))
	target = path.with_name(expected + rest)
	if old_prefix == expected:
		print(f"{path}: OK ({count} entries)")
		return 0

	print(f"{path}: prefix {old_prefix} != {count} entries; expected {target.name}")
	if args.rename:
		path.rename(target)
		print(f"renamed to {target}")
		return 0
	return 1


if __name__ == "__main__":
	raise SystemExit(main())
