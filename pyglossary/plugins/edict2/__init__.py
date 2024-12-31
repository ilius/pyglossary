from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)

from .reader import Reader

__all__ = [
	"Reader",
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
lname = "edict2"
name = "EDICT2"
description = "EDICT2 (CEDICT) (.u8)"
extensions = (".u8",)
extensionCreate = ""
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/CEDICT"
website = None

# Websites / info for different uses of format:

# CC-CEDICT: Chinese-English (122k entries)
# "https://cc-cedict.org/editor/editor.php", "CC-CEDICT Editor"

# HanDeDict: Chinese-German (144k entries)
# "https://handedict.zydeo.net/de/download",
# "Herunterladen - HanDeDict @ Zydeo Wörterbuch Chinesisch-Deutsch"

# CFDICT: Chinese-French (56k entries)
# "https://chine.in/mandarin/dictionnaire/CFDICT/",
# "Dictionnaire chinois français _ 汉法词典 — Chine Informations"

# CC-Canto is Pleco Software's addition of Cantonese language readings
# in Jyutping transcription to CC-CEDICT
# "https://cantonese.org/download.html",

optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"traditional_title": BoolOption(
		comment="Use traditional Chinese for entry titles/keys",
	),
	"colorize_tones": BoolOption(
		comment="Set to false to disable tones coloring",
	),
}
