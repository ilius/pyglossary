#!/usr/bin/env python
# mypy: ignore-errors
"""
Git external diff driver for glossary files.

Git runs this (via ``scripts/git-diff-glossary``) as the ``command`` of a diff
driver, with the arguments:

	path old-file old-hex old-mode new-file new-hex new-mode

Added and deleted files are rendered with ``view_glossary``; modified files
are compared entry by entry with ``diff_glossary``.
"""

from __future__ import annotations

import atexit
import os
import os.path
import sys

from .diff_glossary import diffGlossary
from .view_glossary import viewGlossary

__all__ = ["gitDiffMain", "main"]


# NOTE: make sure to set GIT_PAGER or config core.pager
# for example GIT_PAGER=less
# or GIT_PAGER='less -R -S -N'
def gitDiffMain() -> None:
	# print(sys.argv[1:])
	# arguments:
	# path old_file old_hex old_mode new_file new_hex new_mode
	path = sys.argv[1]
	oldFile = sys.argv[2]
	oldHex = sys.argv[3][:7]
	newFile = sys.argv[5]
	newHex = sys.argv[6][:7]

	if oldFile == os.devnull:
		print(f"{'_' * 80}\n\n### New file: {path}  ({newHex})\n", end="")
		viewGlossary(newFile, pager=False)
		return

	if newFile == os.devnull:
		print(f"{'_' * 80}\n\n### Deleted file: {path}  ({oldHex})\n", end="")
		viewGlossary(oldFile, pager=False)
		return

	header = f"{'_' * 80}\n\n### File: {path}  ({oldHex}..{newHex})\n"

	resDir = path + "_res"
	if os.path.isdir(resDir):
		resDirTmp = oldFile + "_res"
		os.symlink(os.path.realpath(resDir), resDirTmp)
		atexit.register(os.remove, resDirTmp)

	diffGlossary(
		oldFile,
		path,
		format1=None,
		format2=None,
		pager=False,
		header=header,
	)


def main() -> None:
	gitDiffMain()


if __name__ == "__main__":
	main()
