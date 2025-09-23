from __future__ import annotations

import logging
import re
import typing
from operator import itemgetter
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Iterable, Iterator

	from .glossary_types import EntryType

__all__ = ["reverseGlossary"]

log = logging.getLogger("pyglossary")

if TYPE_CHECKING:

	class _GlossaryType(typing.Protocol):
		def __iter__(self) -> Iterator[EntryType]: ...

		def getInfo(self, key: str) -> str: ...

		def progressInit(self, *args: Any) -> None: ...

		def progress(self, pos: int, total: int, unit: str = "entries") -> None: ...

		def progressEnd(self) -> None: ...

		@property
		def progressbar(self) -> bool: ...

		@progressbar.setter
		def progressbar(self, enabled: bool) -> None: ...


def reverseGlossary(  # noqa: PLR0913
	glos: _GlossaryType,
	savePath: str = "",
	terms: list[str] | None = None,
	includeDefs: bool = False,
	saveStep: int = 1000,  # set this to zero to disable auto saving
	**kwargs: Any,
) -> Iterator[int]:
	"""
	Usage:
		for wordIndex in reverseGlossary(glos, ...):
			pass.

	Inside the `for` loop, you can pause by waiting (for input or a flag)
		or stop by breaking

	Potential keyword arguments:
		matchWord = True
		sepChars = ".,،"
		maxNum = 100
		minRel = 0.0
		minWordLen = 3
		includeDefs = False
		showRel = "None"
			allowed values: None, "Percent", "Percent At First"
	"""
	if not savePath:
		savePath = glos.getInfo("name") + ".txt"

	if saveStep < 2:
		raise ValueError("saveStep must be more than 1")

	entries: list[EntryType] = list(glos)
	log.info(f"loaded {len(entries)} entries into memory")

	terms = list(terms) if terms else takeOutputWords(glos, entries)

	entryCount = len(terms)
	log.info(
		f"Reversing to file {savePath!r}, number of entries: {entryCount}",
	)
	glos.progressInit("Reversing")
	wcThreshold = entryCount // 200 + 1

	with open(savePath, "w", encoding="utf-8") as saveFile:
		for entryIndex in range(entryCount):
			term = terms[entryIndex]
			if entryIndex % wcThreshold == 0:
				glos.progress(entryIndex, entryCount)

			if entryIndex % saveStep == 0 and entryIndex > 0:
				saveFile.flush()
			result = searchWordInDef(
				entries,
				term,
				includeDefs=includeDefs,
				**kwargs,
			)
			if result:
				try:
					if includeDefs:
						defi = "\\n\\n".join(result)
					else:
						defi = ", ".join(result) + "."
				except Exception:
					log.exception("")
					log.debug(f"{result = }")
					return
				saveFile.write(f"{term}\t{defi}\n")
			yield entryIndex

	glos.progressEnd()
	yield entryCount


def takeOutputWords(
	glos: _GlossaryType,
	entryIter: Iterable[EntryType],
	minWordLen: int = 3,
) -> list[str]:
	# f"[\\w]{{{minWordLen},}}" == fr"[\w]{{{minWordLen},}}"
	#   == r"[\w]{%d,}" % minWordLen
	termPattern = re.compile(rf"[\w]{{{minWordLen},}}", re.UNICODE)
	terms = set()
	progressbar, glos.progressbar = glos.progressbar, False
	for entry in entryIter:
		terms.update(
			termPattern.findall(
				entry.defi,
			)
		)
	glos.progressbar = progressbar
	return sorted(terms)


# C901 too complex (22 > 13)
# PLR0912 Too many branches (27 > 12)
# PLR0913 Too many arguments in function definition (9 > 5)
def searchWordInDef(  # noqa: C901, PLR0912, PLR0913
	entryIter: Iterable[EntryType],
	st: str,
	matchWord: bool = True,
	sepChars: str = ".,،",
	maxNum: int = 100,
	minRel: float = 0.0,
	minWordLen: int = 3,
	includeDefs: bool = False,
	showRel: str = "Percent",  # "Percent" | "Percent At First" | ""
) -> list[str]:
	# searches word "st" in definitions of the glossary
	splitPattern = re.compile(
		"|".join(re.escape(x) for x in sepChars),
		re.UNICODE,
	)
	wordPattern = re.compile(rf"[\w]{{{minWordLen},}}", re.UNICODE)
	outRel: list[tuple[str, float] | tuple[str, float, str]] = []
	for entry in entryIter:
		terms = entry.l_term
		defi = entry.defi
		if st not in defi:
			continue
		for word in terms:
			rel = 0.0  # relation value of word (0 <= rel <= 1)
			for part in splitPattern.split(defi):
				if not part:
					continue
				if matchWord:
					partWords = wordPattern.findall(
						part,
					)
					if not partWords:
						continue
					rel = max(
						rel,
						partWords.count(st) / len(partWords),
					)
				else:
					rel = max(
						rel,
						part.count(st) * len(st) / len(part),
					)
			if rel <= minRel:
				continue
			if includeDefs:
				outRel.append((word, rel, defi))
			else:
				outRel.append((word, rel))
	outRel.sort(
		key=itemgetter(1),
		reverse=True,
	)
	n = len(outRel)
	if n > maxNum > 0:
		outRel = outRel[:maxNum]
		n = maxNum
	num = 0
	out = []
	if includeDefs:
		for j in range(n):
			numP = num
			w, num, m = outRel[j]  # type: ignore
			m = m.replace("\n", "\\n").replace("\t", "\\t")
			onePer = int(1.0 / num)
			if onePer == 1.0:
				out.append(f"{w}\\n{m}")
			elif showRel == "Percent":
				out.append(f"{w}(%{100 * num})\\n{m}")
			elif showRel == "Percent At First":
				if num == numP:
					out.append(f"{w}\\n{m}")
				else:
					out.append(f"{w}(%{100 * num})\\n{m}")
			else:
				out.append(f"{w}\\n{m}")
		return out
	for j in range(n):
		numP = num
		w, num = outRel[j]  # type: ignore
		onePer = int(1.0 / num)
		if onePer == 1.0:
			out.append(w)
		elif showRel == "Percent":
			out.append(f"{w}(%{100 * num})")
		elif showRel == "Percent At First":
			if num == numP:
				out.append(w)
			else:
				out.append(f"{w}(%{100 * num})")
		else:
			out.append(w)
	return out
