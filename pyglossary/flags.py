from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import TypeAlias


flagsByName = {}


class StrWithDesc(str):
	desc: str

	def __new__(cls: "type", name: str, desc: str) -> "StrWithDesc":
		s: StrWithDesc = str.__new__(cls, name)
		s.desc = desc
		flagsByName[name] = s
		return s


ALWAYS = StrWithDesc("always", "Always")
DEFAULT_YES = StrWithDesc("default_yes", "Yes (by default)")
DEFAULT_NO = StrWithDesc("default_no", "No (by default)")
NEVER = StrWithDesc("never", "Never")

# to satisfy mypy:
YesNoAlwaysNever: "TypeAlias" = StrWithDesc
