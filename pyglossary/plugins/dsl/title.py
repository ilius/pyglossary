from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, cast
from xml.sax.saxutils import escape

from pyglossary.core import log

from .transform import Transformer

if TYPE_CHECKING:
	from ._types import ErrorType
	from ._types import TitleLexType as LexType
	from ._types import TitleTransformerType as TransformerType


__all__ = ["TitleTransformer"]


def lexRoot(tr: TransformerType) -> tuple[LexType, ErrorType]:
	# if tr.start < tr.pos:
	# 	log.warning(f"incomplete buffer near pos {tr.pos}")

	if tr.end():
		return None, None

	c = tr.next()
	if tr.end():
		tr.addText2(c)
		return None, None

	if c == "\\":
		return lexBackslash, None

	if c == "(":
		# tr.resetBuf()
		return lexParan, None

	if c == "{":
		return lexCurly, None

	tr.addText2(c)
	# tr.resetBuf()
	return lexRoot, None


def lexBackslash(tr: TransformerType) -> tuple[LexType, ErrorType]:
	c = tr.next()
	tr.addText2(c)
	# tr.resetBuf()
	return lexRoot, None


def lexParan(tr: TransformerType) -> tuple[LexType, ErrorType]:
	while True:
		if tr.end():
			log.warning(f"unclosed '(' near pos {tr.pos}")
			return None, None

		c = tr.next()
		if c == "\\":
			if tr.end():
				log.warning("unclosed '(' near pos {tr.pos}")
				return None, None
			tr.addText("\\" + tr.next())
			continue

		if c == ")":
			break
		tr.addText(c)

	return lexRoot, None


def lexCurly(tr: TransformerType) -> tuple[LexType, ErrorType]:
	start = tr.pos
	while True:
		if tr.end():
			log.warning("unclosed '{{' near pos {tr.pos}")
			return None, None

		c = tr.next()

		if c == "\\":
			if tr.end():
				log.warning("unclosed '{{' near pos {tr.pos}")
				return None, None
			tr.next()
			continue

		if c == "}":
			break

	tr2 = Transformer(tr.input[start : tr.pos - 1])
	res, err = tr2.transform()
	if err or res is None:
		return None, err
	tr.title += res.output

	return lexRoot, None


class TitleResult(NamedTuple):
	output: str
	outputAlt: str


class TitleTransformer:
	def __init__(
		self,
		inputTitle: str,
	) -> None:
		self.input = inputTitle
		# self.start = 0
		self.pos = 0
		self.output = ""
		self.outputAlt = ""
		self.title = ""

	def end(self) -> bool:
		return self.pos >= len(self.input)

	def move(self, chars: int) -> None:
		self.pos += chars

	def next(self) -> str:
		c = self.input[self.pos]
		self.pos += 1
		return c  # noqa: RET504

	# def resetBuf(self) -> str:
	# 	self.start = self.pos

	def addText(self, st: str) -> None:
		self.output += escape(st)
		self.title += escape(st)

	def addText2(self, st: str) -> None:
		esc = escape(st)
		self.output += esc
		self.outputAlt += esc
		self.title += esc

	def transform(self) -> tuple[TitleResult | None, ErrorType]:
		lex: LexType = lexRoot
		tr = cast("TransformerType", self)
		while lex is not None:
			lex, err = lex(tr)
			if err:
				return None, err
		return TitleResult(
			output=self.output,
			outputAlt=self.outputAlt,
		), None
