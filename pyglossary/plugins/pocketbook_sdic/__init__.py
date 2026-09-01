"""
PyGlossary PocketBook SDIC format plugin.

PocketBook ``.dic`` SDIC dictionaries for e-ink devices. Write-only ``Writer``
packages sorted entries into the PocketBook SDIC binary layout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.flags import NEVER
from pyglossary.option import StrOption

from .writer import Writer

if TYPE_CHECKING:
	from pyglossary.option import Option

__all__ = [
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
lname = "pocketbook_sdic"
name = "PocketBookSdic"
description = "PocketBook SDIC (.dic)"
extensions = (".dic",)
extensionCreate = ".dic"
singleFile = True
sortOnWrite = NEVER
kind = "binary"
wiki = ""
website = None

optionsProp: dict[str, Option] = {
	"metadata_dir": StrOption(
		comment="Path to a directory containing collates.txt,"
		" morphems.txt, keyboard.txt, and an optional"
		" metadata.json",
	),
	"collates_path": StrOption(
		comment="Path to collates.txt (overrides metadata_dir)",
	),
	"keyboard_path": StrOption(
		comment="Path to keyboard.txt (overrides metadata_dir)",
	),
	"morphems_path": StrOption(
		comment="Path to morphems.txt (overrides metadata_dir)",
	),
	"metadata_json_path": StrOption(
		comment="Path to metadata.json (overrides metadata_dir)",
	),
	"merge_separator": StrOption(
		comment="Separator for merging duplicate headwords",
	),
}
