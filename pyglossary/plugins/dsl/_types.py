import typing
from typing import Optional

from pyglossary.interfaces import Interface


class TransformerType(metaclass=Interface):
	def __init__(self: "typing.Self") -> None:
		pass

	def end(self: "typing.Self") -> bool:
		pass

	def move(self: "typing.Self", chars: int) -> None:
		pass

	def next(self: "typing.Self") -> str:
		pass

	def followsString(self: "typing.Self", st: str, skip: str = "") -> bool:
		pass

	def skipChars(self: "typing.Self", chars: str):
		pass

	def addText(self: "typing.Self", st: str) -> None:
		pass

	@property
	def output(self: "typing.Self") -> str:
		pass

	@output.setter
	def output(self: "typing.Self", st: str) -> str:
		pass


ErrorType = Optional[str]

# it is an State Function (state as in state machine)
LexType = "Optional[Callable[[StateType], Tuple[LexType, ErrorType]]]"
