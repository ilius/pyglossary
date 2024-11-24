from __future__ import annotations

import typing
from collections.abc import Callable
from typing import AnyStr

__all__ = ["T_Collator", "T_Locale"]


class T_Locale(typing.Protocol):
	def __init__(self, _id: str) -> None: ...

	def getName(self) -> str: ...


class T_Collator(typing.Protocol):
	PRIMARY: int = 0
	SECONDARY: int = 1
	TERTIARY: int = 2
	QUATERNARY: int = 3
	IDENTICAL: int = 15

	# mypy: error: Self argument missing for a non-static method
	# (or an invalid type for self)  [misc]
	@classmethod  # pyright: ignore[reportArgumentType]
	def createInstance(cls: T_Locale) -> T_Collator: ...  # type: ignore

	@property
	def getSortKey(self) -> Callable[[AnyStr], bytes]: ...

	def setStrength(self, strength: int) -> None: ...

	def setAttribute(self, attr: int, value: int) -> None: ...


class T_UCollAttribute(typing.Protocol):
	ALTERNATE_HANDLING: int = 1
	CASE_FIRST: int = 2
	CASE_LEVEL: int = 3
	DECOMPOSITION_MODE: int = 4
	FRENCH_COLLATION: int = 0
	HIRAGANA_QUATERNARY_MODE: int = 6
	NORMALIZATION_MODE: int = 4
	NUMERIC_COLLATION: int = 7
	STRENGTH: int = 5


class T_UCollAttributeValue(typing.Protocol):
	DEFAULT: int = -1
	DEFAULT_STRENGTH: int = 2
	IDENTICAL: int = 15
	LOWER_FIRST: int = 24
	NON_IGNORABLE: int = 21
	OFF: int = 16
	ON: int = 17
	PRIMARY: int = 0
	QUATERNARY: int = 3
	SECONDARY: int = 1
	SHIFTED: int = 20
	TERTIARY: int = 2
	UPPER_FIRST: int = 25
