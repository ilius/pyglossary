"""
Typing protocols for PyICU collators and locales.

Defines ``T_Locale`` and ``T_Collator`` ``Protocol`` types so locale-aware sort
key modules can be type-checked whether or not ICU is installed at analysis
time.
"""

from __future__ import annotations

import typing
from collections.abc import Callable
from typing import AnyStr

__all__ = ["T_Collator", "T_Locale"]


class T_Locale(typing.Protocol):
	"""T Locale."""

	def __init__(self, _id: str) -> None: ...

	def getName(self) -> str: ...


class T_Collator(typing.Protocol):
	"""T Collator."""

	PRIMARY: int = 0
	SECONDARY: int = 1
	TERTIARY: int = 2
	QUATERNARY: int = 3
	IDENTICAL: int = 15

	# mypy: error: Self argument missing for a non-static method
	# (or an invalid type for self)  [misc]
	@classmethod
	def createInstance(cls: T_Locale) -> T_Collator: ...

	@property
	def getSortKey(self) -> Callable[[AnyStr], bytes]: ...

	def setStrength(self, strength: int) -> None: ...

	def setAttribute(self, attr: int, value: int) -> None: ...
