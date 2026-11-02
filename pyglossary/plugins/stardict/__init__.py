"""
PyGlossary StarDict format plugin.

Directory-based StarDict glossaries identified by an ``.ifo`` index file plus
``.idx``/``.dict``/``.syn`` companions. Supports reading and writing with
sort-on-write, dictzip compression, SQLite buffering, and XDXF-to-HTML options.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pyglossary.flags import ALWAYS, DEFAULT_YES
from pyglossary.option import (
	BoolOption,
	FileSizeOption,
	StrOption,
)

from .reader import Reader
from .writer import Writer

if TYPE_CHECKING:
	from pyglossary.option import Option

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
lname = "stardict"
name = "Stardict"
description = "StarDict (.ifo)"
extensions = (".ifo",)
extensionCreate = "-stardict/"
singleFile = False
sortOnWrite = ALWAYS
sortKeyName = "stardict"
sortEncoding = "utf-8"

kind = "directory"
wiki = "https://en.wikipedia.org/wiki/StarDict"
website = (
	"http://huzheng.org/stardict/",
	"huzheng.org/stardict",
)
relatedFormats: list[str] = ["StardictTextual", "StardictMergeSyns"]

docTail = """\
### StarDict program HTML support

The StarDict application renders HTML definitions with a very limited engine
(its `stardict-html-parsedata-plugin`). It only understands these tags:

- inline formatting: `b`, `big`, `i`, `s`, `sub`, `sup`, `small`, `tt`, `u`,
  `font` (`face` and `color` attributes)
- line breaks: `br` (literal `<br>` only) and `hr`
- links and images: `a` (`href`), `img` (`src`)

All other tags — including `div`, `p`, `span`, `ol`, `li`, `blockquote`,
`table` and headings — are dropped and their content is rendered inline. As a
result:

- line breaks and block boundaries (keyword, sibling definitions, examples)
  are lost,
- ordered and unordered lists are not numbered or bulleted,
- `blockquote` indentation is not applied,
- the self-closing `<br/>` form is **not** recognized as a line break.
  PyGlossary emits `<br/>` by default, so explicit line breaks are dropped
  unless the `stardict_client` option is enabled, which rewrites them as
  `<br>` before writing,
- inline formatting (bold, italic, underline, sub/superscript, `font` color)
  is preserved.

This matters for `sametypesequence=h` (HTML) and `sametypesequence=x` (XDXF)
entries, which PyGlossary converts to HTML on read (see the `xdxf_to_html`
option). That HTML relies on `div`, `ol`/`li` and `<br/>` for layout, so
entries will look degraded in the StarDict program even with `stardict_client`
enabled (it only fixes line breaks). Viewers that support a larger HTML subset,
such as GoldenDict or AyanDict, are recommended instead.

See the
[StarDict HTML parsing plugin source](https://github.com/huzheng001/stardict-3/blob/master/dict/stardict-plugins/stardict-html-parsedata-plugin/stardict_html_parsedata.cpp).
"""

# https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat
optionsProp: dict[str, Option] = {
	"large_file": BoolOption(
		comment="Use idxoffsetbits=64 bits, for large files only",
	),
	"max_file_size": FileSizeOption(
		comment=(
			"Max .dict file size before splitting into multiple glossaries;\n"
			"0 means use default based on large_file (4 GiB or 64-bit limit).\n"
			" Examples: 100m, 1g"
		),
	),
	"stardict_client": BoolOption(
		comment="Modify html entries for StarDict 3.0",
	),
	"dictzip": BoolOption(
		comment="Compress .dict file to .dict.dz",
	),
	"dictzip_syn": BoolOption(
		comment="Compress .syn file to .syn.dz",
	),
	"sametypesequence": StrOption(
		values=["", "h", "m", "x", "-"],
		comment="Definition format: h=html, m=plaintext, x=xdxf",
	),
	"xdxf_to_html": BoolOption(
		comment="Convert XDXF entries to HTML",
	),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
	"unicode_errors": StrOption(
		values=[
			"strict",  # raise a UnicodeDecodeError exception
			"ignore",  # just leave the character out
			"replace",  # use U+FFFD, REPLACEMENT CHARACTER
			"backslashreplace",  # insert a \xNN escape sequence
		],
		comment="What to do with Unicode decoding errors",
	),
	"audio_goldendict": BoolOption(
		comment="Convert audio links for GoldenDict (desktop)",
	),
	"audio_icon": BoolOption(
		comment="Add glossary's audio icon",
	),
	"autosqlite": BoolOption(
		comment="Auto-enable/disable SQLite option based on global SQLite mode.",
	),
	"sqlite": BoolOption(
		comment="Use SQLite to limit memory usage.",
	),
}

if os.getenv("PYGLOSSARY_STARDICT_NO_FORCE_SORT") == "1":
	sortOnWrite = DEFAULT_YES
