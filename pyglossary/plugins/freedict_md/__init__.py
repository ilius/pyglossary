"""
PyGlossary FreeDict Markdown format plugin.

FreeDict TEI sources rendered to Markdown-oriented output (``.tei`` input).
Read-only plugin that mirrors the FreeDict reader pipeline while emitting
Markdown-friendly definitions instead of HTML.
"""

from pyglossary.plugins.freedict.options import optionsProp

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
lname = "freedict_md"
name = "FreeDictMarkdown"
description = "FreeDict Markdown (.tei) (text output)"
extensions = ()
extensionCreate = ".tei"
singleFile = True
kind = "text"
wiki = "https://github.com/freedict/fd-dictionaries/wiki"
website = (
	"https://freedict.org/",
	"FreeDict.org",
)
relatedFormats: list[str] = ["FreeDict"]
