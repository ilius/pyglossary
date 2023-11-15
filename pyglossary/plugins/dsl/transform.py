import re
from collections import namedtuple
from typing import Optional, cast
from xml.sax.saxutils import escape

from ._types import ErrorType, LexType, TransformerType
from .lex import lexRoot

re_comment_block = re.compile(r"\{\{([^}]*)\}\}")


Result = namedtuple(
	"Result", [
		"output",  # str,
		"resFileSet",  # "set[str]",
	],
)


# called Lexer by Rob Pike in "Lexical Scanning" video)
class Transformer:
	def __init__(
		self,
		input: str,
		currentKey: str = "",
		exampleColor: str = "steelblue",
		audio: bool = True,
	) -> None:
		self.input = input
		self.start = 0
		self.pos = 0
		self.output = ""
		self.resFileSet: "set[str]" = set()

		self.attrs: dict[str, str] = {}
		self.attrName = ""

		self.currentKey = currentKey
		self.exampleColor = exampleColor
		self.audio = audio

	def end(self) -> bool:
		return self.pos >= len(self.input)

	def move(self, chars: int) -> None:
		self.pos += chars
		# self.absPos += chars

	def next(self) -> str:
		c = self.input[self.pos]
		self.pos += 1
		# self.absPos += 1
		return c  # noqa: RET504

	def resetBuf(self) -> None:
		self.start = self.pos
		self.attrName = ""
		self.attrs = {}

	def follows(self, st: str) -> bool:
		"""Check if current position follows the string `st`."""
		pos = self.pos
		for c in st:
			if pos >= len(self.input):
				return False
			if self.input[pos] not in c:
				return False
			pos += 1
		return True

	def skipAny(self, chars: str) -> None:
		"""Skip any of the characters that are in `chars`."""
		pos = self.pos
		while True:
			if pos >= len(self.input):
				break
			if self.input[pos] not in chars:
				break
			pos += 1
		self.pos = pos

	def addText(self, st: str) -> None:
		self.output += escape(st)

	def transform(self) -> tuple[Optional[Result], ErrorType]:
		# TODO: implement these 2 with lex functions
		self.input = re_comment_block.sub("", self.input)

		lex: LexType = lexRoot
		tr = cast(TransformerType, self)
		while lex is not None:
			lex, err = lex(tr)
			if err:
				return None, err
		return Result(self.output, self.resFileSet), None
