from __future__ import annotations

import re
from typing import TYPE_CHECKING, NamedTuple, cast
from xml.sax.saxutils import escape

from pyglossary.core import log

from .lex import lexRoot

if TYPE_CHECKING:
	from ._types import ErrorType, LexType, TransformerType


__all__ = ["Transformer"]

re_comment_block = re.compile(r"\{\{([^}]*)\}\}")


class Result(NamedTuple):
	output: str
	resFileSet: set[str]


# called Lexer by Rob Pike in "Lexical Scanning" video)
class Transformer:
	def __init__(  # noqa: PLR0913
		self,
		inputText: str,
		currentKey: str = "",
		exampleColor: str = "steelblue",
		audio: bool = True,
		abbrev: str = "",  # "" or "css"
		abbrevDict: dict[str, str] | None = None,
	) -> None:
		self.input = inputText
		self.start = 0
		self.pos = 0
		self.labelOpen = False
		self.label = ""
		self.output = ""
		self.resFileSet: set[str] = set()

		self.abbrev = abbrev
		self.abbrevDict = abbrevDict

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

	def addHtml(self, st: str) -> None:
		if self.labelOpen:
			self.label += st
			return
		self.output += st

	def addText(self, st: str) -> None:
		st = escape(st)
		if self.labelOpen:
			self.label += st
			return
		self.output += st

	def closeLabel(self) -> None:
		# print(f"Label: {self.label!r}")
		desc = None
		if self.abbrev:
			desc = self.abbrevDict.get(self.label)
		if desc:
			self.output += (
				'<i class="p"><font color="green" '
				f'title="{escape(desc)}">{self.label}</font></i>'
			)
		else:
			self.output += (
				'<i class="p"><font color="green">' + self.label + "</font></i>"
			)
		self.label = ""
		self.labelOpen = False

	def closeTag(self, tag: str) -> None:
		assert tag
		if tag == "m":
			self.addHtml("</p>")
		elif tag == "b":
			self.addHtml("</b>")
		elif tag in {"u", "'"}:
			self.addHtml("</u>")
		elif tag == "i":
			self.addHtml("</i>")
		elif tag == "sup":
			self.addHtml("</sup>")
		elif tag == "sub":
			self.addHtml("</sub>")
		elif tag in {"c", "t"}:
			self.addHtml("</font>")
		elif tag == "p":
			self.closeLabel()
		elif tag == "*":
			self.addHtml("</span>")
		elif tag == "ex":
			self.addHtml("</font></span>")
		elif tag in {
			"ref",
			"url",
			"s",
			"trn",
			"!trn",
			"trs",
			"!trs",
			"lang",
			"com",
		}:
			pass
		else:
			log.warning(f"unknown close tag {tag!r}")
		self.resetBuf()

	def transform(self) -> tuple[Result | None, ErrorType]:
		# TODO: implement these 2 with lex functions
		self.input = re_comment_block.sub("", self.input)

		lex: LexType = lexRoot
		tr = cast("TransformerType", self)
		while lex is not None:
			lex, err = lex(tr)
			if err:
				return None, err
		if self.labelOpen:
			self.closeLabel()
		return Result(self.output, self.resFileSet), None
