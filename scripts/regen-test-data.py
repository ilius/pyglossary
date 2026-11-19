#!/usr/bin/env python3
"""
Re-convert expected ``.txt`` output fixtures in ``tests/data``.

Runs the glossary conversion tests with ``PYGLOSSARY_UPDATE_TEST_DATA=1``,
which makes ``compareTextFiles`` copy each produced ``.txt`` output over its
expected fixture instead of asserting equality. Conversion options come from
the tests themselves, so variants using read/write options are preserved.

Examples:
	python scripts/regen-test-data.py
	python scripts/regen-test-data.py g_xdxf_test g_freedict_test

"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT_DIR / "tests"


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"tests",
		nargs="*",
		help="test modules or test names to run (default: all top-level test files)",
	)
	parser.add_argument(
		"-p",
		"--pattern",
		default="*_test.py",
		help="glob pattern for top-level test files (default: *_test.py)",
	)
	parser.add_argument(
		"-v",
		"--verbose",
		action="store_true",
		help="show each test as it runs",
	)
	args = parser.parse_args()

	env = os.environ.copy()
	env["PYGLOSSARY_UPDATE_TEST_DATA"] = "1"
	pythonPath = [str(ROOT_DIR), str(TESTS_DIR)]
	if env.get("PYTHONPATH"):
		pythonPath.append(env["PYTHONPATH"])
	env["PYTHONPATH"] = os.pathsep.join(pythonPath)

	command = [sys.executable, "-m", "unittest"]
	if args.tests:
		command += args.tests
	else:
		command += sorted(
			path.name for path in TESTS_DIR.glob(args.pattern) if path.is_file()
		)
	if args.verbose:
		command.append("-v")

	print("Running:", " ".join(command))
	return subprocess.run(command, cwd=TESTS_DIR, env=env, check=False).returncode


if __name__ == "__main__":
	raise SystemExit(main())
