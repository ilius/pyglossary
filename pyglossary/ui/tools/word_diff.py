from __future__ import annotations

import difflib
import re
import sys
from typing import TYPE_CHECKING

from pyglossary.ui.tools.colors import green, red, reset

if TYPE_CHECKING:
	from collections.abc import Iterator

__all__ = ["formatDiff", "xmlDiff"]

wordRE = re.compile(r"(\W)", re.MULTILINE)
xmlTagRE = re.compile(
	"</?[a-z][0-9a-z]* *[^<>]*>",
	re.IGNORECASE | re.MULTILINE,
)


def plainWordSplit(text: str) -> list[str]:
	return [word for word in wordRE.split(text) if word]


def xmlWordSplit(text: str) -> list[str]:
	pos = 0
	words = []

	for m in xmlTagRE.finditer(text):
		start, end = m.span()
		match = m.group()
		if start > pos:
			words += plainWordSplit(text[pos:start])
		words.append(match)
		pos = end

	if pos < len(text):
		words += plainWordSplit(text[pos:])

	return words


def xmlDiff(text1: str, text2: str) -> Iterator[str]:
	words1 = xmlWordSplit(text1)
	words2 = xmlWordSplit(text2)
	return difflib.ndiff(words1, words2, linejunk=None, charjunk=None)


def formatDiff(diff: Iterator[str]) -> str:
	res = ""
	for part in diff:
		if part[0] == " ":
			res += part[2:]
			continue
		if part[0] == "-":
			res += red + part[2:] + reset
			continue
		if part[0] == "+":
			res += green + part[2:] + reset
			continue
	return res


def main_word_split() -> None:
	text = sys.argv[1]
	print(text)
	for word in xmlWordSplit(text):
		print(f"word: {word!r}")


def main() -> None:
	filename1 = sys.argv[1]
	filename2 = sys.argv[2]
	with open(filename1, encoding="utf-8") as _file:
		text1 = _file.read()
	with open(filename2, encoding="utf-8") as _file:
		text2 = _file.read()
	print(formatDiff(xmlDiff(text1, text2)))


if __name__ == "__main__":
	main()
