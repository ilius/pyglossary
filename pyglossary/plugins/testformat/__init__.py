"""
PyGlossary test format plugin.

Internal regression format (``.test`` / ``.tst``) for PyGlossary development.
Registers ``Reader`` and ``Writer`` to exercise the plugin pipeline with minimal
fixtures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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

enable = False
lname = "testformat"
name = "Test"
description = "Test Format File(.test)"
extensions = (".test", ".tst")
extensionCreate = ".test"
singleFile = True
kind = "text"
wiki = ""
website = None

# key is option/argument name, value is instance of Option
optionsProp: dict[str, Option] = {}
