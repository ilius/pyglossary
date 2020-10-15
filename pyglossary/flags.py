ALWAYS = 'always'
DEFAULT_YES = 'default_yes'
DEFAULT_NO = 'default_no'
NEVER = 'never'

# typing.Literal is added in Python 3.8
YesNoAlwaysNever = """Union[
	"Literal[ALWAYS]",
	"Literal[DEFAULT_YES]",
	"Literal[DEFAULT_NO]",
	"Literal[NEVER]",
]"""
