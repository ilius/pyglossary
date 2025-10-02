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
	@classmethod
	def createInstance(cls: T_Locale) -> T_Collator: ...  # type: ignore

	@property
	def getSortKey(self) -> Callable[[AnyStr], bytes]: ...

	def setStrength(self, strength: int) -> None: ...

	def setAttribute(self, attr: int, value: int) -> None: ...
