# -*- coding: utf-8 -*-

from pyglossary.option import (
	BoolOption,
	IntOption,
	Option,
	StrOption,
)

__all__ = ["optionsProp"]


optionsProp: "dict[str, Option]" = {
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"discover": BoolOption(
		comment="Find and show unsupported tags",
	),
	"auto_rtl": BoolOption(
		allowNone=True,
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
	"example_padding": IntOption(
		comment="Padding for examples (in px)",
	),
}
