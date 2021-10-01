class StrWithDesc(str):
	def __new__(cls, name: str, desc: str):
		s = str.__new__(cls, name)
		s.desc = desc
		return s


ALWAYS = StrWithDesc("always", "Always")
DEFAULT_YES = StrWithDesc("default_yes", "Yes (by default)")
DEFAULT_NO = StrWithDesc("default_no", "No (by default)")
NEVER = StrWithDesc("never", "Never")

# typing.Literal is added in Python 3.8
YesNoAlwaysNever = """Union[
	"Literal[ALWAYS]",
	"Literal[DEFAULT_YES]",
	"Literal[DEFAULT_NO]",
	"Literal[NEVER]",
]"""
