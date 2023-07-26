import typing
from typing import Callable, Optional, Tuple


class TransformerType(typing.Protocol):
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

	@property
	def output(self: "typing.Self") -> str:
		pass

	@output.setter
	def output(self: "typing.Self", st: str) -> str:
		pass


class TitleTransformerType(TransformerType, typing.Protocol):
	@property
	def outputAlt(self: "typing.Self") -> str:
		pass

	@outputAlt.setter
	def outputAlt(self: "typing.Self", st: str) -> str:
		pass

	def addText2(self: "typing.Self", st: str) -> None:
		pass


ErrorType = Optional[str]

# it is an State Function (state as in state machine)
LexType = Optional[Callable[[TransformerType], Tuple["LexType", ErrorType]]]

TitleLexType = Optional[
	Callable[[TitleTransformerType], Tuple["TitleLexType", ErrorType]]
]

