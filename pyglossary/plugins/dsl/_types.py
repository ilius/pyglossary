"""
ABBYY Lingvo DSL typed error and token aliases.

Declares type aliases and error categories for the DSL lexer and transformer.
Keeps DSL plugin modules consistently typed without circular imports.
"""

from __future__ import annotations

import typing
from collections.abc import Callable
from typing import TYPE_CHECKING

__all__ = [
	"ErrorType",
	"LexType",
	"TitleLexType",
	"TitleTransformerType",
	"TransformerType",
]


class TransformerType(typing.Protocol):
	"""Transformer Type."""

	start: int
	pos: int
	input: str
	output: str
	currentKey: str
	attrs: dict[str, str | None]
	attrName: str
	audio: bool
	resFileSet: set[str]
	exampleColor: str

	def __init__(self) -> None:
		pass

	def end(self) -> bool: ...

	def move(self, chars: int) -> None: ...

	def next(self) -> str: ...

	def follows(self, st: str) -> bool: ...

	def skipAny(self, chars: str) -> None: ...

	def addText(self, st: str) -> None: ...

	def resetBuf(self) -> None: ...

	def addHtml(self, st: str) -> None: ...

	def closeTag(self, tag: str) -> None: ...

	@property
	def labelOpen(self) -> bool: ...

	@labelOpen.setter
	def labelOpen(self, value: bool) -> None: ...


class TitleTransformerType(TransformerType, typing.Protocol):
	"""Title Transformer Type."""

	title: str
	outputAlt: str

	def addText2(self, st: str) -> None: ...


if TYPE_CHECKING:
	ErrorType = str | None

	# it is an State Function (state as in state machine)
	LexType = Callable[[TransformerType], tuple["LexType", ErrorType]] | None

	TitleLexType = (
		Callable[
			[TitleTransformerType],
			tuple["TitleLexType", ErrorType],
		]
		| None
	)
