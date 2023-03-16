import typing
from typing import AnyStr, Callable

from .interfaces import Interface


class T_Locale(metaclass=Interface):
	def __init__(self: "typing.Self", _id: str) -> None:
		pass

	def getName(self: "typing.Self") -> str:
		pass


class T_Collator(metaclass=Interface):
	PRIMARY = 0
	SECONDARY = 1
	TERTIARY = 2
	QUATERNARY = 3
	IDENTICAL = 15

	@classmethod
	def createInstance(loc: "T_Locale | None" = None) -> "T_Collator":
		pass

	@property
	def getSortKey(self: "typing.Self") -> Callable[[AnyStr], bytes]:
		pass

	def setStrength(self: "typing.Self", strength: int) -> None:
		pass

	def setAttribute(self: "typing.Self", attr: int, value: int) -> None:
		pass


class T_UCollAttribute(metaclass=Interface):
	ALTERNATE_HANDLING = 1
	CASE_FIRST = 2
	CASE_LEVEL = 3
	DECOMPOSITION_MODE = 4
	FRENCH_COLLATION = 0
	HIRAGANA_QUATERNARY_MODE = 6
	NORMALIZATION_MODE = 4
	NUMERIC_COLLATION = 7
	STRENGTH = 5


class T_UCollAttributeValue(metaclass=Interface):
	DEFAULT = -1
	DEFAULT_STRENGTH = 2
	IDENTICAL = 15
	LOWER_FIRST = 24
	NON_IGNORABLE = 21
	OFF = 16
	ON = 17
	PRIMARY = 0
	QUATERNARY = 3
	SECONDARY = 1
	SHIFTED = 20
	TERTIARY = 2
	UPPER_FIRST = 25

