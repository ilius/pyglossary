import re
import typing
from collections import namedtuple
from typing import Optional, Tuple
from xml.sax.saxutils import escape

from ._types import ErrorType
from .lex import lexRoot

re_comment_block = re.compile(r"\{\{([^}]*)\}\}")
re_ref_short = re.compile(r"<<([^<>]*)>>")



Result = namedtuple(
	"Result", [
		"output",  # str,
		"resFileSet",  # "set[str]",
	],
)


# called Lexer by Rob Pike in "Lexical Scanning" video)
class Transformer:
	def __init__(
		self: "typing.Self",
		input: str,
		current_key: str = "",
		example_color: str = "steelblue",
		audio: bool = True,
	):
		self.input = input
		self.pos = 0
		self.buff = ""  # can replace by adding a self.start: int
		self.output = ""
		self.resFileSet: "set[str]" = set()

		self.current_key = current_key
		self.example_color = example_color
		self.audio = audio

	def end(self: "typing.Self") -> bool:
		return self.pos >= len(self.input)

	def move(self: "typing.Self", chars: int) -> None:
		self.pos += chars
		# self.absPos += chars

	def next(self: "typing.Self") -> str:
		c = self.input[self.pos]
		self.pos += 1
		# self.absPos += 1
		return c  # noqa: RET504

	def followsString(self: "typing.Self", st: str, skip: str = "") -> bool:
		pos = self.pos
		for c in st:
			if pos >= len(self.input):
				return False
			if self.input[pos] not in c:
				return False
			pos += 1
		return True

	def skipChars(self: "typing.Self", chars: str) -> None:
		pos = self.pos
		while True:
			if pos >= len(self.input):
				break
			if self.input[pos] not in chars:
				break
			pos += 1
		self.pos = pos

	def addText(self: "typing.Self", st: str) -> None:
		self.output += escape(st)

	def transform(self: "typing.Self") -> Tuple[Optional[Result], ErrorType]:
		self.input = re_comment_block.sub("", self.input)
		self.input = re_ref_short.sub(r"[ref]\1[/ref]", self.input)

		lex = lexRoot
		while lex is not None:
			lex, err = lex(self)
			if err:
				return None, err
		return Result(self.output, self.resFileSet), None
