"""
PyGlossary XDXF reader option definitions.

Declares PyGlossary options for XDXF import such as HTML output and
pronunciation formatting. Wired into the XDXF plugin ``optionsProp``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import BoolOption, IntOption, StrOption

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = ["optionsProp"]


optionsProp: dict[str, Option] = {
	"html": BoolOption(comment="Entries are HTML"),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
	"auto_rtl": BoolOption(
		comment="Auto-detect and mark Right-to-Left text",
	),
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
		minim=0,
		maxim=10000,
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
	"pron_color": StrOption(
		comment="Pronunciation color",
	),
	"gram_color": StrOption(
		comment="Grammar color",
	),
}
