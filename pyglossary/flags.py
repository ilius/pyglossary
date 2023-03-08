flagsByName = {}

from typing import Literal, Type, TypeAlias, Union


class StrWithDesc(str):
	def __new__(cls: "Type", name: str, desc: str) -> "StrWithDesc":
		s = str.__new__(cls, name)
		s.desc = desc
		flagsByName[name] = s
		return s


ALWAYS = StrWithDesc("always", "Always")
DEFAULT_YES = StrWithDesc("default_yes", "Yes (by default)")
DEFAULT_NO = StrWithDesc("default_no", "No (by default)")
NEVER = StrWithDesc("never", "Never")

# typing.Literal is added in Python 3.8
YesNoAlwaysNever: TypeAlias = Union[
	"Literal[ALWAYS]",
	"Literal[DEFAULT_YES]",
	"Literal[DEFAULT_NO]",
	"Literal[NEVER]",
]
