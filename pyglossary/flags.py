"""
This module is used in plugins.

Yes/no/always/never flag values for plugin options.

``StrWithDesc`` pairs each flag name with a human-readable description and
registers it in ``flagsByName``. Predefined values include ``ALWAYS``,
``DEFAULT_YES``, ``DEFAULT_NO``, ``NEVER``, and ``INTERNAL``.
"""

from __future__ import annotations

from typing import Self, cast

__all__ = [
	"ALWAYS",
	"DEFAULT_NO",
	"DEFAULT_YES",
	"INTERNAL",
	"NEVER",
	"StrWithDesc",
	"YesNoAlwaysNever",
	"flagsByName",
]

flagsByName: dict[str, StrWithDesc] = {}


class StrWithDesc(str):
	"""String with `desc` attribute (description)."""

	desc: str
	__slots__ = ["desc"]

	def __new__(cls: type[Self], name: str, desc: str) -> Self:
		s: StrWithDesc = str.__new__(cls, name)
		s.desc = desc
		flagsByName[name] = s
		return cast("Self", s)


ALWAYS = StrWithDesc("always", "Always")
DEFAULT_YES = StrWithDesc("default_yes", "Yes (by default)")
DEFAULT_NO = StrWithDesc("default_no", "No (by default)")
NEVER = StrWithDesc("never", "Never")
INTERNAL = StrWithDesc(
	"internal",
	"Internal (format-defined order, --sort is ignored)",
)

# to satisfy mypy:
type YesNoAlwaysNever = StrWithDesc
