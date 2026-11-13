"""
FreeDict TEI reader option definitions.

Declares PyGlossary options for FreeDict import such as HTML output paths,
encoding, and TEI processing flags. Wired into the FreeDict plugin ``optionsProp``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import (
	BoolOption,
	IntOption,
	StrOption,
)

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = ["optionsProp"]


optionsProp: dict[str, Option] = {
	"auto_rtl": BoolOption(
		comment="Auto-detect and mark Right-to-Left text",
	),
	"auto_comma": BoolOption(
		comment="Auto-detect comma sign based on text",
	),
	"comma": StrOption(
		customValue=True,
		values=[", ", "، "],
		comment="Comma sign (following space) to use as separator",
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
	"usage_color": StrOption(
		comment="Usage label color",
	),
	"label_color": StrOption(
		comment="Label color",
	),
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
		minim=0,
		maxim=10000,
	),
}
