# Copyright (C) 2026 glowinthedark
#
# SPDX-License-Identifier: GPL-3.0-or-later

r"""
wudict markdown: one dictionary in standard CommonMark (https://github.com/wuweidict/wudict/blob/master/docs/WUDICT-MARKDOWN.md).

As a user plugin, this folder goes in pyglossary's plugin folder:
~/Library/Preferences/PyGlossary/plugins/ on macOS, ~/.pyglossary/plugins/ on
Linux, %APPDATA%\PyGlossary\plugins\ on Windows. Needs markdown-it-py.
"""

from __future__ import annotations

from pyglossary.option import BoolOption, StrOption

from .reader import Reader
from .writer import Writer

__all__ = [
	"Reader",
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "wudict_md"
name = "WudictMarkdown"
description = "wudict markdown (.wudict.md)"
# pyglossary matches the last extension, so `.wudict.md` is found as `.md`; a
# `.md` that is not a WuDict dictionary is refused when it is opened.
extensions = (".md",)
extensionCreate = ".wudict.md"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/wuweidict/wudict/blob/master/docs/WUDICT-MARKDOWN.md",
	"WuDict markdown",
)

optionsProp = {
	"mode": StrOption(
		values=["html", "clean"],
		comment="html (default): each article's HTML kept; clean: markdown only, lossy",
	),
	"resources": BoolOption(comment="Read and write resources (<name>.wudict.files)"),
}

docTail = """One dictionary per file: `# Title`, then `wudict: 1` on line 2, then
`key: value` header lines. Each entry is a `## headword` heading, with its
other spellings as more `##` headings right under it; its body is standard
markdown. See docs/WUDICT-MARKDOWN.md in the wudict repository."""
