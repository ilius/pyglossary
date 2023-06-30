import typing
from collections import namedtuple
from typing import Optional, Tuple
from xml.sax.saxutils import escape

from pyglossary.core import log

from ._types import (
	ErrorType,
)
from ._types import TitleLexType as LexType
from ._types import TitleTransformerType as TransformerType


def lexRoot(tr: TransformerType) -> Tuple[LexType, ErrorType]:
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
		tr.addText(c)
		return lexParan, None

	if c == "{":
		return lexCurly, None

	tr.addText2(c)
	# tr.resetBuf()
	return lexRoot, None


def lexBackslash(tr: TransformerType) -> Tuple[LexType, ErrorType]:
	c = tr.next()
	tr.addText2(c)
	# tr.resetBuf()
	return lexRoot, None


def lexParan(tr: TransformerType) -> Tuple[LexType, ErrorType]:
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

		tr.addText(c)
		if c == ')':
			break

	return lexRoot, None 


def lexCurly(tr: TransformerType) -> Tuple[LexType, ErrorType]:
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

	return lexRoot, None 


TitleResult = namedtuple(
	"TitleResult", [
		"output",  # str,
		"outputAlt",  # str,
	],
)


class TitleTransformer:
	def __init__(
		self,
		input: str,
	):
		self.input = input
		# self.start = 0
		self.pos = 0
		self.output = ""
		self.outputAlt = ""
		# TODO: self.outputRich?

	def end(self: "typing.Self") -> bool:
		return self.pos >= len(self.input)

	def move(self: "typing.Self", chars: int) -> None:
		self.pos += chars

	def next(self: "typing.Self") -> str:
		c = self.input[self.pos]
		self.pos += 1
		return c  # noqa: RET504

	# def resetBuf(self: "typing.Self") -> str:
	# 	self.start = self.pos

	def addText(self: "typing.Self", st: str) -> None:
		self.output += escape(st)

	def addText2(self: "typing.Self", st: str) -> None:
		esc = escape(st)
		self.output += esc
		self.outputAlt += esc

	def transform(self: "typing.Self") -> Tuple[Optional[TitleResult], ErrorType]:
		lex = lexRoot
		while lex is not None:
			lex, err = lex(self)
			if err:
				return None, err
		return TitleResult(
			output=self.output,
			outputAlt=self.outputAlt,
		), None
