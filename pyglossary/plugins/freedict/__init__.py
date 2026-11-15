"""
PyGlossary FreeDict format plugin.

TEI XML dictionaries from the FreeDict project (``.tei``). Read-only
``Reader`` parses TEI entries, resolves XIncludes, and builds definitions with
detected source/target languages. The ``defiFormat`` read option selects HTML
(default) or Markdown definitions.
"""

from .options import optionsProp
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
lname = "freedict"
name = "FreeDict"
description = "FreeDict (.tei)"
extensions = (".tei",)
extensionCreate = ".tei"
singleFile = True
kind = "text"
wiki = "https://github.com/freedict/fd-dictionaries/wiki"
website = (
	"https://freedict.org/",
	"FreeDict.org",
)
