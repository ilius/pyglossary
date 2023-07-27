import typing
from typing import Callable, Optional, Tuple


class TransformerType(typing.Protocol):
	start: int
	pos: int
	input: str
	output: str
	currentKey: str
	attrs: "dict[str, str | None]"
	attrName: str
	audio: bool
	resFileSet: "set[str]"
	exampleColor: str

	def __init__(self: "typing.Self") -> None:
		pass

	def end(self: "typing.Self") -> bool:
		pass

	def move(self: "typing.Self", chars: int) -> None:
		pass

	def next(self: "typing.Self") -> str:
		pass

	def follows(self: "typing.Self", st: str) -> bool:
		pass

	def skipAny(self: "typing.Self", chars: str):
		pass

	def addText(self: "typing.Self", st: str) -> None:
		pass

	def resetBuf(self: "typing.Self") -> str:
		pass


class TitleTransformerType(TransformerType, typing.Protocol):
	title: str
	outputAlt: str

	def addText2(self: "typing.Self", st: str) -> None:
		pass


ErrorType = Optional[str]

# it is an State Function (state as in state machine)
LexType = Optional[Callable[[TransformerType], Tuple["LexType", ErrorType]]]

TitleLexType = Optional[
	Callable[[TitleTransformerType], Tuple["TitleLexType", ErrorType]]
]

